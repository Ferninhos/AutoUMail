import logging
import asyncio
from typing import Dict, Any, Optional
import re
from .gemini_service import GeminiService
from .nlp_preprocessor import NLPPreprocessor
from .text_features import TextFeatureExtractor
from models.email_models import ClassificationResult

logger = logging.getLogger(__name__)

class EmailClassifier:
    """
    Serviço de classificação de emails que determina se são produtivos ou improdutivos
    e gera respostas automáticas apropriadas.
    
    Agora com camada de NLP para pré-processamento e extração de features.
    """
    
    def __init__(self):
        self.ai_service = GeminiService()
        self.nlp_preprocessor = NLPPreprocessor()
        self.feature_extractor = TextFeatureExtractor()
        logger.info("[CLASSIFIER] Initialized with AI-first approach + NLP enrichment")
    
    async def classify_and_respond(
        self, 
        content: str, 
        subject: Optional[str] = None, 
        sender: Optional[str] = None,
        company_config: Optional[Dict[str, str]] = None
    ) -> ClassificationResult:
        """
        Classifica o email usando IA (método principal) com fallback enriquecido por NLP
        """
        try:
            logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            logger.info(f"[CLASSIFIER] Starting classification with NLP")
            logger.info(f"[CLASSIFIER] Content preview: {content[:150]}...")
            logger.info(f"[CLASSIFIER] Subject: '{subject}'")
            logger.info(f"[CLASSIFIER] Sender: '{sender}'")
            logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            # ===== NLP PRÉ-PROCESSAMENTO =====
            logger.info("[NLP STEP] Preprocessing text...")
            preprocessed = self.nlp_preprocessor.preprocess(content, remove_stopwords=False)
            features = self.feature_extractor.extract_all_features(content, subject)
            
            logger.info(f"[NLP STEP] ✅ Preprocessing complete:")
            logger.info(f"  - Keywords found: {preprocessed['metadata'].get('keywords', [])}")
            logger.info(f"  - Urgency detected: {preprocessed['metadata'].get('has_urgency', False)}")
            logger.info(f"  - Feature-based hint: {features.get('feature_based_category', 'uncertain')}")
            
            final_category = "unproductive"  # Conservative default
            final_reasoning = "Classificação padrão por segurança"
            classification_method = "default"
            confidence = "low"
            
            
            logger.info("[CLASSIFIER STEP 1] Attempting AI classification with NLP-cleaned text...")
            try:
              
                cleaned_content = preprocessed['cleaned_text']
                
                ai_result = await asyncio.wait_for(
                    self.ai_service.classify_email_with_context(cleaned_content, subject, company_config),
                    timeout=15.0
                )
                final_category = ai_result.get('category', 'unproductive')
                final_reasoning = ai_result.get('reasoning', 'Classificação por IA')
                confidence = ai_result.get('confidence', 'medium')
                classification_method = "AI+NLP"
                logger.info(f"[CLASSIFIER STEP 1] ✅ AI Success: category={final_category}, confidence={confidence}")
                logger.info(f"[CLASSIFIER STEP 1] Reasoning: {final_reasoning}")
            except asyncio.TimeoutError:
                logger.warning(f"[CLASSIFIER STEP 1] ⏱️ AI classification TIMEOUT after 15s")
                
                fallback_result = self._nlp_enhanced_fallback(content, subject, features)
                final_category = fallback_result['category']
                final_reasoning = fallback_result['reasoning']
                confidence = fallback_result['confidence']
                classification_method = "NLP_fallback"
                logger.info(f"[CLASSIFIER STEP 2] 🔄 NLP-enhanced fallback: {final_category} (confidence: {confidence})")
            except Exception as ai_error:
                logger.warning(f"[CLASSIFIER STEP 1] ⚠️ AI classification ERROR: {str(ai_error)}")
                
                fallback_result = self._nlp_enhanced_fallback(content, subject, features)
                final_category = fallback_result['category']
                final_reasoning = fallback_result['reasoning']
                confidence = fallback_result['confidence']
                classification_method = "NLP_fallback"
                logger.info(f"[CLASSIFIER STEP 2] 🔄 NLP-enhanced fallback: {final_category} (confidence: {confidence})")
            
            
            logger.info(f"[CLASSIFIER STEP 3] Generating response for category: {final_category}")
            structured_response = None
            try:
                structured_response = await asyncio.wait_for(
                    self._generate_response(content, final_category, subject, sender, company_config),
                    timeout=20.0
                )
                logger.info(f"[CLASSIFIER STEP 3] ✅ Response generated successfully")
            except Exception as response_error:
                logger.warning(f"[CLASSIFIER STEP 3] ⚠️ Response generation failed: {str(response_error)}")
                
                if final_category == "productive":
                    body = "Prezado(a),\n\nRecebemos sua mensagem e nossa equipe irá analisá-la. Retornaremos o contato em breve.\n\nAtenciosamente,\nEquipe de Suporte"
                else:
                    body = "Prezado(a),\n\nAgradecemos seu contato.\n\nAtenciosamente,\nEquipe"
                
                from models.email_models import StructuredResponse
                structured_response = StructuredResponse(
                    to=sender if sender else "cliente@email.com",
                    subject=f"Re: {subject}" if subject else "Re: Seu contato",
                    body=body
                )
            
            result = ClassificationResult(
                category=final_category,
                reasoning=final_reasoning,
                suggested_response=structured_response
            )
            
            logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            logger.info(f"[CLASSIFIER] ✅ COMPLETED SUCCESSFULLY")
            logger.info(f"[CLASSIFIER] Result: {result.category} (method: {classification_method}, confidence: {confidence})")
            logger.info(f"[CLASSIFIER] Reasoning: {final_reasoning}")
            logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            return result
            
        except Exception as e:
            logger.error(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            logger.error(f"[CLASSIFIER] ❌ CRITICAL ERROR")
            logger.error(f"[CLASSIFIER] Error message: {str(e)}")
            logger.error(f"[CLASSIFIER] Error type: {type(e).__name__}")
            logger.error(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            raise Exception(f"Email Classification Service failed: {str(e)}")
    
    def _nlp_enhanced_fallback(self, content: str, subject: Optional[str] = None, features: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Fallback ENRIQUECIDO com features NLP quando a IA falha
        Usa scores de features para melhor classificação
        """
        text = f"{subject or ''} {content}".lower().strip()
        
        logger.info(f"[NLP FALLBACK] Analyzing with extracted features...")
        
        if features is None:
            features = self.feature_extractor.extract_all_features(content, subject)
        
       
        technical_score = features.get('technical_score', 0.0)
        business_score = features.get('business_score', 0.0)
        support_score = features.get('support_score', 0.0)
        social_score = features.get('social_score', 0.0)
        urgency_score = features.get('urgency_score', 0.0)
        
        logger.info(f"[NLP FALLBACK] Scores: tech={technical_score:.2f}, biz={business_score:.2f}, "
                   f"support={support_score:.2f}, social={social_score:.2f}, urgency={urgency_score:.2f}")
        
       
        if urgency_score > 0.5 and (technical_score > 0.2 or business_score > 0.2):
            return {
                'category': 'productive',
                'reasoning': f'Email urgente detectado com contexto de negócios (urgência: {urgency_score:.1f})',
                'confidence': 'high'
            }
        
        # Score técnico alto = productive
        if technical_score > 0.4:
            return {
                'category': 'productive',
                'reasoning': f'Problema técnico identificado pelas features NLP (score: {technical_score:.2f})',
                'confidence': 'high'
            }
        
        # Score de negócio alto = productive
        if business_score > 0.4:
            return {
                'category': 'productive',
                'reasoning': f'Questão comercial identificada (score: {business_score:.2f})',
                'confidence': 'high'
            }
        
        # Score de suporte alto = productive
        if support_score > 0.4:
            return {
                'category': 'productive',
                'reasoning': f'Solicitação de suporte identificada (score: {support_score:.2f})',
                'confidence': 'medium'
            }
        
        # Score social alto + outros baixos = unproductive
        if social_score > 0.4 and technical_score < 0.1 and business_score < 0.1:
            return {
                'category': 'unproductive',
                'reasoning': f'Mensagem social/pessoal sem contexto de negócios (score social: {social_score:.2f})',
                'confidence': 'high'
            }
        
        # Múltiplas perguntas + baixo score social = productive (likely dúvidas)
        if features.get('has_multiple_questions', False) and social_score < 0.2:
            return {
                'category': 'productive',
                'reasoning': 'Múltiplas perguntas detectadas, indicando necessidade de suporte',
                'confidence': 'medium'
            }
        
        # Mensagem muito curta sem contexto claro
        if features.get('word_count', 0) < 10:
            return {
                'category': 'unproductive',
                'reasoning': f'Mensagem muito curta ({features.get("word_count", 0)} palavras) sem indicadores claros',
                'confidence': 'medium'
            }
        
        # Default conservador - se não há indicadores claros
        logger.info(f"[NLP FALLBACK] No clear indicators, defaulting to unproductive")
        return {
            'category': 'unproductive',
            'reasoning': 'Sem indicadores claros de necessidade de ação (análise NLP conservadora)',
            'confidence': 'low'
        }
    
    def _critical_fallback_classification(self, content: str, subject: Optional[str] = None) -> Dict[str, Any]:
        """
        Fallback LEGADO mantido para compatibilidade
        (agora usa o NLP-enhanced como padrão)
        """
        return self._nlp_enhanced_fallback(content, subject, None)
    
    
    async def _generate_response(self, content: str, category: str, subject: Optional[str] = None, sender: Optional[str] = None, company_config: Optional[Dict[str, str]] = None):
        """
        Gera resposta automática estruturada usando IA
        """
        try:
            from models.email_models import StructuredResponse
            
            # Gerar resposta estruturada usando IA
            response_dict = await self.ai_service.generate_response(content, category, subject, sender, company_config)
            
            # Create StructuredResponse object
            structured_response = StructuredResponse(
                to=response_dict["to"],
                subject=response_dict["subject"],
                body=response_dict["body"]
            )
            
            logger.info(f"AI structured response generated successfully for {category} email")
            return structured_response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            raise Exception("AI Response Generation falhou")
    