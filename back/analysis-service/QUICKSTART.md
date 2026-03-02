# Analysis Service - Quick Start Guide

**5 minutos para começar a usar o serviço de análise de vídeos**

---

## Start Rápido

### 1. Iniciar o Serviço

```bash
# Opção A: Via Docker Compose (recomendado)
cd /home/vitor/git/tcc
docker-compose up analysis-service

# Opção B: Standalone (desenvolvimento)
cd back/analysis-service
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

### 2. Verificar se está funcionando

```bash
curl http://localhost:8002/

# Response esperado:
# {
# "service": "Analysis Service",
# "status": "running",
# "version": "1.0.0"
# }
```

---

## Fluxo Básico de Uso

### **Cenário:** Professor quer analisar gravação de um aluno

#### Passo 1: Obter JWT Token
```typescript
// Frontend
const token = await firebase.auth().currentUser.getIdToken();
```

#### Passo 2: Iniciar Análise
```bash
curl -X POST http://localhost:8002/analyze/1/42 \
  -H "Authorization: Bearer <SEU_JWT_TOKEN>"

# Response:
{
  "message": "Analysis started in background",
  "status": "processing",
  "prova_id": 1,
  "aluno_id": 42
}
```

#### Passo 3: Consultar Progresso
```bash
curl http://localhost:8002/analysis/1/42 \
  -H "Authorization: Bearer <SEU_JWT_TOKEN>"

# Durante processamento:
{
  "status": "processing",
  "message": "Analysis in progress",
  "progress": 47.3
}

# Quando completo:
{
  "status": "completed",
  "metrics": {
    "percentage_forward": 67.3,
    "percentage_left": 12.5,
    "position_changes_per_minute": 8.4
  }
}
```

---

## Teste Completo (Passo a Passo)

### 1. Preparar Ambiente

```bash
# Certifique-se que existe um vídeo de teste
ls back/recordings/prova_1_aluno_42.webm

# Se não existir, copie um vídeo de teste:
cp analise/gaze/test_video.webm back/recordings/prova_1_aluno_42.webm
```

### 2. Configurar Variáveis

```bash
# back/analysis-service/.env
DATABASE_URL=sqlite:////home/vitor/git/tcc/back/data/escola.db
RECORDINGS_DIR=/home/vitor/git/tcc/back/recordings
FIREBASE_PROJECT_ID=your-firebase-project
```

### 3. Iniciar Serviço

```bash
cd back/analysis-service
uvicorn main:app --port 8002 --reload
```

### 4. Obter Token de Teste

**Opção A: Via Frontend**
1. Faça login como professor no frontend
2. Abra DevTools Console
3. Execute: `firebase.auth().currentUser.getIdToken().then(console.log)`

**Opção B: Via Script Python**
```python
import firebase_admin
from firebase_admin import auth

firebase_admin.initialize_app()
token = auth.create_custom_token("professor_uid")
print(token)
```

### 5. Testar Endpoints

```bash
# Guardar token em variável
TOKEN="eyJhbGciOiJSUzI1NiIsIn..."

# Teste 1: Health check
curl http://localhost:8002/

# Teste 2: Iniciar análise
curl -X POST http://localhost:8002/analyze/1/42 \
  -H "Authorization: Bearer $TOKEN"

# Teste 3: Consultar resultado (aguarde alguns segundos)
curl http://localhost:8002/analysis/1/42 \
  -H "Authorization: Bearer $TOKEN"
```

---

## Integração no Frontend

### Exemplo: Botão "Gerar Análise"

```typescript
// DetalhesProva.tsx
const ANALYSIS_SERVICE_URL = import.meta.env.VITE_ANALYSIS_SERVICE_URL || 'http://localhost:8002';

const startAnalysis = async (alunoId: number) => {
  try {
    const token = await getIdToken();

    const response = await axios.post(
      `${ANALYSIS_SERVICE_URL}/analyze/${provaId}/${alunoId}`,
      {},
      { headers: { Authorization: `Bearer ${token}` } }
    );

    alert('Análise iniciada! Aguarde alguns minutos.');

    // Poll para verificar progresso
    const interval = setInterval(async () => {
      const result = await axios.get(
        `${ANALYSIS_SERVICE_URL}/analysis/${provaId}/${alunoId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (result.data.status === 'completed') {
        clearInterval(interval);
        console.log('Análise completa:', result.data.metrics);
      }
    }, 5000); // Verifica a cada 5 segundos

  } catch (err) {
    console.error('Erro ao iniciar análise:', err);
  }
};
```

### Exemplo: Mostrar Resultados

```typescript
interface AnalysisMetrics {
  percentage_forward: number;
  percentage_left: number;
  percentage_right: number;
  position_changes_per_minute: number;
}

const AnalysisResults = ({ metrics }: { metrics: AnalysisMetrics }) => (
  <div className="analysis-results">
    <h3>Análise de Gaze</h3>

    <div className="metric">
      <span>Olhando para frente:</span>
      <strong>{metrics.percentage_forward}%</strong>
    </div>

    <div className="metric">
      <span>Olhando para esquerda:</span>
      <strong>{metrics.percentage_left}%</strong>
    </div>

    <div className="metric">
      <span>Trocas por minuto:</span>
      <strong>{metrics.position_changes_per_minute}</strong>
    </div>
  </div>
);
```

---

## Troubleshooting

### Erro: "Video not found"

**Causa:** Arquivo de vídeo não existe no diretório esperado

**Solução:**
```bash
# Verificar se vídeo existe
ls back/recordings/prova_{prova_id}_aluno_{aluno_id}.webm

# Copiar vídeo de teste se necessário
cp seu_video.webm back/recordings/prova_1_aluno_42.webm
```

### Erro: "Exam still in progress"

**Causa:** Prova ainda não terminou (validação de TCC)

**Solução:**
- Aguarde até `data_fim < now`
- Ou edite a prova no banco para `data_fim` no passado

```sql
-- SQLite
UPDATE provas SET data_fim = '2024-01-01T00:00:00Z' WHERE id = 1;
```

### Erro: "Invalid token"

**Causa:** JWT token inválido ou expirado

**Solução:**
- Gere novo token no frontend
- Verifique se `FIREBASE_PROJECT_ID` está correto

### Análise muito lenta

**Causa:** Processando muitos frames

**Solução:**
```bash
# Processar menos frames (mais rápido, menos preciso)
export PROCESS_EVERY_N_FRAMES=10 # Default: 5

# Reiniciar serviço
uvicorn main:app --port 8002 --reload
```

---

## Métricas Explicadas

### `percentage_forward`
**O que é:** % do tempo olhando para frente (tela)
**Esperado:** 60-80% (normal)
**Suspeito:** < 50%

### `percentage_left/right`
**O que é:** % olhando para os lados
**Esperado:** < 15% cada
**Suspeito:** > 20%

### `position_changes_per_minute`
**O que é:** Quantas vezes muda direção do olhar por minuto
**Esperado:** 5-10 (normal)
**Suspeito:** > 15 (muito distraído)

### `suspicious_periods`
**O que é:** Períodos > 10 segundos olhando para direções não-frontais
**Exemplo:**
```json
{
  "start": 120.5, // Segundo 120 (2min)
  "end": 145.2, // Segundo 145 (2min25s)
  "duration": 24.7, // 25 segundos
  "direction": "Looking Right"
}
```

---

## Configuração Avançada

### Otimizar Performance

```bash
# .env
PROCESS_EVERY_N_FRAMES=10 # Processar 1 a cada 10 frames (mais rápido)
USE_GPU=true # Usar GPU (requer CUDA)
MAX_CONCURRENT_ANALYSIS=5 # Máx 5 análises simultâneas
```

### Usar PostgreSQL ao invés de SQLite

```bash
# .env
DATABASE_URL=postgresql://user:pass@localhost:5432/testmaker
```

### Deploy em Produção

```yaml
# docker-compose.prod.yml
services:
  analysis-service:
    build: ./back/analysis-service
    environment:
      - DATABASE_URL=postgresql://prod-user:pass@db-host:5432/testmaker
      - RECORDINGS_DIR=/mnt/recordings
      - USE_GPU=true
    deploy:
      replicas: 3 # 3 instâncias
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

---

## Próximos Passos

1. **Testar localmente:**
   ```bash
   docker-compose up analysis-service
   ```

2. **Integrar no frontend:**
   - Adicionar botão "Gerar Análise"
   - Mostrar progresso com barra
   - Exibir métricas em cards

3. **Adicionar mais métricas:**
   - Detecção de múltiplas pessoas
   - Análise de iluminação
   - Detecção de objetos suspeitos

4. **Escalar:**
   - Múltiplos containers
   - Load balancer (NGINX)
   - Queue system (Celery + Redis)

---

## Comandos Úteis

```bash
# Ver logs em tempo real
docker-compose logs -f analysis-service

# Reiniciar serviço
docker-compose restart analysis-service

# Rebuild após mudanças
docker-compose up --build analysis-service

# Parar serviço
docker-compose stop analysis-service

# Ver containers rodando
docker ps | grep analysis

# Acessar shell do container
docker exec -it testmaker-analysis bash
```

---

## Checklist Rápido

- [ ] Serviço rodando em http://localhost:8002
- [ ] Health check retorna 200 OK
- [ ] JWT token válido configurado
- [ ] Vídeo de teste existe em recordings/
- [ ] Prova tem `data_fim` no passado
- [ ] Database acessível
- [ ] Endpoint POST /analyze funciona
- [ ] Endpoint GET /analysis retorna resultados

**Tudo checado? Você está pronto para usar o Analysis Service! **
