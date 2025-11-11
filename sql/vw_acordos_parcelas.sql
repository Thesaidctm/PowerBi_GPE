CREATE OR REPLACE VIEW vw_acordos_parcelas AS
SELECT
    app.id AS parcela_id,
    app.acordo_parcelamento_id AS acordo_id,
    app.numero_parcela,
    app.data_vencimento,
    app.valor_parcela,
    apos.situacao_atual
FROM acordo_parcela_parcelamento app
LEFT JOIN acordo_posicao_parcelamento apos
    ON apos.acordo_parcela_parcelamento_id = app.id;