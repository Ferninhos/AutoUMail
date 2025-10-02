from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class EmailRequest(BaseModel):
    """Request model for email classification"""
    content: str = Field(..., min_length=1, max_length=10000, description="Conteúdo do email")
    subject: Optional[str] = Field(None, max_length=500, description="Assunto do email")
    sender: Optional[str] = Field(None, max_length=100, description="Remetente do email")
    config_id: Optional[str] = Field(None, max_length=20, description="ID de configuração da empresa")

class Email(BaseModel):
    """Email model"""
    id: str
    content: str
    subject: Optional[str] = None
    sender: Optional[str] = None
    timestamp: datetime

class StructuredResponse(BaseModel):
    """Structured email response model"""
    to: str = Field(..., description="Destinatário do email")
    subject: str = Field(..., description="Assunto da resposta")
    body: str = Field(..., description="Corpo da resposta")

class EmailClassificationResponse(BaseModel):
    """Response model for email classification"""
    id: str
    email: Email
    category: Literal['productive', 'unproductive']
    reasoning: str = Field(..., description="Explicação da classificação")
    suggestedResponse: StructuredResponse = Field(..., description="Resposta sugerida estruturada")
    processedAt: datetime

class ClassificationResult(BaseModel):
    """Internal model for classification result"""
    category: Literal['productive', 'unproductive']
    reasoning: str = Field(..., description="Explicação da classificação")
    suggested_response: StructuredResponse