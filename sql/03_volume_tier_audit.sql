WITH deduplicated_invoice_lines AS (
    SELECT 
        invoice_id,
        line_item_id,
        contract_id,
        transaction_reference,
        order_date,
        service_tier,
        volume_units,
        unit_rate_billed_gbp,
        total_line_amount_billed_gbp,
        ROW_NUMBER() OVER (
            PARTITION BY transaction_reference 
            ORDER BY line_item_id ASC
        ) AS transaction_occurrence_count
    FROM fact_supplier_invoice_lines
),
total_monthly_volume AS (
    SELECT 
        contract_id,
        SUM(volume_units) AS total_genuine_volume
    FROM deduplicated_invoice_lines
    WHERE transaction_occurrence_count = 1
    GROUP BY contract_id
),
active_contract_tier AS (
    SELECT 
        v.contract_id,
        v.total_genuine_volume,
        r.tier_name AS contracted_tier_name,
        r.standard_unit_rate_gbp AS contracted_base_rate,
        r.admin_fee_pct AS contracted_admin_fee_pct
    FROM total_monthly_volume AS v
    INNER JOIN dim_contract_rate_cards AS r
        ON v.contract_id = r.contract_id
        AND v.total_genuine_volume >= r.min_volume
        AND v.total_genuine_volume <= r.max_volume
)
SELECT 
    inv.invoice_id,
    inv.line_item_id,
    inv.transaction_reference,
    inv.volume_units,
    inv.unit_rate_billed_gbp AS supplier_billed_rate,
    tier.contracted_base_rate AS contractual_target_rate,
    inv.total_line_amount_billed_gbp AS amount_billed_gbp,
    ROUND(inv.volume_units * tier.contracted_base_rate * (1 + tier.contracted_admin_fee_pct), 2) AS contractual_expected_amount_gbp,
    ROUND(inv.total_line_amount_billed_gbp - (inv.volume_units * tier.contracted_base_rate * (1 + tier.contracted_admin_fee_pct)), 2) AS tier_omission_leakage_gbp
FROM deduplicated_invoice_lines AS inv
INNER JOIN active_contract_tier AS tier
    ON inv.contract_id = tier.contract_id
WHERE inv.service_tier = 'Standard Managed Service'
  AND inv.transaction_occurrence_count = 1;
