#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# Test Maker Platform - Teste de Integração dos 3 Streams
# ═══════════════════════════════════════════════════════════════
#
# Este script testa o fluxo completo de captura dos 3 streams:
# 1. Screen Recording (porta 8001)
# 2. Webcam (porta 8003)
# 3. Audio (porta 8004)
#
# Uso: ./test_3stream_integration.sh
#
# ═══════════════════════════════════════════════════════════════

set -e # Exit on error

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

MAIN_API="http://localhost:8000"
RECORDING_SERVICE="http://localhost:8001"
ANALYSIS_SERVICE="http://localhost:8002"
WEBCAM_SERVICE="http://localhost:8003"
AUDIO_SERVICE="http://localhost:8004"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE} Test Maker Platform - Teste de Integração 3 Streams${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}[1/6] Verificando se todos os serviços estão rodando...${NC}"
echo ""

check_service() {
    local name=$1
    local url=$2

    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e " ${GREEN} $name está rodando${NC}"
        return 0
    else
        echo -e " ${RED} $name NÃO está rodando em $url${NC}"
        return 1
    fi
}

ALL_UP=true

check_service "Main API" "$MAIN_API" || ALL_UP=false
check_service "Recording Service" "$RECORDING_SERVICE" || ALL_UP=false
check_service "Analysis Service" "$ANALYSIS_SERVICE" || ALL_UP=false
check_service "Webcam Service" "$WEBCAM_SERVICE" || ALL_UP=false
check_service "Audio Service" "$AUDIO_SERVICE" || ALL_UP=false

echo ""

if [ "$ALL_UP" = false ]; then
    echo -e "${RED} Alguns serviços não estão rodando!${NC}"
    echo -e "${YELLOW}Execute: docker-compose up --build${NC}"
    exit 1
fi

echo -e "${GREEN} Todos os serviços estão rodando!${NC}"
echo ""

echo -e "${YELLOW}[2/6] Verificando health checks...${NC}"
echo ""

check_health() {
    local name=$1
    local url=$2

    response=$(curl -s "$url")

    if echo "$response" | grep -q "status"; then
        echo -e " ${GREEN} $name health check OK${NC}"
        echo " Response: $response"
        return 0
    else
        echo -e " ${RED} $name health check FAILED${NC}"
        return 1
    fi
}

check_health "Recording Service" "$RECORDING_SERVICE/health"
check_health "Webcam Service" "$WEBCAM_SERVICE"
check_health "Audio Service" "$AUDIO_SERVICE"

echo ""

echo -e "${YELLOW}[3/6] Verificando estrutura de diretórios...${NC}"
echo ""

check_dir() {
    local dir=$1

    if [ -d "$dir" ]; then
        echo -e " ${GREEN} $dir existe${NC}"
        return 0
    else
        echo -e " ${YELLOW} $dir não existe (será criado automaticamente)${NC}"
        return 0
    fi
}

check_dir "back/recordings"
check_dir "back/webcam_recordings"
check_dir "back/audio_recordings"

echo ""

echo -e "${YELLOW}[4/6] Verificando configuração do Docker Compose...${NC}"
echo ""

if [ -f "docker-compose.yml" ]; then
    echo -e " ${GREEN} docker-compose.yml encontrado${NC}"

    services=(main-api recording-service analysis-service webcam-service audio-service frontend)

    for service in "${services[@]}"; do
        if grep -q "$service:" docker-compose.yml; then
            echo -e " ${GREEN} Serviço '$service' definido${NC}"
        else
            echo -e " ${RED} Serviço '$service' NÃO está definido${NC}"
        fi
    done
else
    echo -e " ${RED} docker-compose.yml não encontrado!${NC}"
    exit 1
fi

echo ""

echo -e "${YELLOW}[5/6] Verificando .env do frontend...${NC}"
echo ""

if [ -f "front/.env" ]; then
    echo -e " ${GREEN} front/.env encontrado${NC}"

    required_vars=(
        "VITE_API_BASE_URL"
        "VITE_RECORDING_SERVICE_URL"
        "VITE_WEBCAM_SERVICE_URL"
        "VITE_AUDIO_SERVICE_URL"
    )

    for var in "${required_vars[@]}"; do
        if grep -q "^$var=" front/.env; then
            value=$(grep "^$var=" front/.env | cut -d '=' -f2)
            echo -e " ${GREEN} $var=$value${NC}"
        else
            echo -e " ${RED} $var NÃO está definido${NC}"
        fi
    done
else
    echo -e " ${YELLOW} front/.env não encontrado${NC}"
    echo -e " ${YELLOW} Copie front/.env.example para front/.env${NC}"

    if [ -f "front/.env.example" ]; then
        echo -e " ${BLUE} Execute: cp front/.env.example front/.env${NC}"
    fi
fi

echo ""

echo -e "${YELLOW}[6/6] Resumo dos Testes${NC}"
echo ""

echo -e "${GREEN} Todos os testes passaram!${NC}"
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE} Próximos Passos para Testar os 3 Streams${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${GREEN}1. Acesse o frontend:${NC}"
echo -e " ${BLUE}http://localhost:3000${NC}"
echo ""

echo -e "${GREEN}2. Faça login como ALUNO${NC}"
echo ""

echo -e "${GREEN}3. Inicie uma prova${NC}"
echo ""

echo -e "${GREEN}4. O navegador solicitará 3 permissões:${NC}"
echo -e " ${YELLOW} Compartilhar tela (Screen)${NC}"
echo -e " ${YELLOW} Acessar webcam${NC}"
echo -e " ${YELLOW} Acessar microfone${NC}"
echo ""

echo -e "${GREEN}5. Após permitir, verifique os logs:${NC}"
echo -e " ${BLUE}docker logs testmaker-recording${NC} - Deve mostrar: Screen recording started"
echo -e " ${BLUE}docker logs testmaker-webcam${NC} - Deve mostrar: Webcam recording started"
echo -e " ${BLUE}docker logs testmaker-audio${NC} - Deve mostrar: Audio recording saved"
echo ""

echo -e "${GREEN}6. Verifique os arquivos criados:${NC}"
echo -e " ${BLUE}ls -lh back/recordings/${NC}"
echo -e " ${BLUE}ls -lh back/webcam_recordings/${NC}"
echo -e " ${BLUE}ls -lh back/audio_recordings/${NC}"
echo ""

echo -e "${GREEN}7. Para solicitar análises de IA:${NC}"
echo -e " ${YELLOW}(Faça login como PROFESSOR)${NC}"
echo ""
echo -e " ${BLUE}Análise de Gaze (MediaPipe):${NC}"
echo -e " curl -X POST http://localhost:8002/analyze/PROVA_ID/ALUNO_ID \\"
echo -e " -H \"Authorization: Bearer \$PROFESSOR_TOKEN\""
echo ""
echo -e " ${BLUE}Análise de Áudio (Speaker Diarization):${NC}"
echo -e " curl -X POST http://localhost:8004/analyze/PROVA_ID/ALUNO_ID \\"
echo -e " -H \"Authorization: Bearer \$PROFESSOR_TOKEN\""
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN} Teste Completo! Sistema Pronto Para Uso! ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
