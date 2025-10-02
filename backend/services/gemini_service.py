import aiohttp
import asyncio
import logging
import os
from typing import Dict, Any, Optional
import json
import time

logger = logging.getLogger(__name__)

class GeminiService:
    """Service for interacting with Google AI Studio (Gemini API)"""
    
    def __init__(self):
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.model = "gemini-2.5-flash-lite"  
        self.fallback_model = "gemini-2.5-flash-lite"  
        

        self.circuit_breaker_errors = []
        self.circuit_breaker_threshold = 3  
        self.circuit_breaker_timeout = 45  
        self.circuit_open_until = 0
        

        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        self.api_key = gemini_key
    
    async def classify_email_with_context(
        self, 
        content: str, 
        subject: Optional[str] = None,
        company_config: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Classify email as productive or unproductive using tool calling for structured output
        Returns: Dict with 'category' (productive/unproductive) and reasoning
        """
        try:
            logger.info(f"[AI CLASSIFICATION] Starting with content length: {len(content)}, subject: '{subject}'")
            if company_config:
                logger.info(f"[AI CLASSIFICATION] Using custom config for: {company_config.get('company_name')}")
            
            if self._is_circuit_open():
                logger.warning("[AI CLASSIFICATION] Circuit breaker is OPEN - skipping AI call")
                raise Exception("Circuit breaker is open - too many recent errors")
            

            limited_content = content[:3000] if len(content) > 3000 else content
            subject_text = f"Assunto: {subject}\n\n" if subject else ""
            

            prompt = f"""Classifique este email como PRODUTIVO ou IMPRODUTIVO.

PRODUTIVO = Email relacionado aos NEGÓCIOS da empresa:
• Dúvidas sobre produtos/serviços
• Problemas técnicos ou bugs
• Solicitações de suporte ou informações
• Reclamações sobre serviços
• Questões comerciais (preços, contratos)
• Perguntas sobre a empresa (localização, horários, etc)

IMPRODUTIVO = Email pessoal/social SEM relação com negócios:
• Agradecimentos, gratificações, felicitações, convites são considerados pessoais/sociais
• Perguntas pessoais sobre funcionários
• Saudações sociais puras sem contexto
• Spam ou marketing externo
• Conversas casuais
• Promoções, atualizações de serviços que não tem haver com uma empresa de tecnologia

REGRAS: Se o email pergunta ALGO SOBRE A EMPRESA OU SEUS SERVIÇOS → PRODUTIVO / SE O EMAIL FOR URGENTE SOBRE ALGO DA EMPRESA -> PRODUTIVO


EMAIL:
Assunto: {subject if subject else "Sem assunto"}
Conteúdo: {limited_content}

Identifique o tipo de questão (ex: "problema técnico", "dúvida comercial", "conversa pessoal") e explique POR QUE é produtivo ou improdutivo em 2-3 frases claras."""


            response = await self._call_with_tool_calling(
                prompt=prompt,
                tool_name="classify_email",
                tool_description="Classifica email como produtivo ou improdutivo",
                parameters={
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["productive", "unproductive"],
                            "description": "Categoria do email"
                        },
                        "issue_type": {
                            "type": "string",
                            "description": "Tipo de questão identificada (ex: 'problema técnico', 'dúvida comercial', 'conversa pessoal', 'spam')"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Explicação específica (mínimo 30 palavras) do POR QUÊ é produtivo ou improdutivo. Deve identificar claramente o que torna este email relacionado ou não aos negócios da empresa."
                        },
                        "confidence": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                            "description": "Confiança na classificação"
                        }
                    },
                    "required": ["category", "issue_type", "reasoning", "confidence"]
                }
            )
            
            logger.info(f"[AI CLASSIFICATION] Result: {response['category']} (confidence: {response.get('confidence', 'unknown')}) - {response['reasoning']}")
            return response
            
        except Exception as e:
            logger.error(f"[AI CLASSIFICATION] Error: {str(e)}")
            raise
    
    async def generate_response(self, context: str, category: str, subject: str = None, sender: str = None, company_config: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Gera uma resposta estruturada (destinatário, assunto, corpo) baseada no contexto
        """
        try:

            if self._is_circuit_open():
                raise Exception("Circuit breaker open - too many recent failures")
            

            limited_context = context[:800] if len(context) > 800 else context
            prompt = self._create_structured_prompt(limited_context, category, subject, sender, company_config)
            

            response = await self._call_with_retry(prompt, max_output_tokens=1024)
            
            if not response or len(response.strip()) < 20:
                raise Exception("Gemini API returned empty or too short response")
            

            parsed = self._parse_structured_response(response, sender, subject)
            return parsed
            
        except Exception as e:
            logger.error(f"Error in AI text generation: {e}")
            raise Exception(f"Gemini Text Generation API failed: {e}")
    
    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open"""
        current_time = time.time()
        

        if current_time > self.circuit_open_until:
            self.circuit_breaker_errors = []
            return False
        

        recent_errors = [t for t in self.circuit_breaker_errors if current_time - t < 60]
        self.circuit_breaker_errors = recent_errors
        
        if len(recent_errors) >= self.circuit_breaker_threshold:
            logger.warning(f"Circuit breaker open: {len(recent_errors)} errors in last minute")
            return True
        
        return False
    
    def _record_error(self):
        """Record an error for circuit breaker"""
        current_time = time.time()
        self.circuit_breaker_errors.append(current_time)
        

        if len(self.circuit_breaker_errors) >= self.circuit_breaker_threshold:
            self.circuit_open_until = current_time + self.circuit_breaker_timeout
            logger.warning(f"Circuit breaker opened for {self.circuit_breaker_timeout}s")
    
    async def _call_with_retry(self, prompt: str, max_output_tokens: int = 512, max_attempts: int = 3) -> str:
        """Call Gemini API with retry logic and exponential backoff"""
        for attempt in range(max_attempts):
            try:

                model = self.fallback_model if attempt > 0 else self.model
                
 
                if attempt > 0:
                    backoff = (2 ** attempt) + (asyncio.get_event_loop().time() % 1)
                    logger.info(f"Retry attempt {attempt + 1}/{max_attempts} after {backoff:.2f}s with model {model}")
                    await asyncio.sleep(backoff)
                
                response = await self._call_gemini_api(prompt, max_output_tokens, model)
                
                if response:
                    logger.info(f"Successful response on attempt {attempt + 1} with model {model}")
                    return response
                    
            except Exception as e:
                error_str = str(e)
                

                if "503" in error_str or "UNAVAILABLE" in error_str:
                    self._record_error()
                    logger.warning(f"503 error on attempt {attempt + 1}: {error_str}")
                    

                    if attempt < max_attempts - 1:
                        continue
                

                if attempt == max_attempts - 1:
                    raise
                    
        raise Exception("All retry attempts failed")
    
    async def _call_gemini_api(self, prompt: str, max_tokens: int = None, model: str = None) -> str:
        """
        Faz chamada para API do Gemini
        """
        current_model = model or self.model
        url = f"{self.base_url}/{current_model}:generateContent"
        
        payload = {
            "contents": [{
                "role": "user",
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": max_tokens or 512, 
                "topP": 0.8,
                "topK": 40,
                "candidateCount": 1,
                "responseMimeType": "text/plain"
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"Starting Gemini API call with prompt length: {len(prompt)}")
            
            timeout = aiohttp.ClientTimeout(total=12) 
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(f"{url}?key={self.api_key}", json=payload, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Gemini API call successful")
                        

                        try:
                            if 'candidates' in result and result['candidates']:
                                candidate = result['candidates'][0]
                                finish_reason = candidate.get('finishReason', 'UNKNOWN')
                                logger.info(f"Gemini finish reason: {finish_reason}")
                                

                                generated_text = ""

                                if 'content' in candidate and 'parts' in candidate['content']:
                 
                                    parts = candidate['content']['parts']
                                    generated_text = ''.join(part.get('text', '') for part in parts if 'text' in part)
                                elif 'content' in candidate and 'text' in candidate['content']:
                                    generated_text = candidate['content']['text']
                                elif 'text' in candidate:
                                    generated_text = candidate['text']
                                
                                if generated_text.strip():
                                    logger.info(f"Extracted text ({len(generated_text)} chars): {generated_text[:100]}...")
                                    return generated_text.strip()
                                
                              
                                if finish_reason == 'MAX_TOKENS':
                                    logger.warning("Response truncated due to max tokens, will retry with shorter prompt")
                                    return ""
                                
                            logger.error(f"Could not extract text from response structure: {result}")
                            return ""
                            
                        except (KeyError, IndexError) as e:
                            logger.error(f"Error parsing Gemini response: {e}")
                            logger.error(f"Full response: {result}")
                            return ""
                    else:
                        error_text = await response.text()
                        logger.error(f"Gemini API call failed: {response.status} - {error_text}")
                        raise Exception(f"Gemini API failed with status {response.status}")
                        
        except asyncio.TimeoutError:
            logger.error("Gemini API call timed out")
            raise Exception("Gemini API timed out")
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            raise Exception(f"Gemini API call failed: {str(e)}")
    
    def _create_structured_prompt(self, context: str, category: str, subject: str = None, sender: str = None, company_config: Optional[Dict[str, str]] = None) -> str:
        """
        Cria prompt estruturado para gerar resposta em JSON com extração inteligente de informações
        """
        import re
        
    
        sender_email = None
        sender_name = sender
        
        if sender and '@' in sender:
            sender_email = sender
            sender_name = sender.split('@')[0].replace('.', ' ').title()
        
      
        if not sender_email:
            email_match = re.search(r'([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)', context)
            if email_match:
                sender_email = email_match.group(1)
        
        
        if not sender_name or sender_name == sender:
            sig_match = re.search(r'(?:Atenciosamente|Cordialmente|Abraços|At\.te)[,\s]*\n+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)+)', context, re.IGNORECASE)
            if sig_match:
                sender_name = sig_match.group(1).strip()
        
     
        sender_role = None
        if sender_name:
            
            name_pattern = re.escape(sender_name)
            role_match = re.search(rf'{name_pattern}\s*\n\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç\s]+(?:de|da|do)\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+|[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç\s]+)', context)
            if role_match:
                potential_role = role_match.group(1).strip()
                
                if not re.search(r'[@\d\(\)]', potential_role) and len(potential_role) < 50:
                    sender_role = potential_role
        
       
        recipient = sender_email if sender_email else "cliente@email.com"
        response_subject = f"Re: {subject}" if subject else "Re: Sua Solicitação"
        greeting = f"Prezado(a) {sender_name}" if sender_name and sender_name != sender else "Prezado(a)"
        
        
        company_name = (company_config or {}).get('company_name', 'Equipe de Suporte')
        
        sender_context = f"{sender_name}"
        if sender_role:
            sender_context += f" ({sender_role})"
        if sender_email:
            sender_context += f" - {sender_email}"
        
        
        custom_instructions = ""
        if company_config and company_config.get('custom_instructions'):
            custom_instructions = f"\n\nINSTRUÇÕES PERSONALIZADAS DA EMPRESA:\n{company_config['custom_instructions']}"
        
        if category == 'unproductive':
            prompt = f"""Você é um assistente profissional da empresa {company_name}.

CATEGORIA: Email social/pessoal (IMPRODUTIVO)

CONTEXTO DO EMAIL RECEBIDO:
{context}

REMETENTE: {sender_context}
ASSUNTO: {subject or 'Não especificado'}

INSTRUÇÕES PARA RESPOSTA:
1. Leia o contexto do email e identifique o tipo de mensagem (agradecimento, convite, felicitação, etc)
2. Crie uma resposta BREVE (2-4 linhas) e personalizada para o contexto específico
3. Seja cordial mas profissional
4. VARIE o texto - não use sempre a mesma resposta genérica
5. SEMPRE termine com: "Atenciosamente,\\n{company_name}"{custom_instructions}

EXEMPLO DE VARIAÇÃO:
- Para agradecimento: agradeça de volta e deseje sucesso
- Para convite: agradeça pelo convite e responda educadamente
- Para felicitação: agradeça e retribua os votos
- Para mensagem genérica: seja cordial mas objetivo

Gere APENAS um JSON válido com uma resposta personalizada:
{{
  "to": "{recipient}",
  "subject": "{response_subject}",
  "body": "[GERE RESPOSTA CURTA PERSONALIZADA BASEADA NO CONTEXTO]"
}}"""
        else:
            prompt = f"""Você é um assistente profissional da empresa {company_name}.

CATEGORIA: Email de negócios (PRODUTIVO)

CONTEXTO DO EMAIL RECEBIDO:
{context}

REMETENTE: {sender_context}
ASSUNTO: {subject or 'Não especificado'}

INSTRUÇÕES PARA RESPOSTA:
1. Analise o tipo de solicitação (problema técnico, dúvida comercial, suporte, etc)
2. Seja ESPECÍFICO - mencione detalhes do problema/questão do remetente
3. Ofereça solução clara ou próximos passos
4. Use tom profissional mas acessível
5. VARIE a resposta baseada no contexto - não use template genérico
6. SEMPRE termine com: "Atenciosamente,\\n{company_name}"{custom_instructions}

EXEMPLOS DE VARIAÇÃO:
- Problema técnico: reconheça o problema específico + ofereça solução ou investigação
- Dúvida comercial: responda a pergunta específica + ofereça mais informações se necessário
- Suporte geral: responda a questão + indique canal apropriado se necessário

Gere APENAS um JSON válido com resposta personalizada e específica:
{{
  "to": "{recipient}",
  "subject": "{response_subject}",
  "body": "[GERE RESPOSTA DETALHADA E ESPECÍFICA BASEADA NO CONTEXTO]"
}}"""
        
        return prompt
    
    def _parse_structured_response(self, response: str, sender: str = None, subject: str = None) -> Dict[str, str]:
        """
        Parse JSON response from Gemini
        """
        try:
            
            response = response.strip()
            
            
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            
            parsed = json.loads(response.strip())
            
            
            if "to" in parsed and "subject" in parsed and "body" in parsed:
                return {
                    "to": parsed["to"],
                    "subject": parsed["subject"],
                    "body": parsed["body"]
                }
            
            raise ValueError("Missing required fields in JSON")
            
        except Exception as e:
            logger.warning(f"Failed to parse JSON response, creating fallback: {e}")
            
            
            return {
                "to": sender if sender else "cliente@email.com",
                "subject": f"Re: {subject}" if subject else "Resposta ao seu contato",
                "body": self._format_response(response)
            }
    
    def _format_response(self, response: str) -> str:
        """
        Limpa e formata a resposta gerada pelo Gemini
        """
        
        formatted = response.strip()
        
        
        if "Resposta profissional:" in formatted:
            formatted = formatted.split("Resposta profissional:")[-1].strip()
        
        return formatted
    
    async def _call_with_tool_calling(self, prompt: str, tool_name: str, tool_description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call Gemini API with tool calling (function calling) for structured output
        """
        url = f"{self.base_url}/{self.model}:generateContent"
        
        payload = {
            "contents": [{
                "role": "user",
                "parts": [{"text": prompt}]
            }],
            "tools": [{
                "function_declarations": [{
                    "name": tool_name,
                    "description": tool_description,
                    "parameters": parameters
                }]
            }],
            "tool_config": {
                "function_calling_config": {
                    "mode": "ANY",
                    "allowed_function_names": [tool_name]
                }
            },
            "generationConfig": {
                "temperature": 0.1,  
                "maxOutputTokens": 256,
                "candidateCount": 1
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"[TOOL CALLING] Invoking {tool_name} with prompt length: {len(prompt)}")
            
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(f"{url}?key={self.api_key}", json=payload, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"[TOOL CALLING] API call successful")
                        
                       
                        if 'candidates' in result and result['candidates']:
                            candidate = result['candidates'][0]
                            
                            if 'content' in candidate and 'parts' in candidate['content']:
                                for part in candidate['content']['parts']:
                                    if 'functionCall' in part:
                                        function_call = part['functionCall']
                                        if function_call.get('name') == tool_name:
                                            args = function_call.get('args', {})
                                            logger.info(f"[TOOL CALLING] Extracted args: {args}")
                                            return args
                        
                        
                        logger.warning("[TOOL CALLING] No function call found, trying text fallback")
                        if 'candidates' in result and result['candidates']:
                            candidate = result['candidates'][0]
                            if 'content' in candidate and 'parts' in candidate['content']:
                                text = candidate['content']['parts'][0].get('text', '')
                                try:
                                    return json.loads(text.strip())
                                except:
                                    pass
                        
                        raise Exception("Could not extract structured output from response")
                    else:
                        error_text = await response.text()
                        logger.error(f"[TOOL CALLING] API call failed: {response.status} - {error_text}")
                        raise Exception(f"Tool calling API failed with status {response.status}")
                        
        except asyncio.TimeoutError:
            logger.error("[TOOL CALLING] API call timed out")
            raise Exception("Tool calling API timed out")
        except Exception as e:
            logger.error(f"[TOOL CALLING] Error: {str(e)}")
            raise Exception(f"Tool calling failed: {str(e)}")