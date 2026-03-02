# Análise de Segurança - Sistema de Provas

**Data:** 2026-02-11
**Testado por:** Claude Code
**Tipo:** Pentest Educacional - Perspectiva de Aluno Malicioso

---

## Cenários de Ataque Testados

### **TESTE 1: Aluno tentando ver submissões de outros alunos**

**Endpoint:** `GET /submissoes/{questao_id}`
**Arquivo:** `back/app/controllers/submissao_controller.py:32-49`

**Tentativa de Ataque:**
```bash
# Aluno A tenta ver submissão do Aluno B para questao_id=5
GET /submissoes/5
Authorization: Bearer <token_aluno_A>
```

**Resultado:** **PROTEGIDO**
- Código sempre usa `aluno.id` do token JWT (linha 47)
- Retorna apenas submissão do próprio aluno
- Mesmo que o aluno tente IDs aleatórios, só vê suas próprias respostas

---

### **TESTE 2: Aluno tentando submeter para prova de outro aluno**

**Endpoint:** `POST /submissoes/`
**Arquivo:** `back/app/controllers/submissao_controller.py:51-120`

**Tentativa de Ataque:**
```json
POST /submissoes/
{
  "prova_id": 10,
  "questao_id": 25,
  "codigo_submetido": "print('código copiado')"
}
Authorization: Bearer <token_aluno_nao_autorizado>
```

**Resultado:** **PROTEGIDO**
- Validação de whitelist (linha 90-94)
- Erro 403: "Você não tem permissão para realizar esta prova"
- Aluno não consegue submeter se email não está em `emails_permitidos`

---

### **TESTE 3: Aluno tentando acessar prova antes do horário**

**Endpoint:** `POST /submissoes/`
**Arquivo:** `back/app/controllers/submissao_controller.py:96-108`

**Tentativa de Ataque:**
```json
POST /submissoes/
{
  "prova_id": 10,
  "questao_id": 25,
  "codigo_submetido": "print('early access')"
}
# Tentando submeter ANTES de data_aplicacao
```

**Resultado:** **PROTEGIDO**
- Validação temporal (linha 105-106)
- Erro 403: "A prova não está disponível neste momento"
- Só aceita submissões entre `data_aplicacao` e `data_fim`

---

### **TESTE 4: Aluno tentando modificar submissão após finalizar**

**Endpoint:** `POST /submissoes/`
**Arquivo:** `back/app/controllers/submissao_controller.py:110-115`

**Tentativa de Ataque:**
```json
# 1. Aluno finaliza a prova
POST /submissoes/finalizar/10

# 2. Depois tenta fazer nova submissão
POST /submissoes/
{
  "prova_id": 10,
  "questao_id": 25,
  "codigo_submetido": "print('mudando resposta')"
}
```

**Resultado:** **PROTEGIDO**
- Validação de prova finalizada (linha 111-115)
- Erro 403: "Esta prova já foi finalizada e não pode mais ser editada"
- Auto-save bloqueado após finalização

---

### **TESTE 5: Aluno tentando finalizar prova DEPOIS do prazo**

**Endpoint:** `POST /submissoes/finalizar/{prova_id}`
**Arquivo:** `back/app/controllers/submissao_controller.py:122-188`

**Tentativa de Ataque:**
```json
# Prova com data_fim = "2026-02-10 23:59:00"
# Atual = "2026-02-11 10:00:00" (DEPOIS DO PRAZO)

POST /submissoes/finalizar/10
{
  "submissoes": [
    {
      "prova_id": 10,
      "questao_id": 25,
      "codigo_submetido": "print('finalizado atrasado')"
    }
  ]
}
```

**Resultado:** **VULNERÁVEL**
- Endpoint **NÃO VALIDA** se está dentro do período da prova
- Valida whitelist, prova já finalizada, questões válidas
- **FALTA**: Validação temporal (`data_inicio <= now <= data_fim`)

**Impacto:**
- Aluno pode continuar fazendo a prova indefinidamente
- Só finaliza quando quiser, mesmo após prazo
- Pode "colar" depois que outros terminaram

**Exploração Real:**
1. Aluno entra na prova durante período válido
2. Não finaliza até o prazo acabar
3. Busca respostas depois do prazo
4. Finaliza prova dias/semanas depois

---

### **TESTE 6: Aluno tentando enumerar IDs de questões**

**Endpoint:** `GET /submissoes/{questao_id}`
**Arquivo:** `back/app/controllers/submissao_controller.py:32-49`

**Tentativa de Ataque:**
```bash
# Aluno tenta vários IDs para descobrir quais questões existem
for id in range(1, 1000):
    GET /submissoes/{id}
    # Se retornar 200 com null = questão existe mas aluno não tem submissão
    # Se retornar 404 = questão não existe
```

**Resultado:** **PROTEÇÃO PARCIAL**
- Só retorna submissões do próprio aluno
- Revela se IDs de questões existem no sistema (pela resposta)
- Sem rate limiting - aluno pode fazer milhares de requests

**Impacto:** Baixo
- Não revela conteúdo de outras submissões
- Apenas revela estrutura de IDs do banco

---

### **TESTE 7: Aluno tentando ver todas as provas do sistema**

**Endpoint:** `GET /provas/aluno/disponiveis`
**Arquivo:** `back/app/controllers/prova_controller.py:181-212`

**Tentativa de Ataque:**
```bash
GET /provas/aluno/disponiveis
Authorization: Bearer <token_aluno>
```

**Resultado:** **PROTEGIDO CORRETAMENTE**
- Retorna apenas provas onde:
  - `emails_permitidos` está vazio (pública), OU
  - Email do aluno está em `emails_permitidos`
- Não revela provas de outros alunos

---

## Resumo de Vulnerabilidades

| ID | Severidade | Descrição | Status |
|----|-----------|-----------|--------|
| V1 | CRÍTICA | Endpoint de finalizar não valida tempo | **ABERTO** |
| V2 | MÉDIA | Enumeração de IDs sem rate limiting | **ABERTO** |

---

## Recomendações de Correção

### **V1 - CRÍTICA: Validação Temporal no Endpoint de Finalizar**

**Arquivo:** `back/app/controllers/submissao_controller.py:122-188`

**Adicionar após linha 153:**

```python
# 4. Validação Temporal (NOVA)
try:
    from zoneinfo import ZoneInfo
    SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")

    now = datetime.now(SAO_PAULO_TZ)
    data_inicio = datetime.fromisoformat(prova.data_aplicacao).astimezone(SAO_PAULO_TZ)
    data_fim = datetime.fromisoformat(prova.data_fim).astimezone(SAO_PAULO_TZ)

    # Permitir finalizar APENAS se ainda está dentro do prazo
    # OU se está no máximo 5 minutos após o fim (tolerância)
    tolerancia_minutos = 5
    data_fim_com_tolerancia = data_fim + timedelta(minutes=tolerancia_minutos)

    if now > data_fim_com_tolerancia:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O prazo para finalizar esta prova já expirou."
        )

    if now < data_inicio:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta prova ainda não começou."
        )
except (ValueError, TypeError):
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Formato de data inválido na configuração da prova."
    )

# 5. Verificar se já foi finalizada (mover para linha depois)
```

---

### **V2 - MÉDIA: Rate Limiting**

**Implementar em toda a API:**

```python
# Usar FastAPI limiter ou slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/{questao_id}")
@limiter.limit("100/minute") # Máximo 100 requests por minuto
def get_submissao_for_questao(...):
    ...
```

---

## Proteções Funcionando Corretamente

1. **Isolamento de Submissões**: Aluno só vê suas próprias submissões
2. **Validação de Whitelist**: Aluno só acessa provas permitidas
3. **Validação Temporal em Submissões**: Não aceita submissões fora do período
4. **Bloqueio Pós-Finalização**: Auto-save bloqueado após finalizar
5. **Validação de Hierarquia**: Questão deve pertencer à prova especificada
6. **Autenticação JWT**: Token obrigatório em todos os endpoints protegidos
7. **Verificação de Existência no Banco**: `get_current_professor` e `get_current_aluno` validam se usuário existe

---

## Conclusão

**Status Geral:** **BOM COM RESSALVAS**

- Maioria das proteções funcionando corretamente
- 1 vulnerabilidade CRÍTICA que precisa ser corrigida
- 1 vulnerabilidade MÉDIA de baixo impacto

**Prioridade:**
1. **URGENTE**: Adicionar validação temporal no endpoint de finalizar
2. **IMPORTANTE**: Implementar rate limiting

**Risco Atual:**
- Aluno malicioso **PODE** finalizar prova após prazo
- Sistema **NÃO PERMITE** cópia de respostas de outros alunos
- Sistema **NÃO PERMITE** acesso a provas não autorizadas
