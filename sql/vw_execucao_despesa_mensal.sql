CREATE OR REPLACE VIEW vw_execucao_despesa_mensal AS
SELECT
    ed.ano,
    ed.mes,
    ed.orgao_id,
    ed.dotacao,
    ed.valor_empenhado,
    ed.valor_liquidado,
    ed.valor_pago
FROM execucao_despesa ed;