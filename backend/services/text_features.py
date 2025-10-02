import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class TextFeatureExtractor:
    """
    Extrator de features numéricas e categóricas de texto para enriquecer classificação
    """
    
    def __init__(self):
        # Palavras que indicam problemas técnicos
        self.technical_keywords = [
            'erro', 'bug', 'falha', 'defeito', 'problema técnico',
            'não funciona', 'não consegui', 'travando', 'lento',
            'crash', 'parou', 'quebrado', 'corrompido'
        ]
        
        # Palavras que indicam solicitações comerciais
        self.business_keywords = [
            'preço', 'custo', 'valor', 'orçamento', 'proposta',
            'contrato', 'comprar', 'adquirir', 'contratar',
            'investimento', 'pagamento', 'fatura'
        ]
        
        # Palavras que indicam suporte/dúvidas
        self.support_keywords = [
            'ajuda', 'suporte', 'dúvida', 'como fazer', 'não sei',
            'orientação', 'assistência', 'informação', 'esclarecimento',
            'tutorial', 'instrução', 'passo a passo'
        ]
        
        # Palavras sociais/pessoais
        self.social_keywords = [
            'parabéns', 'felicitações', 'aniversário', 'festa',
            'convite', 'celebração', 'gratidão', 'obrigado por tudo',
            'abraço', 'beijo', 'feliz', 'alegria'
        ]
    
    def extract_all_features(self, text: str, subject: str = None) -> Dict[str, Any]:
        """
        Extrai todas as features do texto
        
        Returns:
            Dict com features numéricas e categóricas
        """
        try:
            full_text = f"{subject or ''} {text}".lower()
            
            features = {
                # Features estruturais
                'text_length': len(text),
                'word_count': len(text.split()),
                'sentence_count': self._count_sentences(text),
                'avg_word_length': self._avg_word_length(text),
                
                # Features de pontuação
                'question_count': text.count('?'),
                'exclamation_count': text.count('!'),
                'has_multiple_questions': text.count('?') >= 2,
                'has_excessive_exclamations': text.count('!') >= 3,
                
                # Features de formatação
                'has_urls': bool(re.search(r'http[s]?://', text)),
                'has_email_addresses': bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)),
                'has_phone_numbers': bool(re.search(r'\(?\d{2}\)?[\s-]?\d{4,5}[\s-]?\d{4}', text)),
                'caps_lock_ratio': self._calculate_caps_ratio(text),
                
                # Features de conteúdo
                'technical_score': self._calculate_keyword_score(full_text, self.technical_keywords),
                'business_score': self._calculate_keyword_score(full_text, self.business_keywords),
                'support_score': self._calculate_keyword_score(full_text, self.support_keywords),
                'social_score': self._calculate_keyword_score(full_text, self.social_keywords),
                
                # Features de urgência
                'urgency_score': self._calculate_urgency_score(full_text),
                'has_deadline_mention': self._has_deadline_mention(full_text),
                
                # Features de sentimento (básico)
                'negative_words_count': self._count_negative_words(full_text),
                'positive_words_count': self._count_positive_words(full_text),
                
                # Features de especificidade
                'has_specific_numbers': bool(re.search(r'\b\d+\b', text)),
                'has_specific_dates': bool(re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', text)),
                'has_bullet_points': bool(re.search(r'^\s*[-•*]\s', text, re.MULTILINE)),
                
                # Classificação simplificada baseada em features
                'feature_based_category': self._classify_by_features(full_text),
                'confidence_score': self._calculate_confidence(full_text)
            }
            
            logger.info(f"[FEATURES] Extracted features: technical={features['technical_score']:.2f}, "
                       f"business={features['business_score']:.2f}, support={features['support_score']:.2f}, "
                       f"social={features['social_score']:.2f}")
            
            return features
            
        except Exception as e:
            logger.error(f"[FEATURES] Error extracting features: {str(e)}")
            return {}
    
    def _count_sentences(self, text: str) -> int:
        """Conta aproximadamente o número de sentenças"""
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])
    
    def _avg_word_length(self, text: str) -> float:
        """Calcula comprimento médio das palavras"""
        words = text.split()
        if not words:
            return 0.0
        total_length = sum(len(word) for word in words)
        return total_length / len(words)
    
    def _calculate_caps_ratio(self, text: str) -> float:
        """Calcula proporção de letras em CAPS LOCK"""
        if not text:
            return 0.0
        letters = [c for c in text if c.isalpha()]
        if not letters:
            return 0.0
        caps_count = sum(1 for c in letters if c.isupper())
        return caps_count / len(letters)
    
    def _calculate_keyword_score(self, text: str, keywords: List[str]) -> float:
        """
        Calcula score baseado em presença de keywords (0.0 a 1.0)
        """
        if not keywords:
            return 0.0
        
        matches = sum(1 for keyword in keywords if keyword in text)
        return min(matches / 3.0, 1.0)  # Normaliza até 3 matches = score 1.0
    
    def _calculate_urgency_score(self, text: str) -> float:
        """Calcula score de urgência (0.0 a 1.0)"""
        urgency_keywords = [
            'urgente', 'imediato', 'asap', 'rápido', 'prazo',
            'emergência', 'crítico', 'quanto antes'
        ]
        
        score = 0.0
        
        # Palavras de urgência (+0.3 cada)
        for keyword in urgency_keywords:
            if keyword in text:
                score += 0.3
        
        # Exclamações múltiplas (+0.2)
        if text.count('!') >= 2:
            score += 0.2
        
        # CAPS LOCK excessivo (+0.2)
        caps_ratio = self._calculate_caps_ratio(text)
        if caps_ratio > 0.5:
            score += 0.2
        
        return min(score, 1.0)
    
    def _has_deadline_mention(self, text: str) -> bool:
        """Detecta menção a prazos ou datas limites"""
        deadline_patterns = [
            r'prazo',
            r'até (hoje|amanhã|segunda|terça|quarta|quinta|sexta)',
            r'até (?:dia|o dia) \d{1,2}',
            r'deadline',
            r'data limite'
        ]
        
        for pattern in deadline_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _count_negative_words(self, text: str) -> int:
        """Conta palavras negativas"""
        negative_words = [
            'não', 'nunca', 'nada', 'ninguém', 'problema', 'erro',
            'falha', 'ruim', 'péssimo', 'horrível', 'insatisfeito',
            'reclamação', 'decepcionado', 'frustrado'
        ]
        
        return sum(1 for word in negative_words if word in text)
    
    def _count_positive_words(self, text: str) -> int:
        """Conta palavras positivas"""
        positive_words = [
            'obrigado', 'agradeço', 'excelente', 'ótimo', 'bom',
            'parabéns', 'feliz', 'satisfeito', 'gostei', 'adorei'
        ]
        
        return sum(1 for word in positive_words if word in text)
    
    def _classify_by_features(self, text: str) -> str:
        """
        Classificação básica baseada apenas em features
        (usado como fallback adicional ou validação)
        """
        technical = self._calculate_keyword_score(text, self.technical_keywords)
        business = self._calculate_keyword_score(text, self.business_keywords)
        support = self._calculate_keyword_score(text, self.support_keywords)
        social = self._calculate_keyword_score(text, self.social_keywords)
        
        # Se tem score alto em technical/business/support → productive
        if technical > 0.3 or business > 0.3 or support > 0.3:
            return 'productive'
        
        # Se tem score alto em social e baixo nos outros → unproductive
        if social > 0.3 and technical < 0.1 and business < 0.1:
            return 'unproductive'
        
        # Default conservador
        return 'uncertain'
    
    def _calculate_confidence(self, text: str) -> float:
        """
        Calcula confiança da classificação baseada em features (0.0 a 1.0)
        """
        technical = self._calculate_keyword_score(text, self.technical_keywords)
        business = self._calculate_keyword_score(text, self.business_keywords)
        support = self._calculate_keyword_score(text, self.support_keywords)
        social = self._calculate_keyword_score(text, self.social_keywords)
        
        # Confiança alta quando há scores claros em uma categoria
        max_score = max(technical, business, support, social)
        
        # Se o score máximo é alto e os outros são baixos = alta confiança
        if max_score > 0.5:
            return 0.8
        elif max_score > 0.3:
            return 0.6
        else:
            return 0.3
