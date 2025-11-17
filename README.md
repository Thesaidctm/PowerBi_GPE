# Módulo Gestor Municipal – Power BI + MySQL

Este pacote é o ponto de partida para montar um módulo gestor robusto conectado ao banco `gpdcoronelmurta`.

## Estrutura
- `sql/` – scripts para criar views no MySQL (faça isso primeiro)
- `powerquery/` – consultas M para o Power BI puxar as views
- `dax/` – medidas e colunas calculadas para montar os dashboards

## Ordem recomendada
1. Rodar os SQLs no MySQL com um usuário com permissão de CREATE VIEW.
2. No Power BI, criar fonte MySQL e importar as consultas M.
3. Colar as medidas DAX no modelo.
4. Montar as páginas: Visão Geral, Financeiro, Arrecadação, Parcelamentos, Licitações e Contratos.

Ajuste os nomes de host, usuário e porta do MySQL conforme o seu ambiente.
