#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# Run All Services Locally - Test Maker Platform
# ═══════════════════════════════════════════════════════════════════════════════
#
# Este script inicia TODOS os 8 microserviços do Test Maker Platform:
# 1. Main API (porta 8000)
# 2. Recording Service (porta 8001) - Screen recording
# 3. Analysis Service (porta 8002) - Gaze tracking (MediaPipe)
# 4. Webcam Service (porta 8003) - Webcam capture
# 5. Audio Service (porta 8004) - Audio capture + speaker diarization
# 6. Keystroke Service (porta 8005) - Keystroke dynamics analysis
# 7. Similarity Service (porta 8006) - Code similarity/plagiarism detection
# 8. Frontend (porta 5173) - React app (Vite dev server)
#
# Uso:
# ./run-all-services.sh # Rodar todos os serviços
# ./run-all-services.sh --test # Rodar todos os testes
# ./run-all-services.sh --help # Mostrar ajuda
#
# ═══════════════════════════════════════════════════════════════════════════════

set -e # Exit on error

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Python: prefer venv, fallback to system python3
if [ -f "$BASE_DIR/back/.venv/bin/python" ]; then
    PYTHON="$BASE_DIR/back/.venv/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON="python3"
else
    echo "Python 3 não encontrado! Crie o venv: cd back && python3 -m venv .venv && pip install -r requirements.txt"
    exit 1
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║ Test Maker Platform - Complete Local Setup ║${NC}"
    echo -e "${BLUE}║ 7 Microservices + Frontend ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_help() {
    echo "Uso: ./run-all-services.sh [OPTIONS]"
    echo ""
    echo "Opções:"
    echo " --help Mostrar esta mensagem de ajuda"
    echo " --docker Usar Docker Compose (todos os serviços em containers)"
    echo " --local Rodar serviços localmente + PostgreSQL em container"
    echo " (requer Python 3.10+, Node 18+, Docker)"
    echo " Será perguntado sobre limpar/popular o banco de dados"
    echo " --test Rodar todos os testes (166 tests)"
    echo " --stop Parar todos os serviços"
    echo " --status Ver status de todos os serviços"
    echo " --logs Ver logs de todos os serviços"
    echo ""
    echo "Serviços iniciados:"
    echo " 1. Main API :8000"
    echo " 2. Recording Service :8001"
    echo " 3. Analysis Service :8002"
    echo " 4. Webcam Service :8003"
    echo " 5. Audio Service :8004"
    echo " 6. Keystroke Service :8005"
    echo " 7. Similarity Service :8006"
    echo " 8. Frontend :5173"
    echo " + PostgreSQL (container) :5432"
    echo ""
    echo "Gerenciamento de Banco de Dados:"
    echo " ./manage-db.sh start # Iniciar PostgreSQL"
    echo " ./manage-db.sh stop # Parar PostgreSQL"
    echo " ./manage-db.sh reset # Limpar e popular banco"
    echo " ./manage-db.sh status # Ver status do banco"
    echo ""
    echo "Python: $PYTHON"
    echo ""
}

check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0 # Port is in use
    else
        return 1 # Port is free
    fi
}

kill_port() {
    local port=$1
    local name=$2
    if check_port $port; then
        echo -e "${YELLOW} Limpando porta $port ($name)...${NC}"
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

create_directories() {
    echo -e "${CYAN} Criando diretórios necessários...${NC}"
    mkdir -p "$BASE_DIR/back/logs"
    mkdir -p "$BASE_DIR/back/data"
    mkdir -p "$BASE_DIR/back/recordings"
    mkdir -p "$BASE_DIR/back/webcam_recordings"
    mkdir -p "$BASE_DIR/back/audio_recordings"
    echo -e "${GREEN} Diretórios criados${NC}"
    echo ""
}

load_env() {
    # Load .env from back/ (where Firebase service account key is configured)
    if [ -f "$BASE_DIR/back/.env" ]; then
        echo -e "${CYAN} Carregando variáveis de ambiente de back/.env...${NC}"
        export $(cat "$BASE_DIR/back/.env" | grep -v '^#' | grep -v '^\s*$' | xargs)
        # Set FIREBASE_SERVICE_ACCOUNT with absolute path for all microservices
        # Main API uses FIREBASE_SERVICE_ACCOUNT_PATH (relative), microservices use FIREBASE_SERVICE_ACCOUNT (absolute)
        if [ -n "$FIREBASE_SERVICE_ACCOUNT_PATH" ]; then
            # Convert relative path to absolute (so it works from any service directory)
            export FIREBASE_SERVICE_ACCOUNT_PATH="$BASE_DIR/back/$FIREBASE_SERVICE_ACCOUNT_PATH"
            export FIREBASE_SERVICE_ACCOUNT="$FIREBASE_SERVICE_ACCOUNT_PATH"
            echo -e "${GREEN} Variáveis carregadas (back/.env)${NC}"
            echo -e " ${CYAN}Firebase: $FIREBASE_SERVICE_ACCOUNT_PATH${NC}"
        else
            echo -e "${GREEN} Variáveis carregadas (back/.env)${NC}"
        fi
    else
        echo -e "${YELLOW} Arquivo back/.env não encontrado!${NC}"
        echo -e "${YELLOW} Crie back/.env com FIREBASE_SERVICE_ACCOUNT_PATH=./serviceAccountKey.json${NC}"
    fi
    if [ -f "$BASE_DIR/front/.env" ]; then
        echo -e "${CYAN} Carregando variáveis de ambiente de front/.env...${NC}"
        export $(cat "$BASE_DIR/front/.env" | grep -v '^#' | grep -v '^\s*$' | xargs)
        echo -e "${GREEN} Variáveis carregadas (front/.env)${NC}"
    fi
    echo ""
}

check_dependencies() {
    echo -e "${CYAN} Verificando dependências...${NC}"

    PYTHON_VERSION=$($PYTHON --version | cut -d' ' -f2)
    echo -e "${GREEN} Python $PYTHON_VERSION ($PYTHON)${NC}"

    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        echo -e "${GREEN} Node $NODE_VERSION instalado${NC}"
    else
        echo -e "${RED} Node.js não encontrado!${NC}"
        exit 1
    fi

    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        echo -e "${GREEN} npm $NPM_VERSION instalado${NC}"
    else
        echo -e "${RED} npm não encontrado!${NC}"
        exit 1
    fi

    echo ""
}

run_docker() {
    echo -e "${PURPLE} Iniciando com Docker Compose...${NC}"
    echo ""

    if ! command -v docker compose &> /dev/null && ! command -v docker &> /dev/null; then
        echo -e "${RED} Docker ou Docker Compose não encontrado!${NC}"
        echo "Instale Docker Desktop ou Docker Engine + Docker Compose"
        exit 1
    fi

    echo -e "${CYAN} Building and starting all containers...${NC}"
    cd "$BASE_DIR"
    docker compose up --build
}

start_python_service() {
    # Usage: start_python_service "Name" port "directory" "command" step
    local name="$1"
    local port="$2"
    local dir="$3"
    local cmd="$4"
    local step="$5"
    local logfile="$BASE_DIR/back/logs/$(echo "$name" | tr ' ' '-' | tr '[:upper:]' '[:lower:]').log"
    local pidname="$(echo "$name" | tr ' ' '-' | tr '[:upper:]' '[:lower:]')"

    echo -e "${BLUE}[$step] $name (porta $port)${NC}"

    local svc_python="$PYTHON"
    if [ -f "$dir/.venv/bin/python" ]; then
        svc_python="$dir/.venv/bin/python"
        echo -e " ${CYAN}Usando venv: $dir/.venv${NC}"
    elif [ -f "$dir/venv/bin/python" ]; then
        svc_python="$dir/venv/bin/python"
        echo -e " ${CYAN}Usando venv: $dir/venv${NC}"
    elif [ -f "$dir/env/bin/python" ]; then
        svc_python="$dir/env/bin/python"
        echo -e " ${CYAN}Usando venv: $dir/env${NC}"
    fi

    cd "$dir"
    $svc_python $cmd > "$logfile" 2>&1 &
    local pid=$!
    echo $pid > "$BASE_DIR/back/.$pidname.pid"

    # Wait a moment and check if process is still alive
    sleep 2
    if ps -p $pid > /dev/null 2>&1; then
        echo -e "${GREEN} PID: $pid${NC}"
    else
        echo -e "${RED} Falhou ao iniciar! Verifique: tail $logfile${NC}"
        # Show last 3 lines of log for quick diagnosis
        tail -3 "$logfile" 2>/dev/null | sed 's/^/ /'
    fi
}

run_local() {
    print_header
    check_dependencies
    create_directories
    load_env

    echo -e "${BLUE} Configurando PostgreSQL Database (container)...${NC}"

    if docker ps | grep -q testmaker-db; then
        echo -e "${GREEN} PostgreSQL container já está rodando${NC}"
    else
        echo -e "${YELLOW} Iniciando PostgreSQL container...${NC}"
        "$BASE_DIR/manage-db.sh" start
    fi

    export DATABASE_URL="postgresql://testmaker:testmaker123@localhost:5432/testmaker"
    echo -e "${CYAN} DATABASE_URL=$DATABASE_URL${NC}"
    echo ""

    if [ "$NO_DB_PROMPT" != "true" ]; then
        echo -e "${YELLOW}═════════════════════════════════════════════════════${NC}"
        echo -e "${YELLOW} Configuração do Banco de Dados${NC}"
        echo -e "${YELLOW}═════════════════════════════════════════════════════${NC}"
        echo ""
        echo -e "${CYAN}Deseja limpar e popular o banco de dados?${NC}"
        echo -e " ${GREEN}1)${NC} Sim - Limpar banco e popular com dados de teste (RECOMENDADO para fresh install)"
        echo -e " ${GREEN}2)${NC} Não - Manter banco de dados como está"
        echo ""
        read -p "Escolha [1/2] (padrão: 1): " db_choice
        db_choice=${db_choice:-1}

        if [ "$db_choice" == "1" ]; then
            echo ""
            echo -e "${YELLOW} Limpando e populando banco de dados...${NC}"
            "$BASE_DIR/manage-db.sh" reset
            echo ""
        else
            echo -e "${BLUE} ℹ Mantendo banco de dados existente${NC}"
            echo ""
        fi
    fi

    echo -e "${YELLOW} Limpando portas...${NC}"
    kill_port 8000 "Main API"
    kill_port 8001 "Recording Service"
    kill_port 8002 "Analysis Service"
    kill_port 8003 "Webcam Service"
    kill_port 8004 "Audio Service"
    kill_port 8005 "Keystroke Service"
    kill_port 8006 "Similarity Service"
    kill_port 5173 "Frontend"
    echo ""

    echo -e "${CYAN} Iniciando serviços...${NC}"
    echo ""

    start_python_service "main-api" 8000 "$BASE_DIR/back" "-m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" "1/8"
    start_python_service "recording-service" 8001 "$BASE_DIR/back/recording-service" "main.py" "2/8"
    start_python_service "analysis-service" 8002 "$BASE_DIR/back/analysis-service" "-m uvicorn main:app --host 0.0.0.0 --port 8002 --reload" "3/8"
    start_python_service "webcam-service" 8003 "$BASE_DIR/back/webcam-service" "main.py" "4/8"
    start_python_service "audio-service" 8004 "$BASE_DIR/back/audio-service" "main.py" "5/8"
    start_python_service "keystroke-service" 8005 "$BASE_DIR/back/keystroke-service" "main.py" "6/8"
    start_python_service "similarity-service" 8006 "$BASE_DIR/back/similarity-service" "main.py" "7/8"

    echo -e "${BLUE}[8/8] Frontend (porta 5173)${NC}"
    cd "$BASE_DIR/front"
    npm run dev > "$BASE_DIR/back/logs/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$BASE_DIR/back/.frontend.pid"
    sleep 3
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${GREEN} PID: $FRONTEND_PID${NC}"
    else
        echo -e "${RED} Falhou ao iniciar! Verifique: tail back/logs/frontend.log${NC}"
    fi

    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║ Todos os serviços foram iniciados com sucesso! ║${NC}"
    echo -e "${GREEN}╠══════════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║ URLs dos serviços: ║${NC}"
    echo -e "${GREEN}║ ║${NC}"
    echo -e "${GREEN}║ Frontend: http://localhost:5173 ║${NC}"
    echo -e "${GREEN}║ Main API: http://localhost:8000 ║${NC}"
    echo -e "${GREEN}║ API Docs: http://localhost:8000/docs ║${NC}"
    echo -e "${GREEN}║ Recording Service: http://localhost:8001 ║${NC}"
    echo -e "${GREEN}║ Analysis Service: http://localhost:8002 ║${NC}"
    echo -e "${GREEN}║ Webcam Service: http://localhost:8003 ║${NC}"
    echo -e "${GREEN}║ Audio Service: http://localhost:8004 ║${NC}"
    echo -e "${GREEN}║ ⌨ Keystroke Service: http://localhost:8005 ║${NC}"
    echo -e "${GREEN}║ Similarity Service: http://localhost:8006 ║${NC}"
    echo -e "${GREEN}║ ║${NC}"
    echo -e "${GREEN}║ PostgreSQL: postgresql://localhost:5432/testmaker ║${NC}"
    echo -e "${GREEN}╠══════════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║ Logs: ║${NC}"
    echo -e "${GREEN}║ tail -f back/logs/main-api.log ║${NC}"
    echo -e "${GREEN}║ tail -f back/logs/recording-service.log ║${NC}"
    echo -e "${GREEN}║ tail -f back/logs/analysis-service.log ║${NC}"
    echo -e "${GREEN}║ tail -f back/logs/webcam-service.log ║${NC}"
    echo -e "${GREEN}║ tail -f back/logs/audio-service.log ║${NC}"
    echo -e "${GREEN}║ tail -f back/logs/keystroke-service.log ║${NC}"
    echo -e "${GREEN}║ tail -f back/logs/similarity-service.log ║${NC}"
    echo -e "${GREEN}║ tail -f back/logs/frontend.log ║${NC}"
    echo -e "${GREEN}╠══════════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║ Para parar: ./run-all-services.sh --stop ║${NC}"
    echo -e "${GREEN}║ Gerenciar DB: ./manage-db.sh [start|stop|reset|status] ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    echo -e "${CYAN} PIDs salvos em back/.*.pid${NC}"
    echo -e "${CYAN} Python: $PYTHON${NC}"
    echo ""
    echo -e "${YELLOW}Pressione Ctrl+C para ver os logs (serviços continuarão rodando)${NC}"
    echo ""

    trap "echo ''; echo -e '${YELLOW}Serviços rodando em background. Use ./run-all-services.sh --stop para parar.${NC}'; exit 0" INT

    tail -f "$BASE_DIR/back/logs/"*.log
}

stop_services() {
    echo -e "${YELLOW} Parando todos os serviços...${NC}"
    echo ""

    for pidfile in "$BASE_DIR/back"/.*pid; do
        if [ -f "$pidfile" ]; then
            PID=$(cat "$pidfile")
            SERVICE=$(basename "$pidfile" .pid | sed 's/^\.//')

            if ps -p $PID > /dev/null 2>&1; then
                echo -e "${CYAN}Parando $SERVICE (PID $PID)...${NC}"
                kill $PID 2>/dev/null || true
                rm "$pidfile"
            else
                echo -e "${YELLOW}$SERVICE já estava parado${NC}"
                rm "$pidfile"
            fi
        fi
    done

    echo ""
    echo -e "${CYAN}Limpando portas...${NC}"
    kill_port 8000 "Main API"
    kill_port 8001 "Recording"
    kill_port 8002 "Analysis"
    kill_port 8003 "Webcam"
    kill_port 8004 "Audio"
    kill_port 8005 "Keystroke"
    kill_port 8006 "Similarity"
    kill_port 5173 "Frontend"

    echo ""
    echo -e "${GREEN} Todos os serviços foram parados!${NC}"
    echo ""
    echo -e "${CYAN} PostgreSQL container ainda está rodando.${NC}"
    echo -e "${CYAN} Para parar: ./manage-db.sh stop${NC}"
    echo -e "${CYAN} Para limpar e popular: ./manage-db.sh reset${NC}"
}

check_status() {
    echo -e "${CYAN} Status dos serviços:${NC}"
    echo ""

    services=(
        "8000:Main API"
        "8001:Recording Service"
        "8002:Analysis Service"
        "8003:Webcam Service"
        "8004:Audio Service"
        "8005:Keystroke Service"
        "8006:Similarity Service"
        "5173:Frontend"
    )

    for service in "${services[@]}"; do
        PORT="${service%%:*}"
        NAME="${service##*:}"

        if check_port $PORT; then
            PID=$(lsof -ti:$PORT 2>/dev/null)
            echo -e "${GREEN} $NAME (:$PORT) - Running (PID: $PID)${NC}"
        else
            echo -e "${RED} $NAME (:$PORT) - Not running${NC}"
        fi
    done

    echo ""
}

if [ "$1" == "--help" ]; then
    print_help
    exit 0
elif [ "$1" == "--docker" ]; then
    run_docker
    exit 0
elif [ "$1" == "--local" ]; then
    read -p "Deseja apagar o banco de dados existente para recomeçar? (s/N): " del_choice
    if [[ "$del_choice" == "s" || "$del_choice" == "S" ]]; then
        export NO_DB_DELETE="false"
        read -p "Deseja popular o banco de dados com dados de teste (seed)? (S/n): " seed_choice
        if [[ "$seed_choice" != "n" && "$seed_choice" != "N" ]]; then
            echo -e "${CYAN} Populando o banco de dados...${NC}"
            cd "$BASE_DIR/back"
            $PYTHON seed_db.py
            echo -e "${GREEN} Banco de dados populado com sucesso!${NC}"
        fi
    else
        export NO_DB_DELETE="true"
    fi
    run_local
    exit 0
elif [ "$1" == "--test" ]; then
    "$BASE_DIR/run-all-tests.sh" "${@:2}"
    exit $?
elif [ "$1" == "--stop" ]; then
    stop_services
    exit 0
elif [ "$1" == "--status" ]; then
    check_status
    exit 0
elif [ "$1" == "--logs" ]; then
    tail -f "$BASE_DIR/back/logs/"*.log
    exit 0
elif [ -z "$1" ]; then
    echo -e "${CYAN}Como você quer rodar o sistema?${NC}"
    echo ""
    echo "1) Docker Compose (recomendado)"
    echo "2) Localmente (Python + Node)"
    echo "3) Rodar todos os testes"
    echo "4) Verificar status"
    echo "5) Parar serviços"
    echo ""
    read -p "Escolha uma opção (1-5): " choice

    case $choice in
        1)
            run_docker
            ;;
        2)
            read -p "Deseja apagar o banco de dados existente para recomeçar? (s/N): " del_choice
            if [[ "$del_choice" == "s" || "$del_choice" == "S" ]]; then
                export NO_DB_DELETE="false"
                read -p "Deseja popular o banco de dados com dados de teste (seed)? (S/n): " seed_choice
                if [[ "$seed_choice" != "n" && "$seed_choice" != "N" ]]; then
                    echo -e "${CYAN} Populando o banco de dados...${NC}"
                    cd "$BASE_DIR/back"
                    $PYTHON seed_db.py
                    echo -e "${GREEN} Banco de dados populado com sucesso!${NC}"
                fi
            else
                export NO_DB_DELETE="true"
            fi
            run_local
            ;;
        3)
            "$BASE_DIR/run-all-tests.sh"
            ;;
        4)
            check_status
            ;;
        5)
            stop_services
            ;;
        *)
            echo -e "${RED}Opção inválida!${NC}"
            print_help
            exit 1
            ;;
    esac
else
    echo -e "${RED}Argumento inválido: $1${NC}"
    print_help
    exit 1
fi
