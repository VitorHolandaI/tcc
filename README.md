# ProctorLCC
(obs --> codigo desenvolvido no self-hosted gitea)

Plataforma de aplicacao de provas de programacao com monitoramento comportamental por IA.

Professores criam provas com questoes de codigo. Alunos resolvem diretamente no navegador, com um editor Monaco integrado. Durante a prova, o sistema captura tela, webcam e audio simultaneamente via WebSockets, e analisa o comportamento do aluno com modelos de machine learning.

---

## Arquitetura

O sistema e composto por 7 microservicos independentes, um frontend React e um banco de dados PostgreSQL.

| Servico | Porta | Descricao |
|---------|-------|-----------|
| main-api | 8000 | API principal: provas, questoes, submissoes, avaliacoes, autenticacao |
| recording-service | 8001 | Captura de tela via WebSocket, segmentacao de video |
| analysis-service | 8002 | Analise de direcao do olhar com MediaPipe |
| webcam-service | 8003 | Captura de webcam via WebSocket |
| audio-service | 8004 | Captura de audio e diarizacao de locutores com PyAnnote |
| keystroke-service | 8005 | Analise de dinamica de digitacao |
| similarity-service | 8006 | Deteccao de plagio entre submissoes de codigo |
| frontend | 3000 | Interface React com Monaco Editor |
| PostgreSQL | 5432 | Banco de dados relacional |

Todos os servicos sao autenticados via Firebase JWT. O frontend comunica com os servicos via Nginx como reverse proxy.

**Backend:** Python 3.10-3.12, FastAPI, SQLAlchemy, PostgreSQL
**Frontend:** React 19, TypeScript, Vite, Monaco Editor
**ML:** MediaPipe, PyAnnote, PyTorch, OpenCV
**Infraestrutura:** Docker, docker-compose, Nginx, Firebase Auth

---

## Execucao rapida

### Docker (recomendado)

```bash
# Configurar credenciais
cp back/.env.example back/.env
# Editar back/.env com FIREBASE_PROJECT_ID, FIREBASE_SERVICE_ACCOUNT_PATH, HUGGINGFACE_TOKEN

# Subir todos os servicos
docker-compose up --build

# Acesso: http://localhost:3000
# API docs: http://localhost:8000/docs
```

### Desenvolvimento local

```bash
# Configurar e iniciar tudo de uma vez
./run-all-services.sh --local

# Outros comandos
./run-all-services.sh --stop    # Parar todos os servicos
./run-all-services.sh --status  # Ver status dos servicos
./run-all-services.sh --logs    # Ver logs
```

Para setup completo (instalacao de dependencias, ambientes virtuais, banco de dados), consulte [FRESH_INSTALL.md](FRESH_INSTALL.md).

---

## Banco de dados

```bash
./manage-db.sh start   # Iniciar container PostgreSQL
./manage-db.sh reset   # Limpar e reinicializar com dados de teste
./manage-db.sh status  # Ver status
```

Credenciais de desenvolvimento: `postgresql://testmaker:testmaker123@localhost:5432/testmaker`

---

## Testes

```bash
# Todos os testes (166 testes)
./run-all-tests.sh

# Backend apenas
./run-all-tests.sh --back

# Verboso
./run-all-tests.sh --verbose
```

---

## Documentacao

| Documento | Descricao |
|-----------|-----------|
| [FRESH_INSTALL.md](FRESH_INSTALL.md) | Instalacao em maquina nova, ambientes virtuais, configuracao |
| [docs/COMO_RODAR.md](docs/COMO_RODAR.md) | Guia detalhado de execucao e troubleshooting |
| [docs/SERVICES_ARCHITECTURE.md](docs/SERVICES_ARCHITECTURE.md) | Arquitetura completa, endpoints, fluxo de dados |
| [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md) | Guia de testes manuais e automatizados |
| [docs/VPS_DEPLOYMENT.md](docs/VPS_DEPLOYMENT.md) | Deploy em VPS com Docker e SSL |
| [docs/SECURITY_ANALYSIS.md](docs/SECURITY_ANALYSIS.md) | Analise de seguranca e vulnerabilidades identificadas |

---

## Variáveis de ambiente

Arquivo `back/.env`:

```env
FIREBASE_PROJECT_ID=seu-projeto
FIREBASE_SERVICE_ACCOUNT_PATH=./serviceAccountKey.json
HUGGINGFACE_TOKEN=seu-token    # Necessario para audio-service
DATABASE_URL=postgresql://testmaker:testmaker123@localhost:5432/testmaker
```

O arquivo `back/serviceAccountKey.json` deve conter as credenciais do Firebase Service Account.
