# Analysis Service - Modular Video Gaze Analysis

**Microservice separado e escalável para análise de vídeos de provas**

---

## Visão Geral

Este serviço é um **container independente** que processa análises de gaze (direção do olhar) em vídeos de provas. É **completamente modular**, permitindo adicionar mais serviços de análise no futuro.

### Características

- **Separado do Main API** - Roda em container próprio (porta 8002)
- **JWT Authentication** - Validação via Firebase
- **Background Processing** - Não bloqueia requests
- **Resume Capability** - Retoma de onde parou se cair
- **Progress Tracking** - Salva progresso no banco
- **Escalável** - Pode rodar múltiplas instâncias

---

## Arquitetura

```
┌─────────────────────────────────────────────┐
│ Frontend (porta 3000) │
└───────────────┬─────────────────────────────┘
                │
    ┌───────────┼────────────┐
    │ │ │
┌───▼────┐ ┌──▼──────┐ ┌─▼────────────┐
│Main API│ │Recording│ │Analysis │
│:8000 │ │:8001 │ │:8002 │ ⭐ Este serviço
└────────┘ └─────────┘ └──┬───────────┘
                            │
                    ┌───────▼────────┐
                    │ MediaPipe │
                    │ (Gaze Analysis)│
                    └────────────────┘
```

---

## Como Usar

### 1. Iniciar o serviço

```bash
# Via Docker Compose (recomendado)
docker-compose up analysis-service

# Ou standalone
cd back/analysis-service
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8002
```

### 2. Endpoints

#### **POST /analyze/{prova_id}/{aluno_id}**
Inicia análise de vídeo (background)

**Requisitos:**
- JWT token de professor
- Prova deve ter terminado (`data_fim < now`)
- Vídeo deve existir

**Request:**
```bash
curl -X POST http://localhost:8002/analyze/1/42 \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

**Response:**
```json
{
  "message": "Analysis started in background",
  "status": "processing",
  "prova_id": 1,
  "aluno_id": 42
}
```

---

#### **GET /analysis/{prova_id}/{aluno_id}**
Consulta resultado da análise

**Response (completed):**
```json
{
  "status": "completed",
  "prova_id": 1,
  "aluno_id": 42,
  "metrics": {
    "percentage_forward": 67.3,
    "percentage_left": 12.5,
    "percentage_right": 8.2,
    "percentage_up": 3.1,
    "percentage_down": 2.9,
    "percentage_no_face": 6.0,
    "position_changes_per_minute": 8.4,
    "total_position_changes": 126
  },
  "suspicious_periods": [
    {
      "start": 120.5,
      "end": 145.2,
      "duration": 24.7,
      "direction": "Looking Right"
    }
  ],
  "completed_at": "2026-02-11T22:45:30"
}
```

**Response (processing):**
```json
{
  "status": "processing",
  "message": "Analysis in progress",
  "progress": 47.3
}
```

---

## Métricas Geradas

### 1. Percentual de Tempo por Direção
- **percentage_forward**: % olhando para frente (normal)
- **percentage_left**: % olhando para esquerda
- **percentage_right**: % olhando para direita
- **percentage_up**: % olhando para cima
- **percentage_down**: % olhando para baixo
- **percentage_no_face**: % sem rosto detectado

### 2. Métricas de Distração
- **position_changes_per_minute**: Trocas de posição por minuto
- **total_position_changes**: Total de trocas durante prova

### 3. Períodos Suspeitos
Períodos > 10 segundos olhando para direções não-frontais

```json
{
  "start": 120.5, // Segundo em que começou
  "end": 145.2, // Segundo em que terminou
  "duration": 24.7, // Duração em segundos
  "direction": "Looking Right"
}
```

---

## Configuração

### Variáveis de Ambiente

```bash
# Serviço
ANALYSIS_SERVICE_HOST=0.0.0.0
ANALYSIS_SERVICE_PORT=8002

# Database (compartilhado)
DATABASE_URL=sqlite:////app/data/escola.db

# Storage
RECORDINGS_DIR=/app/recordings

# Processing
MAX_CONCURRENT_ANALYSIS=10 # Máx análises simultâneas
PROCESS_EVERY_N_FRAMES=5 # Processar 1 a cada N frames
USE_GPU=false # Usar GPU (MediaPipe)

# Firebase (JWT)
FIREBASE_PROJECT_ID=your-project-id
```

---

## Tecnologias

- **FastAPI** - Web framework
- **MediaPipe** - Face mesh detection
- **OpenCV** - Video processing
- **SQLAlchemy** - Database ORM
- **Firebase Admin** - JWT validation

---

## Performance

### Tempo de Processamento

| Duração do Vídeo | Frames Processados | Tempo Estimado |
|------------------|-------------------|----------------|
| 30 min | ~360 frames | ~5 min |
| 1 hora | ~720 frames | ~10 min |
| 2 horas | ~1440 frames | ~20 min |

**Nota:** Processa 1 frame a cada 5 frames (6 FPS) para otimização

### Otimizações Possíveis

1. **Processar menos frames**
   ```python
   PROCESS_EVERY_N_FRAMES=10 # 3 FPS ao invés de 6 FPS
   ```
   → 50% mais rápido

2. **Usar GPU**
   ```python
   USE_GPU=true
   ```
   → 3x mais rápido (requer CUDA)

3. **Reduzir resolução**
   → Implementar resize para 640x480

---

## Escalabilidade

### Múltiplos Containers (Horizontal Scaling)

```yaml
# docker-compose.yml
services:
  analysis-service-1:
    build: ./back/analysis-service
    ports: ["8002:8002"]

  analysis-service-2:
    build: ./back/analysis-service
    ports: ["8003:8002"]

  analysis-service-3:
    build: ./back/analysis-service
    ports: ["8004:8002"]
```

**Com load balancer:**
- NGINX distribui requests entre instâncias
- Cada container processa análises independentemente

---

## Segurança

### JWT Validation

Todos os endpoints validam:
- Token válido (Firebase)
- User type = "professor"
- Ownership da prova (simplificado)

### Validação de Prova Finalizada

```python
# Análise só permitida após prova terminar
if data_fim > now:
    raise HTTPException(400, "Exam still in progress")
```

---

## Futuro: Mais Serviços de Análise

Este é um **serviço modular**. Você pode adicionar outros:

### Exemplo: Audio Analysis Service (porta 8003)

```yaml
# docker-compose.yml
audio-analysis-service:
  build: ./back/audio-analysis-service
  ports: ["8003:8003"]
  environment:
    - ANALYSIS_TYPE=audio
```

### Exemplo: Code Analysis Service (porta 8004)

```yaml
code-analysis-service:
  build: ./back/code-analysis-service
  ports: ["8004:8004"]
  environment:
    - ANALYSIS_TYPE=code_similarity
```

---

## Fluxo Completo

### 1. Professor Solicita Análise

```typescript
// Frontend
const response = await axios.post(
  `http://localhost:8002/analyze/${provaId}/${alunoId}`,
  {},
  { headers: { Authorization: `Bearer ${token}` } }
);
```

### 2. Serviço Processa em Background

```
Frame 100/1000 (10%) → Salva no DB
Frame 500/1000 (50%) → Salva no DB
Frame 1000/1000 (100%) → Análise completa
```

### 3. Professor Consulta Resultado

```typescript
const result = await axios.get(
  `http://localhost:8002/analysis/${provaId}/${alunoId}`,
  { headers: { Authorization: `Bearer ${token}` } }
);

if (result.data.status === "completed") {
  console.log(result.data.metrics);
}
```

---

## Troubleshooting

### Erro: "Video not found"
- Verifique se o vídeo existe em `/app/recordings/`
- Formato esperado: `prova_{prova_id}_aluno_{aluno_id}.webm`

### Erro: "Exam still in progress"
- Análise só permitida após `data_fim < now`
- Aguarde o término da prova

### Análise lenta
- Ajuste `PROCESS_EVERY_N_FRAMES=10` (processar menos frames)
- Use `USE_GPU=true` se disponível

---

## Referências

- [MediaPipe Face Mesh](https://google.github.io/mediapipe/solutions/face_mesh.html)
- [OpenCV solvePnP](https://docs.opencv.org/master/d9/d0c/group__calib3d.html#ga549c2075fac14829ff4a58bc931c033d)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)

---

## Para TCC

**Este serviço foi projetado para ser:**
1. Simples de entender
2. Modular (fácil adicionar mais análises)
3. Escalável (múltiplos containers)
4. Seguro (JWT em todos endpoints)

**Ideal para demonstrar:**
- Arquitetura de microserviços
- Processamento assíncrono
- Análise de vídeo com IA
- Escalabilidade horizontal
