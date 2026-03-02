# COMO RODAR O PROJETO - Guia Completo

**Data:** 2026-02-11
**Versão:** 2.0 (Arquitetura de Microserviços)

---

## Índice

1. [Visão Geral da Arquitetura](#-visão-geral-da-arquitetura)
2. [Pré-requisitos](#-pré-requisitos)
3. [Configuração Inicial](#-configuração-inicial)
4. [Como Rodar TUDO (Forma Rápida)](#-como-rodar-tudo-forma-rápida)
5. [Como Rodar Cada Serviço Individualmente](#-como-rodar-cada-serviço-individualmente)
6. [Testando o Sistema](#-testando-o-sistema)
7. [Troubleshooting](#-troubleshooting)
8. [Comandos Úteis](#-comandos-úteis)

---

## Visão Geral da Arquitetura

O projeto é composto por **6 serviços independentes**:

```
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND (3000) │
│ React + TypeScript │
└───┬─────────┬──────────┬──────────┬──────────┬─────────────────┘
    │ │ │ │ │
    ▼ ▼ ▼ ▼ ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Main API│ │Screen │ │ Gaze │ │Webcam │ │ Audio │
│ :8000 │ │ :8001 │ │ :8002 │ │ :8003 │ │ :8004 │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘
     │ │ │ │ │
     └─────────┴──────────┴──────────┴──────────┘
                         │
                 ┌───────▼────────┐
                 │ PostgreSQL │
                 │ (Shared DB) │
                 └────────────────┘
```

### O Que Cada Serviço Faz

| Serviço | Porta | Função | Tecnologias |
|---------|-------|--------|-------------|
| **Main API** | 8000 | Gerenciamento geral (provas, questões, submissões) | FastAPI, SQLAlchemy |
| **Screen Recording** | 8001 | Captura de tela (screen) do aluno | WebSocket, ffmpeg |
| **Gaze Analysis** | 8002 | Análise de direção do olhar (webcam) | MediaPipe, OpenCV |
| **Webcam Service** | 8003 | Captura de vídeo da webcam | WebSocket |
| **Audio Service** | 8004 | Captura e análise de áudio (diarização) | pyannote.audio, torch |
| **Frontend** | 3000 | Interface web (professor e aluno) | React, Vite |

---

## Pré-requisitos

### Software Necessário

- **Docker** (recomendado) ou:
  - Python 3.11+
  - Node.js 18+
  - PostgreSQL (ou SQLite para desenvolvimento)

### Tokens e Configurações

1. **Firebase Project** (obrigatório)
   - Criar projeto em https://console.firebase.google.com
   - Baixar `serviceAccountKey.json`

2. **HuggingFace Token** (para análise de áudio)
   - Criar conta em https://huggingface.co
   - Obter token em https://huggingface.co/settings/tokens
   - Aceitar licença do modelo: https://huggingface.co/pyannote/speaker-diarization-3.1

---

## Configuração Inicial

### 1. Clonar Repositório

```bash
cd /home/vitor/git/tcc
```

### 2. Criar Arquivo `.env`

**No diretório raiz:**

```bash
# .env
FIREBASE_PROJECT_ID=seu-projeto-firebase
HUGGINGFACE_TOKEN=seu-token-huggingface
```

### 3. Configurar Frontend

```bash
cd front
cp .env.example .env

# Editar .env:
VITE_API_BASE_URL=http://localhost:8000
VITE_RECORDING_SERVICE_URL=http://localhost:8001
VITE_ANALYSIS_SERVICE_URL=http://localhost:8002
VITE_WEBCAM_SERVICE_URL=http://localhost:8003
VITE_AUDIO_SERVICE_URL=http://localhost:8004
```

### 4. Criar Diretórios de Gravação

```bash
mkdir -p back/recordings
mkdir -p back/webcam_recordings
mkdir -p back/audio_recordings
mkdir -p back/data
mkdir -p back/logs
```

---

## Como Rodar TUDO (Forma Rápida)

### Via Docker Compose (Recomendado)

```bash
# Na raiz do projeto
docker-compose up --build

# Em background
docker-compose up --build -d
```

**Isso vai iniciar todos os 6 serviços automaticamente!**

Aguarde até ver:
```
 testmaker-main-api | Uvicorn running on http://0.0.0.0:8000
 testmaker-recording | Uvicorn running on http://0.0.0.0:8001
 testmaker-analysis | Uvicorn running on http://0.0.0.0:8002
 testmaker-webcam | Uvicorn running on http://0.0.0.0:8003
 testmaker-audio | Uvicorn running on http://0.0.0.0:8004
 testmaker-frontend | Nginx started
```

### Verificar se Está Tudo Rodando

```bash
# Main API
curl http://localhost:8000/

# Screen Recording
curl http://localhost:8001/health

# Gaze Analysis
curl http://localhost:8002/

# Webcam
curl http://localhost:8003/

# Audio
curl http://localhost:8004/

# Frontend
curl http://localhost:3000/
```

---

## Como Rodar Cada Serviço Individualmente

Se você NÃO quer usar Docker ou quer rodar apenas alguns serviços:

### 1 Main API (:8000)

```bash
cd back

# Instalar dependências
pip install -r requirements.txt

# Rodar
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Endpoints:**
- `GET /` - Health check
- `POST /provas` - Criar prova
- `GET /questoes/prova/{id}` - Listar questões
- `POST /submissoes` - Enviar submissão

---

### 2 Screen Recording Service (:8001)

```bash
cd back/recording-service

# Instalar dependências
pip install -r requirements.txt

# Configurar .env
echo "RECORDING_SERVICE_PORT=8001" > .env
echo "RECORDINGS_DIR=../recordings" >> .env

# Rodar
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

**Endpoints:**
- `WebSocket /ws/{prova_id}` - Stream de tela
- `GET /health` - Health check

**O que faz:**
- Recebe chunks de vídeo da **tela** do aluno via WebSocket
- Salva em `back/recordings/prova_{id}_aluno_{id}.webm`

---

### 3 Gaze Analysis Service (:8002)

```bash
cd back/analysis-service

# Instalar dependências
pip install -r requirements.txt

# Configurar .env
echo "ANALYSIS_SERVICE_PORT=8002" > .env
echo "RECORDINGS_DIR=../recordings" >> .env

# Rodar
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

**Endpoints:**
- `POST /analyze/{prova_id}/{aluno_id}` - Iniciar análise
- `GET /analysis/{prova_id}/{aluno_id}` - Ver resultado

**O que faz:**
- Analisa vídeo da **webcam** com MediaPipe
- Detecta direção do olhar (Forward, Left, Right, Up, Down)
- Calcula métricas de distração

---

### 4 Webcam Service (:8003)

```bash
cd back/webcam-service

# Instalar dependências
pip install -r requirements.txt

# Rodar
uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

**Endpoints:**
- `WebSocket /ws/{prova_id}` - Stream de webcam
- `GET /` - Health check

**O que faz:**
- Recebe chunks de vídeo da **webcam** do aluno via WebSocket
- Salva em `back/webcam_recordings/webcam_prova_{id}_aluno_{id}.webm`

---

### 5 Audio Service (:8004)

```bash
cd back/audio-service

# Instalar dependências
pip install -r requirements.txt

# Configurar .env
echo "AUDIO_SERVICE_PORT=8004" > .env
echo "HUGGINGFACE_TOKEN=seu_token_aqui" >> .env

# Rodar
uvicorn main:app --host 0.0.0.0 --port 8004 --reload
```

**Endpoints:**
- `WebSocket /ws/{prova_id}` - Stream de áudio
- `POST /analyze/{prova_id}/{aluno_id}` - Iniciar análise
- `GET /analysis/{prova_id}/{aluno_id}` - Ver resultado

**O que faz:**
- Recebe chunks de **áudio do microfone** via WebSocket
- Analisa com pyannote.audio (speaker diarization)
- Detecta múltiplas vozes ao longo do tempo

---

### 6 Frontend (:3000)

```bash
cd front

# Instalar dependências
npm install

# Rodar em desenvolvimento
npm run dev

# Build para produção
npm run build
npm run preview
```

**Acessar:** http://localhost:3000

---

## Testando o Sistema

### Teste Completo (Professor → Aluno → Análise)

#### 1. Criar Professor

```bash
# Via frontend: http://localhost:3000/register
# Ou via curl:
curl -X POST http://localhost:8000/professor/register \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Prof. Teste",
    "email": "prof@test.com",
    "matricula": "PROF001"
  }'
```

#### 2. Criar Prova

```bash
# Login como professor no frontend
# Dashboard → Criar Nova Prova
# Ou via curl (com JWT token)
```

#### 3. Aluno Faz Prova

1. Registrar aluno: http://localhost:3000/register
2. Login como aluno
3. Entrar na prova
4. **O navegador vai pedir 3 permissões:**
   - Compartilhar tela
   - Acessar webcam
   - Acessar microfone
5. Resolver questões
6. Finalizar prova

#### 4. Professor Solicita Análise

1. Login como professor
2. Dashboard → Detalhes da Prova
3. Clicar em "Gerar Análise de Gaze"
4. Aguardar processamento (~2-5 min por aluno)
5. Ver resultados:
   - Percentual olhando para frente
   - Trocas de posição por minuto
   - Períodos suspeitos

#### 5. Professor Solicita Análise de Áudio

1. Clicar em "Analisar Áudio"
2. Aguardar processamento (~1-3 min)
3. Ver resultados:
   - Número de speakers detectados
   - Timeline de vozes
   - Períodos com múltiplas vozes

---

## Troubleshooting

### Erro: "Address already in use"

```bash
# Verificar portas ocupadas
lsof -i :8000
lsof -i :8001
lsof -i :8002
lsof -i :8003
lsof -i :8004

# Matar processo
kill -9 <PID>
```

### Erro: "WebSocket failed to connect"

1. Verificar se o serviço está rodando:
   ```bash
   curl http://localhost:8001/health
   ```

2. Verificar logs:
   ```bash
   docker-compose logs recording-service
   ```

3. Verificar variáveis de ambiente no frontend (.env)

### Erro: "Invalid token" (JWT)

1. Verificar `FIREBASE_PROJECT_ID` no .env
2. Refazer login no frontend
3. Verificar se `serviceAccountKey.json` está correto

### Erro: "pyannote.audio failed" (Audio Service)

1. Verificar `HUGGINGFACE_TOKEN` no .env
2. Aceitar licença do modelo: https://huggingface.co/pyannote/speaker-diarization-3.1
3. Verificar logs:
   ```bash
   docker-compose logs audio-service
   ```

### Erro: "Video not found" (Analysis)

1. Verificar se gravação existe:
   ```bash
   ls back/recordings/
   ls back/webcam_recordings/
   ls back/audio_recordings/
   ```

2. Verificar se aluno completou a prova
3. Verificar logs do recording service

---

## Comandos Úteis

### Docker Compose

```bash
# Iniciar tudo
docker-compose up

# Iniciar em background
docker-compose up -d

# Rebuild após mudanças
docker-compose up --build

# Ver logs
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f audio-service

# Parar tudo
docker-compose down

# Parar e remover volumes
docker-compose down -v

# Escalar serviço (múltiplas instâncias)
docker-compose up --scale analysis-service=3
```

### Ver Status dos Containers

```bash
docker ps
docker ps -a
```

### Entrar em um Container

```bash
docker exec -it testmaker-audio bash
docker exec -it testmaker-analysis bash
```

### Ver Logs de um Container

```bash
docker logs testmaker-audio -f
docker logs testmaker-analysis -f
```

### Limpar Tudo

```bash
# Parar containers
docker-compose down

# Remover volumes
docker volume prune

# Remover imagens
docker image prune -a

# Limpar gravações
rm -rf back/recordings/*
rm -rf back/webcam_recordings/*
rm -rf back/audio_recordings/*
```

---

## Estrutura de Diretórios

```
tcc/
├── back/
│ ├── app/ # Main API
│ │ ├── controllers/
│ │ ├── models/
│ │ ├── services/
│ │ └── main.py
│ │
│ ├── recording-service/ # Screen Recording (:8001)
│ │ ├── main.py
│ │ ├── Dockerfile
│ │ └── requirements.txt
│ │
│ ├── analysis-service/ # Gaze Analysis (:8002)
│ │ ├── main.py
│ │ ├── video_analyzer.py
│ │ ├── Dockerfile
│ │ └── requirements.txt
│ │
│ ├── webcam-service/ # Webcam Capture (:8003)
│ │ ├── main.py
│ │ ├── Dockerfile
│ │ └── requirements.txt
│ │
│ ├── audio-service/ # Audio Analysis (:8004)
│ │ ├── main.py
│ │ ├── audio_analyzer.py
│ │ ├── Dockerfile
│ │ └── requirements.txt
│ │
│ ├── recordings/ # Screen recordings
│ ├── webcam_recordings/ # Webcam videos
│ ├── audio_recordings/ # Audio files
│ ├── data/ # Database
│ └── logs/ # Logs
│
├── front/ # Frontend (:3000)
│ ├── src/
│ │ ├── components/
│ │ ├── pages/
│ │ └── services/
│ ├── package.json
│ └── .env
│
├── docker-compose.yml # Orquestração de containers
├── COMO_RODAR.md # Este arquivo
└── .env # Variáveis de ambiente globais
```

---

## Fluxo de Dados

### Durante a Prova (Aluno)

```
Aluno abre prova
    ↓
Solicita 3 permissões
    ├─ Screen sharing → Recording Service (:8001)
    ├─ Webcam access → Webcam Service (:8003)
    └─ Microphone access → Audio Service (:8004)
    ↓
3 WebSockets ativos enviando chunks
    ↓
Salva em 3 diretórios diferentes
    ├─ recordings/prova_1_aluno_1.webm (tela)
    ├─ webcam_recordings/webcam_...webm (webcam)
    └─ audio_recordings/prova_1_aluno_1.wav (áudio)
```

### Após a Prova (Professor)

```
Professor clica "Gerar Análise de Gaze"
    ↓
Analysis Service (:8002)
    ├─ Lê webcam_recordings/webcam_...webm
    ├─ Processa com MediaPipe
    └─ Salva resultados no DB
    ↓
Professor clica "Analisar Áudio"
    ↓
Audio Service (:8004)
    ├─ Lê audio_recordings/prova_1_aluno_1.wav
    ├─ Processa com pyannote.audio
    └─ Salva resultados no DB
```

---

## Checklist de Funcionamento

- [ ] Todos os 7 serviços iniciam sem erros
- [ ] Frontend acessível em http://localhost:3000
- [ ] Professor consegue criar prova
- [ ] Aluno consegue se registrar
- [ ] Aluno consegue fazer login
- [ ] Aluno consegue entrar na prova
- [ ] **Navegador solicita 3 permissões** (tela, webcam, microfone)
- [ ] Gravação de tela funciona
- [ ] Gravação de webcam funciona
- [ ] Gravação de áudio funciona
- [ ] Aluno consegue submeter código
- [ ] Aluno consegue finalizar prova
- [ ] Professor consegue ver submissões
- [ ] Professor consegue solicitar análise de gaze
- [ ] Análise de gaze completa com sucesso
- [ ] Professor consegue solicitar análise de áudio
- [ ] Análise de áudio completa com sucesso

---

## 🆘 Suporte

**Se algo não funcionar:**

1. Verifique os logs de cada serviço
2. Verifique as variáveis de ambiente
3. Verifique as permissões dos diretórios
4. Consulte a seção [Troubleshooting](#-troubleshooting)
5. Leia a documentação específica de cada serviço

**Para dúvidas sobre um serviço específico:**
- Main API → `back/app/`
- Screen Recording → `back/recording-service/README.md`
- Gaze Analysis → `back/analysis-service/README.md`
- Webcam Service → `back/webcam-service/`
- Audio Service → `back/audio-service/`

---

** Sistema completo e pronto para uso!**
