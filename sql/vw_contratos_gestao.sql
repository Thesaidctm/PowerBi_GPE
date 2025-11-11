CREATE OR REPLACE VIEW vw_contratos_gestao AS
SELECT
    lc.id AS contrato_id,
    lc.numero_contrato,
    lc.processo_id,
    lc.data_assinatura,
    lc.vigencia_inicio,
    lc.vigencia_fim,
    lc.valor_total,
    DATEDIFF(lc.vigencia_fim, CURDATE()) AS dias_para_vencer
FROM licit_contrato lc
WHERE lc.vigencia_fim IS NOT NULL;