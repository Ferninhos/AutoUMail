# Email Classification API

Backend FastAPI para classificação de emails e geração de respostas automáticas usando Gemini AI.

## Instalação

1. Instalar dependências:
```bash
pip install -r requirements.txt
```

2. Executar servidor:
```bash
python main.py
```

Ou usando uvicorn diretamente:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### POST /classify-email
Classifica um email como produtivo ou improdutivo e gera resposta automática.

**Request:**
```json
{
  "content": "Texto do email aqui...",
  "subject": "Assunto do email (opcional)",
  "sender": "email@exemplo.com (opcional)"
}
```

**Response:**
```json
{
  "id": "classification-uuid",
  "email": {
    "id": "email-uuid",
    "content": "Texto do email...",
    "subject": "Assunto",
    "sender": "email@exemplo.com",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "category": "productive",
  "confidence": 0.89,
  "suggestedResponse": "Resposta automática gerada...",
  "processedAt": "2024-01-15T10:30:05Z"
}
```
