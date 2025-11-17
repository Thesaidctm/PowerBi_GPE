# Módulo Gestor Municipal – Power BI + MySQL

Este pacote é o ponto de partida para montar um módulo gestor robusto conectado ao banco `gpdcoronelmurta`.

## Estrutura
- `sql/` – scripts para criar views no MySQL (faça isso primeiro)
- `powerquery/` – consultas M para o Power BI puxar as views
- `dax/` – medidas e colunas calculadas para montar os dashboards
- `app/` – backend FastAPI que expõe os dashboards via JSON

## Ordem recomendada
1. Rodar os SQLs no MySQL com um usuário com permissão de CREATE VIEW.
2. No Power BI, criar fonte MySQL e importar as consultas M.
3. Colar as medidas DAX no modelo.
4. Montar as páginas: Visão Geral, Financeiro, Arrecadação, Parcelamentos, Licitações e Contratos.

Ajuste os nomes de host, usuário e porta do MySQL conforme o seu ambiente.

## Backend FastAPI (Módulo Gestor)

### Pré-requisitos
- Python 3.10+
- Dependências do `requirements.txt`

### Configuração
1. Copie `.env.example` para `.env` e ajuste as variáveis (host, porta, usuário e senha do MySQL).
2. (Opcional) Crie um ambiente virtual: `python -m venv .venv && source .venv/bin/activate`.
3. Instale as dependências: `pip install -r requirements.txt`.

### Execução
```
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Endpoints principais
- `GET /health`
- `GET /dashboard/overview`
- `GET /dashboard/receita/resumo?ano=YYYY`
- `GET /dashboard/despesa/resumo?ano=YYYY`
- `GET /dashboard/licitacoes/resumo?ano=YYYY`
- `GET /dashboard/contratos/proximos-vencimentos?dias=90`
- `GET /dashboard/obras/resumo`
- `GET /dashboard/convenios/resumo`

Os SQLs usam colunas padrão sugeridas nas views. Caso o schema real seja diferente, ajuste as colunas nos arquivos em `app/routers/`.
