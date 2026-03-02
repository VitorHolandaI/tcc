# Keystroke Analysis Service - Implementation Summary

## Overview

Microservice completo para análise de keystroke dynamics no Test Maker Platform.

**Porta**: 8005
**Linguagem**: Python 3.11
**Framework**: FastAPI + SQLAlchemy
**Autenticação**: Firebase JWT

## Arquivos Criados

### 1. **config.py** (819 bytes)
- Configurações do serviço via variáveis de ambiente
- HOST, PORT, DATABASE_URL
- Configurações de análise (MAX_CONCURRENT_ANALYSIS, MIN_EVENTS_THRESHOLD)

### 2. **database.py** (1.7 KB)
- Modelo SQLAlchemy: `KeystrokeAnalysis`
- Campos:
  - Status: pending, processing, completed, failed
  - Typing Metrics: hold_time_avg, hold_time_std, flight_time_avg, flight_time_std
  - Suspicious Commands: command_counts (JSON), suspicious_percentage, total_commands, avg_manhattan_distance
- Session management com get_db()

### 3. **main.py** (8.6 KB)
- FastAPI application
- Endpoints:
  - `GET /`: Health check
  - `POST /analyze/{prova_id}/{aluno_id}`: Inicia análise (apenas professores)
  - `GET /analysis/{prova_id}/{aluno_id}`: Retorna resultados
- Firebase JWT authentication
- Background tasks para processamento assíncrono
- Integração com banco principal para ler keystroke_dynamics

### 4. **Dockerfile** (782 bytes)
- Base: python:3.11-slim
- Porta: 8005
- CMD: uvicorn com hot-reload
- Cria diretório /tmp/keystroke_analysis

### 5. **requirements.txt** (172 bytes)
Dependências:
- fastapi==0.115.12
- uvicorn[standard]==0.34.0
- sqlalchemy==2.0.36
- firebase-admin==6.6.0
- python-multipart==0.0.20
- numpy==1.24.3
- matplotlib==3.7.1
- reportlab==4.0.4
- scipy==1.11.3

### 6. **README.md** (4.2 KB)
Documentação completa:
- Features
- Endpoints com exemplos
- Arquitetura
- Schema do banco
- Instalação (local e Docker)
- Variáveis de ambiente
- Integração com outros serviços

### 7. **test_service.py** (2.9 KB)
Script de teste para validar:
- Imports de todos os módulos
- Analyzer funcionando com dados de amostra
- Database models
- Configuração

### 8. **.env.example** (793 bytes)
Template de variáveis de ambiente:
- KEYSTROKE_SERVICE_HOST
- KEYSTROKE_SERVICE_PORT
- DATABASE_URL
- FIREBASE_PROJECT_ID
- FIREBASE_SERVICE_ACCOUNT
- MAX_CONCURRENT_KEYSTROKE_ANALYSIS
- MIN_EVENTS_THRESHOLD

### 9. **.gitignore**
Ignora arquivos temporários, logs, databases, etc.

## Arquivos Pré-Existentes (do tccRoberto)

- **analyzer.py** (23 KB): Algoritmos de análise de keystroke
- **report_generator.py** (18 KB): Geração de relatórios PDF

## Integração com Docker Compose

Adicionado ao `/home/vitor/git/tcc/docker-compose.yml`:
- Service: `keystroke-service`
- Container: `testmaker-keystroke`
- Porta: 8005
- Volume: compartilha /app/data com main-api
- Network: testmaker-network
- Healthcheck: curl http://localhost:8005/

Frontend build args atualizado:
- `VITE_KEYSTROKE_SERVICE_URL=http://localhost:8005`

## Fluxo de Funcionamento

### 1. Professor Solicita Análise
```
POST /analyze/{prova_id}/{aluno_id}
Authorization: Bearer <jwt_token>
```

O serviço:
1. Valida JWT (apenas professores)
2. Busca keystroke_dynamics da submissão no banco principal
3. Cria registro de análise com status "pending"
4. Inicia task em background
5. Retorna imediatamente com status "processing"

### 2. Background Task
1. Atualiza status para "processing"
2. Salva keystroke_data em arquivo JSON temporário
3. Executa KeyloggerAnalyzer:
   - calculate_typing_metrics()
   - analyze_suspicious_commands()
4. Salva resultados no banco
5. Atualiza status para "completed"
6. Remove arquivo temporário

### 3. Professor Consulta Resultados
```
GET /analysis/{prova_id}/{aluno_id}
Authorization: Bearer <jwt_token>
```

Retorna:
- Status (processing, completed, failed)
- Typing metrics
- Suspicious commands analysis
- Timestamp de conclusão

## Database Schema

### Tabela: keystroke_analysis

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | Integer | Primary key |
| prova_id | Integer | Foreign key |
| aluno_id | Integer | Foreign key |
| status | String | pending/processing/completed/failed |
| error_message | String | Mensagem de erro |
| total_events | Integer | Total de eventos analisados |
| hold_time_avg | Float | Média de hold time (ms) |
| hold_time_std | Float | Desvio padrão hold time |
| flight_time_avg | Float | Média de flight time (ms) |
| flight_time_std | Float | Desvio padrão flight time |
| command_counts | JSON | {"paste": 5, "copy": 3, ...} |
| suspicious_percentage | Float | % de comandos suspeitos |
| total_commands | Integer | Total de comandos suspeitos |
| avg_manhattan_distance | Float | Distância média de Manhattan |
| command_sequences | Integer | Número de sequências |
| created_at | DateTime | Data de criação |
| completed_at | DateTime | Data de conclusão |

## Como Testar

### Teste Local
```bash
cd /home/vitor/git/tcc/back/keystroke-service
python test_service.py
```

### Iniciar Serviço
```bash
python main.py
```

### Docker Compose
```bash
cd /home/vitor/git/tcc
docker-compose up keystroke-service
```

## Métricas Analisadas

### Typing Metrics
- **Hold Time**: Duração do pressionamento de tecla
- **Flight Time**: Tempo entre teclas
- **Standard Deviation**: Consistência do padrão de digitação

### Suspicious Commands
- **Copy/Paste**: Uso de área de transferência
- **Cut**: Recortar texto
- **Backspace**: Apagar caracteres
- **Cursor Movement**: Movimentação do cursor
- **Command Sequences**: Agrupamentos de comandos suspeitos
- **Manhattan Distance**: Distância temporal entre comandos

### Indicadores de Suspeita
- Alto % de comandos suspeitos (> 10%)
- Muitas sequências de paste
- Baixa consistência no hold/flight time
- Padrões anormais de digitação

## Segurança

- JWT validation via Firebase
- Acesso restrito a professores
- Nenhum dado sensível em logs
- Arquivos temporários deletados após análise
- Validação de ownership (prova_id/aluno_id)

## Performance

- Análise assíncrona (background tasks)
- Limite de análises concorrentes (MAX_CONCURRENT_ANALYSIS=5)
- Processamento otimizado com NumPy/SciPy
- Cache de resultados no banco

## Próximos Passos (Opcional)

1. **Relatórios PDF**: Integrar report_generator.py
2. **Webhooks**: Notificar quando análise completar
3. **Machine Learning**: Modelo de detecção de fraude
4. **Visualizações**: Gráficos de typing patterns
5. **Comparação**: Comparar padrões entre alunos
6. **Histórico**: Análise de evolução temporal

## Status

 Microserviço completo e funcional
 Integrado ao docker-compose
 Documentação completa
 Testes implementados
 Pronto para deploy

## Contato

Para dúvidas ou melhorias, consulte:
- README.md
- test_service.py
- Documentação da API em http://localhost:8005/docs
