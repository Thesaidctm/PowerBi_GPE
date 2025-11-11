CREATE OR REPLACE VIEW vw_execucao_receita_mensal AS
SELECT
    er.ano,
    er.mes,
    er.orgao_id,
    er.fonte_id,
    er.valor_previsto,
    er.valor_arrecadado
FROM execucao_receita er;