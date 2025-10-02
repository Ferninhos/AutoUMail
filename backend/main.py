from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import asyncio
from datetime import datetime
import uuid
import PyPDF2
import io

from models.email_models import EmailRequest, EmailClassificationResponse
from models.company_models import CompanyConfigRequest, CompanyConfigResponse
from services.classifier import EmailClassifier
from services.company_service import CompanyService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Email Classification API",
    description="API para classificação de emails e geração de respostas automáticas",
    version="1.0.0"
)

origins = [
    "https://autouemailapi.netlify.app",
    "http://localhost:3000",
    "http://localhost"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # lista de origens permitidas
    allow_credentials=False,      # se precisar de cookies ou headers de autenticação
    allow_methods=["*"],         # permite todos os métodos (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],         # permite todos os headers
)

# Initialize services
classifier = EmailClassifier()
company_service = CompanyService()

@app.get("/")
async def root():
    return {"message": "Email Classification API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/extract-pdf")
async def extract_pdf(file: UploadFile = File(...)):
    """
    Extrai texto de arquivo PDF
    """
    try:
        # Validação do tipo de arquivo
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos")
        
        # Validação do tamanho (10MB máximo)
        contents = await file.read()
        file_size = len(contents)
        max_size = 10 * 1024 * 1024  # 10MB
        
        if file_size > max_size:
            raise HTTPException(
                status_code=400, 
                detail=f"Arquivo muito grande. Tamanho máximo: 10MB. Tamanho atual: {file_size / (1024*1024):.1f}MB"
            )
        
        logger.info(f"Processing PDF: {file.filename} ({file_size / 1024:.1f}KB)")
        
        # Extrair texto do PDF
        pdf_file = io.BytesIO(contents)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Verificar se o PDF tem páginas
        if len(pdf_reader.pages) == 0:
            raise HTTPException(status_code=400, detail="PDF não contém páginas")
        
        # Extrair texto de todas as páginas
        text_parts = []
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                text = page.extract_text()
                if text.strip():
                    text_parts.append(text)
                logger.info(f"Extracted {len(text)} characters from page {page_num + 1}")
            except Exception as e:
                logger.warning(f"Error extracting page {page_num + 1}: {e}")
                continue
        
        if not text_parts:
            raise HTTPException(
                status_code=400, 
                detail="Não foi possível extrair texto do PDF. O arquivo pode estar vazio ou protegido."
            )
        
        extracted_text = "\n\n".join(text_parts)
        logger.info(f"Successfully extracted {len(extracted_text)} characters from {len(text_parts)} pages")
        
        return {
            "text": extracted_text,
            "pages": len(pdf_reader.pages),
            "filename": file.filename,
            "size_kb": round(file_size / 1024, 1)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar PDF: {str(e)}")

@app.post("/company-config", response_model=CompanyConfigResponse)
async def create_company_config(request: CompanyConfigRequest):
    """Create a new company configuration and return a unique config_id"""
    try:
        logger.info(f"Creating config for company: {request.company_name}")
        
        config = company_service.create_config(request)
        
        return CompanyConfigResponse(
            config_id=config.config_id,
            company_name=config.company_name,
            message="Configuração criada com sucesso! Guarde este código para usar no sistema."
        )
    except Exception as e:
        logger.error(f"Error creating company config: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar configuração: {str(e)}")

@app.get("/company-config/{config_id}")
async def get_company_config(config_id: str):
    """Get company configuration by ID"""
    config = company_service.get_config(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    return config

@app.post("/classify-email", response_model=EmailClassificationResponse)
async def classify_email(request: EmailRequest):
    try:
        logger.info("=== STARTING EMAIL CLASSIFICATION ===")
        logger.info(f"Subject: {request.subject}, Sender: {request.sender}")

        email_id = str(uuid.uuid4())
        classification_id = str(uuid.uuid4())

        # Get company config if provided
        company_config_data = None
        if request.config_id:
            company_config = company_service.get_config(request.config_id)
            if company_config:
                logger.info(f"Using company config: {company_config.company_name}")
                company_config_data = {
                    "company_name": company_config.company_name,
                    "custom_instructions": company_config.custom_instructions
                }
            else:
                logger.warning(f"Config ID {request.config_id} not found, using default")

        classification_result = await asyncio.wait_for(
            classifier.classify_and_respond(
                content=request.content,
                subject=request.subject,
                sender=request.sender,
                company_config=company_config_data
            ),
            timeout=30.0
        )

        response = EmailClassificationResponse(
            id=classification_id,
            email={
                "id": email_id,
                "content": request.content,
                "subject": request.subject,
                "sender": request.sender,
                "timestamp": datetime.now()
            },
            category=classification_result.category,
            reasoning=classification_result.reasoning,
            suggestedResponse=classification_result.suggested_response,
            processedAt=datetime.now()
        )

        return response

    except asyncio.TimeoutError:
        logger.error("Classification timed out")
        from models.email_models import StructuredResponse
        return EmailClassificationResponse(
            id=str(uuid.uuid4()),
            email={
                "id": str(uuid.uuid4()),
                "content": request.content,
                "subject": request.subject,
                "sender": request.sender,
                "timestamp": datetime.now()
            },
            category="productive",
            reasoning="Timeout no processamento - classificação padrão aplicada",
            suggestedResponse=StructuredResponse(
                to=request.sender if request.sender else "cliente@email.com",
                subject=f"Re: {request.subject}" if request.subject else "Resposta",
                body="Prezado(a),\n\nRecebemos sua mensagem e vamos analisá-la em breve.\n\nAtenciosamente,\nEquipe de Suporte"
            ),
            processedAt=datetime.now()
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        from models.email_models import StructuredResponse
        return EmailClassificationResponse(
            id=str(uuid.uuid4()),
            email={
                "id": str(uuid.uuid4()),
                "content": request.content,
                "subject": request.subject,
                "sender": request.sender,
                "timestamp": datetime.now()
            },
            category="productive",
            reasoning="Erro no processamento - classificação padrão aplicada",
            suggestedResponse=StructuredResponse(
                to=request.sender if request.sender else "cliente@email.com",
                subject=f"Re: {request.subject}" if request.subject else "Resposta",
                body="Prezado(a),\n\nRecebemos sua mensagem. Nossa equipe irá analisá-la e retornar em breve.\n\nAtenciosamente,\nEquipe de Suporte"
            ),
            processedAt=datetime.now()
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
