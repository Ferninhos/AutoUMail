import re
import logging
from typing import Dict, Any, Optional, List
from unidecode import unidecode

logger = logging.getLogger(__name__)

class NLPPreprocessor:
    """
    Pré-processador de texto com técnicas de NLP para melhorar classificação de emails
    """
    
    def __init__(self):
        # Stop words em português - apenas as menos relevantes
        # MANTÉM palavras importantes como "não", "problema", "ajuda"
        self.stop_words = {
            'o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas',
            'de', 'da', 'do', 'das', 'dos', 'em', 'no', 'na', 'nos', 'nas',
            'por', 'para', 'com', 'sem', 'sob', 'sobre',
            'e', 'ou', 'mas', 'porém', 'contudo',
            'que', 'qual', 'quais', 'quanto', 'quantos',
            'esse', 'essa', 'esses', 'essas', 'aquele', 'aquela',
            'isto', 'isso', 'aquilo',
            'se', 'como', 'quando', 'onde'
        }
        
        # Padrões de assinatura automática para remoção
        self.auto_signatures = [
            r'enviado do meu (iphone|ipad|android|samsung|xiaomi)',
            r'sent from my (iphone|ipad|android)',
            r'get outlook for (ios|android)',
            r'baixado do outlook para (ios|android)',
            r'este email e qualquer arquivo anexado.*confidencial',
            r'aviso legal:.*',
            r'disclaimer:.*',
            r'confidential.*'
        ]
        
        # Padrões de urgência
        self.urgency_patterns = [
            r'\burgente\b',
            r'\bprazo\b',
            r'\bimediato\b',
            r'\basap\b',
            r'\brapidamente\b',
            r'\bpremência\b',
            r'\bcrítico\b',
            r'\bemergência\b',
            r'o mais rápido possível',
            r'quanto antes'
        ]
        
    def preprocess(self, text: str, remove_stopwords: bool = False) -> Dict[str, Any]:
        """
        Pré-processa texto completo e retorna texto limpo + metadados
        
        Args:
            text: Texto original
            remove_stopwords: Se True, remove stop words (padrão: False para preservar contexto)
            
        Returns:
            Dict com texto limpo e metadados extraídos
        """
        try:
            logger.info(f"[NLP] Starting preprocessing for text length: {len(text)}")
            
            # 1. Normalização básica
            cleaned_text = self._normalize_text(text)
            
            # 2. Remover assinaturas automáticas
            cleaned_text = self._remove_auto_signatures(cleaned_text)
            
            # 3. Extrair estruturas importantes
            urls = self._extract_urls(text)
            emails = self._extract_emails(text)
            phones = self._extract_phones(text)
            
            # 4. Detectar idioma (básico)
            language = self._detect_language(cleaned_text)
            
            # 5. Remover stop words se solicitado (OPCIONAL)
            processed_text = cleaned_text
            if remove_stopwords:
                processed_text = self._remove_stopwords(cleaned_text)
            
            # 6. Extrair palavras-chave importantes
            keywords = self._extract_keywords(cleaned_text)
            
            result = {
                'original_text': text,
                'cleaned_text': cleaned_text,
                'processed_text': processed_text,
                'metadata': {
                    'urls': urls,
                    'emails': emails,
                    'phones': phones,
                    'language': language,
                    'keywords': keywords,
                    'text_length': len(cleaned_text),
                    'word_count': len(cleaned_text.split()),
                    'has_urgency': self._detect_urgency(cleaned_text)
                }
            }
            
            logger.info(f"[NLP] Preprocessing complete. Words: {result['metadata']['word_count']}, Keywords: {len(keywords)}")
            return result
            
        except Exception as e:
            logger.error(f"[NLP] Error in preprocessing: {str(e)}")
            # Retornar texto original em caso de erro
            return {
                'original_text': text,
                'cleaned_text': text,
                'processed_text': text,
                'metadata': {
                    'error': str(e)
                }
            }
    
    def _normalize_text(self, text: str) -> str:
        """Normaliza texto: remove espaços extras, normaliza quebras de linha"""
        # Remove espaços múltiplos
        text = re.sub(r'\s+', ' ', text)
        # Normaliza quebras de linha (max 2 consecutivas)
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Remove espaços no início e fim
        return text.strip()
    
    def _remove_auto_signatures(self, text: str) -> str:
        """Remove assinaturas automáticas conhecidas"""
        cleaned = text
        for pattern in self.auto_signatures:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
        return cleaned.strip()
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extrai URLs do texto"""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, text)
    
    def _extract_emails(self, text: str) -> List[str]:
        """Extrai endereços de email"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(email_pattern, text)
    
    def _extract_phones(self, text: str) -> List[str]:
        """Extrai números de telefone (formato brasileiro e internacional)"""
        phone_patterns = [
            r'\+?\d{2}[\s-]?\(?\d{2}\)?[\s-]?\d{4,5}[\s-]?\d{4}',  # BR: +55 (11) 99999-9999
            r'\(?\d{2}\)?[\s-]?\d{4,5}[\s-]?\d{4}'  # BR: (11) 99999-9999
        ]
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text))
        return phones
    
    def _detect_language(self, text: str) -> str:
        """Detecção básica de idioma (português vs inglês)"""
        portuguese_indicators = ['ção', 'ões', 'ão', 'ê', 'á', 'à', 'ó', 'ô']
        text_lower = text.lower()
        
        pt_count = sum(1 for indicator in portuguese_indicators if indicator in text_lower)
        
        return 'pt' if pt_count > 2 else 'en'
    
    def _remove_stopwords(self, text: str) -> str:
        """
        Remove stop words mantendo palavras importantes
        CUIDADO: Pode remover contexto importante!
        """
        words = text.lower().split()
        filtered_words = [word for word in words if word not in self.stop_words]
        return ' '.join(filtered_words)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extrai palavras-chave relevantes (substantivos, verbos importantes)
        """
        # Palavras-chave técnicas e de negócio
        business_keywords = [
            'problema', 'erro', 'bug', 'falha', 'defeito',
            'ajuda', 'suporte', 'dúvida', 'questão', 'pergunta',
            'produto', 'serviço', 'compra', 'pagamento', 'preço',
            'contrato', 'proposta', 'orçamento',
            'reclamação', 'insatisfação', 'insatisfeito',
            'urgente', 'imediato', 'prazo',
            'funcionar', 'acessar', 'instalar', 'configurar',
            'cancelar', 'devolver', 'reembolso'
        ]
        
        text_lower = text.lower()
        found_keywords = [kw for kw in business_keywords if kw in text_lower]
        
        return found_keywords
    
    def _detect_urgency(self, text: str) -> bool:
        """Detecta se o texto contém indicadores de urgência"""
        text_lower = text.lower()
        
        # Verificar padrões de urgência
        for pattern in self.urgency_patterns:
            if re.search(pattern, text_lower):
                return True
        
        # Verificar excesso de exclamações (indicador de urgência/emoção)
        exclamation_count = text.count('!')
        if exclamation_count >= 3:
            return True
        
        # Verificar CAPS LOCK excessivo
        if text.isupper() and len(text) > 20:
            return True
        
        return False
    
    def normalize_for_ai(self, text: str) -> str:
        """
        Normaliza texto especificamente para envio à IA
        Remove apenas ruído sem perder contexto
        """
        # Remove assinaturas automáticas
        text = self._remove_auto_signatures(text)
        
        # Normaliza espaços
        text = self._normalize_text(text)
        
        # Limita tamanho (para evitar token overflow)
        max_length = 3000
        if len(text) > max_length:
            text = text[:max_length] + "...[texto truncado]"
        
        return text
