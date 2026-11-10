WITH ranked_transactions AS (
    SELECT 
        invoice_id,
        line_item_id,
        contract_id,
        transaction_reference,
        order_date,
        service_tier,
        volume_units,
        total_line_amount_billed_gbp,
        ROW_NUMBER() OVER (
            PARTITION BY transaction_reference 
            ORDER BY line_item_id ASC
        ) AS transaction_occurrence_count
    FROM fact_supplier_invoice_lines
)
SELECT 
    invoice_id,
    line_item_id,
    transaction_reference,
    order_date,
    service_tier,
    volume_units,
    total_line_amount_billed_gbp AS duplicate_leakage_amount_gbp
FROM ranked_transactions
WHERE transaction_occurrence_count > 1;