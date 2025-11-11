CREATE OR REPLACE VIEW vw_acordos_parcelamento AS
SELECT
    ap.id AS acordo_id,
    ap.contribuinte_id,
    ap.data_acordo,
    ap.qtde_parcelas,
    ap.valor_total
FROM acordo_parcelamento ap;