import os
import random
import numpy as np
import pandas as pd

def make_directories():
    """Establish clear repository folders relative to the script location."""
    for folder in ['../data', '../sql', '../reports']:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Created directory: {folder}")

def generate_mock_data():
    """Create structural contract dimensions and invoice fact tables."""
    np.random.seed(42)
    random.seed(42)
    
    print("Generating contract rate card dimension...")
    
    # Contract volume brackets explicitly populated to prevent syntax tokens breaking
    contract_data = {
        'contract_id': ['CON-2026-X01'] * 3,
        'supplier_name': ['Vertex Business Solutions Ltd'] * 3,
        'tier_name': ['Tier 1 (Base)', 'Tier 2 (Mid-Volume)', 'Tier 3 (High-Volume)'],
        'min_volume': [0, 5001, 15001],
        'max_volume': [5000, 15000, 99999999],
        'standard_unit_rate_gbp': [45.00, 38.50, 32.00],
        'admin_fee_pct': [0.12, 0.10, 0.08]
    }
    df_contract = pd.DataFrame(contract_data)
    df_contract.to_csv('../data/contract_rate_card.csv', index=False)
    
    print("Generating monthly supplier invoice fact table...")
    
    invoice_lines = []
    base_rate = 45.00
    base_admin_fee = 0.12
    
    for i in range(1, 151):
        volume_units = int(random.randint(85, 140))
        total_billed = round(volume_units * base_rate * (1 + base_admin_fee), 2)
        
        invoice_lines.append({
            'invoice_id': 'INV-2026-OCT',
            'line_item_id': f'LN-2026-OCT-{i:03d}',
            'contract_id': 'CON-2026-X01',
            'transaction_reference': f'TX-REF-{1000 + i}',
            'order_date': f'2026-10-{random.randint(1, 31):02d}',
            'service_tier': 'Standard Managed Service',
            'volume_units': volume_units,
            'unit_rate_billed_gbp': base_rate,
            'admin_fee_billed_pct': base_admin_fee,
            'total_line_amount_billed_gbp': total_billed
        })
        
    df_invoice = pd.DataFrame(invoice_lines)
    
    print("Injecting overcharges and billing anomalies...")
    
    # Explicitly populated indices to prevent bracket truncation
    duplicate_indices = [14, 42, 77, 104, 131]
    for idx, target_idx in enumerate(duplicate_indices):
        dup_row = df_invoice.iloc[target_idx].copy()
        dup_row['line_item_id'] = f'LN-2026-OCT-DUP-{idx+1:02d}'
        df_invoice = pd.concat([df_invoice, pd.DataFrame([dup_row])], ignore_index=True)
        
    for idx in range(25, 37):
        df_invoice.loc[idx, 'service_tier'] = 'Premium Custom Bespoke'
        df_invoice.loc[idx, 'unit_rate_billed_gbp'] = 65.00
        df_invoice.loc[idx, 'total_line_amount_billed_gbp'] = round(
            df_invoice.loc[idx, 'volume_units'] * 65.00 * (1 + base_admin_fee), 2
        )
        
    df_invoice.to_csv('../data/supplier_invoice_lines.csv', index=False)
    
    print("Data generation complete. Exported rows cleanly to ../data/.")
    print(f"Total operational volume generated: {df_invoice['volume_units'].sum():,} units.")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    make_directories()
    generate_mock_data()