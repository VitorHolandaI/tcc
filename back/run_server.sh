#!/bin/bash

# Script para iniciar o servidor da Escola API

echo "================================"
echo " Escola API - Test Maker"
echo "================================"
echo ""

echo "1. Ativando ambiente virtual..."
source ./env/bin/activate

if [ $? -ne 0 ]; then
    echo " Erro ao ativar ambiente virtual!"
    echo "Certifique-se de que o ambiente virtual está em ../env/"
    exit 1
fi

echo " Ambiente virtual ativado"
echo ""

echo "2. Verificando dependências..."
python -c "import fastapi, uvicorn, sqlalchemy, pydantic" 2>/dev/null

if [ $? -ne 0 ]; then
    echo " Algumas dependências estão faltando. Instalando..."
    pip install -r requirements.txt
    echo " Dependências instaladas"
else
    echo " Todas as dependências estão instaladas"
fi

echo ""

echo "3. Iniciando servidor..."
echo ""
echo " Servidor disponível em: http://localhost:8000"
echo " Documentação: http://localhost:8000/docs"
echo ""
echo "Pressione Ctrl+C para parar o servidor"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000