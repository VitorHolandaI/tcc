# Keystroke Service - Quick Start Guide

## Iniciar o Serviço

### Opção 1: Docker Compose (Recomendado)
```bash
cd /home/vitor/git/tcc
docker-compose up keystroke-service
```

### Opção 2: Local (Development)
```bash
cd /home/vitor/git/tcc/back/keystroke-service
pip install -r requirements.txt
python main.py
```

## Verificar se está Funcionando

```bash
curl http://localhost:8005/
```

Resposta esperada:
```json
{
  "service": "Keystroke Analysis Service",
  "status": "running",
  "version": "1.0.0"
}
```

## Testar Análise (com JWT token)

### 1. Obter JWT Token
```bash
# Faça login no frontend e copie o token do localStorage
# Ou use o endpoint /auth/login da main-api
```

### 2. Solicitar Análise
```bash
curl -X POST http://localhost:8005/analyze/1/123 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Resposta:
```json
{
  "message": "Keystroke analysis started in background",
  "status": "processing",
  "total_events": 1234
}
```

### 3. Consultar Resultados
```bash
curl http://localhost:8005/analysis/1/123 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Testar Módulos Localmente

```bash
cd /home/vitor/git/tcc/back/keystroke-service
python test_service.py
```

Saída esperada:
```
 analyzer.py imported successfully
 report_generator.py imported successfully
 config.py imported successfully
 database.py imported successfully
 KeyloggerAnalyzer initialized
 Typing metrics calculated
 Suspicious commands analyzed
 Cleanup successful
==================================================
All tests passed!
==================================================
```

## Ver Documentação da API

Abra no navegador:
```
http://localhost:8005/docs
```

## Logs

### Docker
```bash
docker-compose logs -f keystroke-service
```

### Local
Os logs aparecem no terminal onde você executou `python main.py`

## Troubleshooting

### Erro: "Module not found"
```bash
pip install -r requirements.txt
```

### Erro: "Firebase initialization failed"
Configure as variáveis:
```bash
export FIREBASE_PROJECT_ID=your-project-id
export FIREBASE_SERVICE_ACCOUNT=/path/to/serviceAccountKey.json
```

### Erro: "Database connection failed"
Verifique DATABASE_URL:
```bash
export DATABASE_URL=postgresql://testmaker:pass@localhost:5432/testmaker
```

### Porta 8005 já em uso
```bash
# Mudar porta
export KEYSTROKE_SERVICE_PORT=8015
```

## Estrutura de Dados Esperada

O serviço espera que `submissoes.keystroke_dynamics` contenha:
```json
[
  {
    "key": "a",
    "press_time": 1000,
    "release_time": 1100,
    "hold_time": 100,
    "flight_time": 0
  },
  {
    "key": "ctrl+v",
    "command_type": "paste",
    "press_time": 1200,
    "release_time": 1250,
    "hold_time": 50,
    "flight_time": 100
  }
]
```

## Próximos Passos

1. Integrar com frontend
2. Adicionar endpoint para gerar PDF
3. Implementar webhooks
4. Configurar monitoring

## Comandos Úteis

```bash
# Ver todas as portas dos serviços
docker-compose ps

# Rebuild apenas keystroke-service
docker-compose up --build keystroke-service

# Ver logs em tempo real
docker-compose logs -f keystroke-service

# Parar serviço
docker-compose stop keystroke-service

# Remover container
docker-compose rm -f keystroke-service

# Entrar no container
docker-compose exec keystroke-service bash
```

## Performance

- Análise típica: 1-2 segundos
- Análises concorrentes: até 5 (configurável)
- Eventos mínimos: 10 (configurável)

## Endpoints Disponíveis

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Health check |
| POST | `/analyze/{prova_id}/{aluno_id}` | Iniciar análise |
| GET | `/analysis/{prova_id}/{aluno_id}` | Obter resultados |
| GET | `/docs` | Documentação Swagger |
| GET | `/redoc` | Documentação ReDoc |

## Variáveis de Ambiente

Ver `.env.example` para lista completa.

Principais:
- `KEYSTROKE_SERVICE_PORT=8005`
- `DATABASE_URL=postgresql://...`
- `FIREBASE_PROJECT_ID=your-project-id`

## Status do Serviço

Verificar health:
```bash
curl http://localhost:8005/
```

Verificar no Docker:
```bash
docker-compose ps keystroke-service
```

## Suporte

- README.md - Documentação completa
- IMPLEMENTATION.md - Detalhes de implementação
- test_service.py - Exemplos de uso
- /docs - Swagger UI
