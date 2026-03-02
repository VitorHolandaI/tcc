#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# Run All Tests - Test Maker Platform
# ═══════════════════════════════════════════════════════════════════════════════
#
# Roda todos os testes do sistema:
# 1. Main API tests (back/tests/)
# 2. Keystroke Service tests (back/keystroke-service/)
# 3. Similarity Service tests (back/similarity-service/)
# 4. Frontend build check (front/)
#
# Uso:
#   ./run-all-tests.sh           # Rodar todos os testes
#   ./run-all-tests.sh --back    # Somente testes do backend
#   ./run-all-tests.sh --front   # Somente build check do frontend
#   ./run-all-tests.sh --verbose # Modo verbose (-v)
#
# ═══════════════════════════════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

TOTAL_PASSED=0
TOTAL_FAILED=0
FAILED_SUITES=()

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detect Python
detect_python() {
    if [ -f "$BASE_DIR/back/.venv/bin/python" ]; then
        PYTHON="$BASE_DIR/back/.venv/bin/python"
    elif command -v python3 &> /dev/null; then
        PYTHON="python3"
    elif command -v python &> /dev/null; then
        PYTHON="python"
    else
        echo -e "${RED}Python not found!${NC}"
        exit 1
    fi
    echo -e "${CYAN}Using Python: $PYTHON${NC}"
}

run_main_api_tests() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  [1/4] Main API Tests (back/tests/)                     ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"

    cd "$BASE_DIR/back"

    if $PYTHON -m pytest tests/ $VERBOSE_FLAG --tb=short 2>&1; then
        echo -e "${GREEN}Main API tests PASSED${NC}"
    else
        echo -e "${RED}Main API tests FAILED${NC}"
        FAILED_SUITES+=("Main API")
    fi
}

run_keystroke_tests() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  [2/4] Keystroke Service Tests                          ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"

    cd "$BASE_DIR/back/keystroke-service"

    if $PYTHON -m pytest test_main.py $VERBOSE_FLAG --tb=short 2>&1; then
        echo -e "${GREEN}Keystroke Service tests PASSED${NC}"
    else
        echo -e "${RED}Keystroke Service tests FAILED${NC}"
        FAILED_SUITES+=("Keystroke Service")
    fi
}

run_similarity_tests() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  [3/4] Similarity Service Tests                         ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"

    cd "$BASE_DIR/back/similarity-service"

    if $PYTHON -m pytest test_analyzer.py test_main.py $VERBOSE_FLAG --tb=short 2>&1; then
        echo -e "${GREEN}Similarity Service tests PASSED${NC}"
    else
        echo -e "${RED}Similarity Service tests FAILED${NC}"
        FAILED_SUITES+=("Similarity Service")
    fi
}

run_frontend_build() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  [4/4] Frontend Build Check (front/)                    ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"

    cd "$BASE_DIR/front"

    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing dependencies...${NC}"
        npm install --silent 2>&1
    fi

    if npm run build 2>&1; then
        echo -e "${GREEN}Frontend build PASSED${NC}"
    else
        echo -e "${RED}Frontend build FAILED${NC}"
        FAILED_SUITES+=("Frontend Build")
    fi
}

print_summary() {
    echo ""
    echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  TEST SUMMARY${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"

    if [ ${#FAILED_SUITES[@]} -eq 0 ]; then
        echo -e "${GREEN}"
        echo "  All test suites PASSED!"
        echo ""
        echo "  Test Suites:"
        echo "    Main API ............... PASSED"
        echo "    Keystroke Service ...... PASSED"
        echo "    Similarity Service ..... PASSED"
        echo "    Frontend Build ......... PASSED"
        echo -e "${NC}"
    else
        echo -e "${RED}"
        echo "  ${#FAILED_SUITES[@]} test suite(s) FAILED:"
        for suite in "${FAILED_SUITES[@]}"; do
            echo "    - $suite"
        done
        echo -e "${NC}"
    fi

    echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
    echo ""

    if [ ${#FAILED_SUITES[@]} -gt 0 ]; then
        exit 1
    fi
}

VERBOSE_FLAG=""
RUN_BACK=true
RUN_FRONT=true

for arg in "$@"; do
    case $arg in
        --verbose|-v)
            VERBOSE_FLAG="-v"
            ;;
        --back)
            RUN_FRONT=false
            ;;
        --front)
            RUN_BACK=false
            ;;
        --help)
            echo "Uso: ./run-all-tests.sh [OPTIONS]"
            echo ""
            echo "Opcoes:"
            echo "  --back       Somente testes do backend"
            echo "  --front      Somente build check do frontend"
            echo "  --verbose    Modo verbose (pytest -v)"
            echo "  --help       Mostrar esta mensagem"
            echo ""
            echo "Test suites (166 tests):"
            echo "  Main API (116 tests) - provas, questoes, submissoes, avaliacoes,"
            echo "                         professores, alunos, keystroke, integration,"
            echo "                         recording, monitoramento"
            echo "  Keystroke Service (11 tests) - endpoint mocks with Firebase auth"
            echo "  Similarity Service (39 tests) - analyzer + endpoint mocks"
            echo "  Frontend Build - TypeScript compilation check"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown argument: $arg${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Test Maker Platform - Test Runner                      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"

detect_python

if [ "$RUN_BACK" = true ]; then
    run_main_api_tests
    run_keystroke_tests
    run_similarity_tests
fi

if [ "$RUN_FRONT" = true ]; then
    run_frontend_build
fi

print_summary
