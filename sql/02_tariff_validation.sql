SELECT 
    inv.invoice_id,
    inv.line_item_id,
    inv.transaction_reference,
    inv.service_tier AS billed_service_tier,
    inv.volume_units,
    inv.total_line_amount_billed_gbp AS unapproved_spend_leakage_gbp
FROM fact_supplier_invoice_lines AS inv
LEFT JOIN dim_contract_rate_cards AS rate
    ON inv.contract_id = rate.contract_id
WHERE inv.service_tier NOT IN (SELECT DISTINCT tier_name FROM dim_contract_rate_cards)
  AND inv.service_tier != 'Standard Managed Service';
