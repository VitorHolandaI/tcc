#!/bin/bash

# Script para executar os testes da Escola API

echo "================================"
echo " Escola API - Executar Testes"
echo "================================"
echo ""

echo "1. Ativando ambiente virtual..."
source ./env/bin/activate
rm school.db

if [ $? -ne 0 ]; then
    echo " Erro ao ativar ambiente virtual!"
    echo "Certifique-se de que o ambiente virtual está em ../env/"
    exit 1
fi

echo " Ambiente virtual ativado"
echo ""

echo "2. Verificando dependências de teste..."
python -c "import pytest, httpx" 2>/dev/null

if [ $? -ne 0 ]; then
    echo " Dependências de teste faltando. Instalando..."
    pip install pytest httpx
    echo " Dependências instaladas"
else
    echo " Dependências de teste instaladas"
fi

echo ""

if [ $# -eq 0 ]; then
    echo "3. Executando TODOS os testes..."
    echo ""
    python -m pytest tests/ -v
else
    echo "3. Executando teste: $1"
    echo ""
    python -m pytest "tests/$1" -v
fi

echo ""

if [ $? -eq 0 ]; then
    echo " Todos os testes passaram!"
else
    echo " Alguns testes falharam. Verifique os erros acima."
    exit 1
fi
