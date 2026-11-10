import os
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows

def run_commercial_audit_pipeline():
    print("Initializing commercial audit engine automation...")
    
    rate_card_path = '../data/contract_rate_card.csv'
    invoice_path = '../data/supplier_invoice_lines.csv'
    
    if not os.path.exists(rate_card_path) or not os.path.exists(invoice_path):
        raise FileNotFoundError("Missing baseline CSV datasets. Please run data_generator.py first.")
        
    df_rate_card = pd.read_csv(rate_card_path)
    df_invoice = pd.read_csv(invoice_path)
    
    # 1. Isolate Leakage Profile 1: Duplicate Billing
    df_invoice['is_duplicate'] = df_invoice.duplicated(subset=['transaction_reference'], keep='first')
    df_duplicates = df_invoice[df_invoice['is_duplicate'] == True].copy()
    
    # 2. Isolate Leakage Profile 2: Tariff Misapplication
    df_tariff_errors = df_invoice[
        (~df_invoice['service_tier'].isin(df_rate_card['tier_name'])) & 
        (df_invoice['service_tier'] != 'Standard Managed Service') &
        (df_invoice['is_duplicate'] == False)
    ].copy()
    
    # 3. Process Leakage Profile 3: Volume Tier Omissions
    df_genuine_lines = df_invoice[
        (df_invoice['is_duplicate'] == False) & 
        (df_invoice['service_tier'] == 'Standard Managed Service')
    ].copy()
    
    total_genuine_units = df_genuine_lines['volume_units'].sum()
    print(f"Total deduplicated standard volume calculated: {total_genuine_units:,} units.")
    
    matched_tier = df_rate_card[
        (total_genuine_units >= df_rate_card['min_volume']) & 
        (total_genuine_units <= df_rate_card['max_volume'])
    ]
    
    if not matched_tier.empty:
        contracted_rate = float(matched_tier['standard_unit_rate_gbp'].iloc[0])
        contracted_admin_fee = float(matched_tier['admin_fee_pct'].iloc[0])
        target_tier_name = str(matched_tier['tier_name'].iloc[0])
    else:
        contracted_rate = 45.00
        contracted_admin_fee = 0.12
        target_tier_name = "Tier 1 (Base)"
        
    print(f"Contractual tier matched: {target_tier_name} (Rate: £{contracted_rate:.2f})")
    
    df_genuine_lines['expected_unit_rate_gbp'] = contracted_rate
    df_genuine_lines['expected_admin_fee_pct'] = contracted_admin_fee
    df_genuine_lines['contractual_expected_amount_gbp'] = round(
        df_genuine_lines['volume_units'] * contracted_rate * (1 + contracted_admin_fee), 2
    )
    df_genuine_lines['tier_omission_leakage_gbp'] = round(
        df_genuine_lines['total_line_amount_billed_gbp'] - df_genuine_lines['contractual_expected_amount_gbp'], 2
    )
    
    df_tier_variance = df_genuine_lines[df_genuine_lines['tier_omission_leakage_gbp'] > 0].copy()
    
    # 4. Compile Master Summary Metrics
    total_billed_gross = df_invoice['total_line_amount_billed_gbp'].sum()
    duplicate_leakage_sum = df_duplicates['total_line_amount_billed_gbp'].sum()
    tariff_leakage_sum = df_tariff_errors['total_line_amount_billed_gbp'].sum()
    tier_leakage_sum = df_tier_variance['tier_omission_leakage_gbp'].sum()
    total_recovered_savings = duplicate_leakage_sum + tariff_leakage_sum + tier_leakage_sum
    audited_correct_total = total_billed_gross - total_recovered_savings
    
    # 5. Generate Stamped Corporate Excel Workbook
    wb = Workbook()
    ws_dash = wb.active
    ws_dash.title = "Executive Summary"
    ws_dash.sheet_view.showGridLines = True
    
    font_title = Font(name="Segoe UI", size=18, bold=True, color="1F497D")
    font_section = Font(name="Segoe UI", size=12, bold=True, color="1F497D")
    font_header = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    font_data = Font(name="Segoe UI", size=11, bold=False)
    font_bold_data = Font(name="Segoe UI", size=11, bold=True)
    
    fill_header = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    fill_alert = PatternFill(start_color="FDE9D9", end_color="FDE9D9", fill_type="solid")
    
    thin_side = Side(border_style="thin", color="D9D9D9")
    border_data = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
    
    ws_dash["A1"] = "Commercial Audit & Cost Recovery Dashboard"
    ws_dash["A1"].font = font_title
    ws_dash["A2"] = "Review Period: October 2026 | Vendor: Vertex Business Solutions Ltd"
    ws_dash["A2"].font = Font(name="Segoe UI", size=11, italic=True, color="595959")
    
    ws_dash["A4"] = "Financial Performance Summary"
    ws_dash["A4"].font = font_section
    
    summary_headers = ["Metric Description", "Value (GBP)"]
    for col_num, header in enumerate(summary_headers, 1):
        cell = ws_dash.cell(row=5, column=col_num, value=header)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="left" if col_num == 1 else "right")
        
    metrics = [
        ("Total Gross Billed Invoice Amount", total_billed_gross),
        ("Leakage Profile 1: Duplicate Charges Identified", duplicate_leakage_sum),
        ("Leakage Profile 2: Uncontracted Tariff Misapplications", tariff_leakage_sum),
        ("Leakage Profile 3: Omitted Volume Discount Tier Variances", tier_leakage_sum),
        ("Total Validated Audit Financial Leakage", total_recovered_savings),
        ("True Contractual Approved Spending Balance", audited_correct_total)
    ]
    
    for idx, (metric_desc, metric_val) in enumerate(metrics, 6):
        cell_desc = ws_dash.cell(row=idx, column=1, value=metric_desc)
        cell_val = ws_dash.cell(row=idx, column=2, value=metric_val)
        
        cell_desc.font = font_bold_data if "Total" in metric_desc or "True" in metric_desc else font_data
        cell_val.font = font_bold_data if "Total" in metric_desc or "True" in metric_desc else font_data
        
        cell_val.number_format = '£#,##0.00'
        cell_desc.border = border_data
        cell_val.border = border_data
        
        if "Leakage" in metric_desc or "Identified" in metric_desc:
            cell_val.fill = fill_alert
            
    # Sheet 2: Duplicate Errors
    ws_dup = wb.create_sheet(title="Duplicate Errors")
    ws_dup.sheet_view.showGridLines = True
    df_dup_clean = df_duplicates[['line_item_id', 'transaction_reference', 'order_date', 'service_tier', 'volume_units', 'total_line_amount_billed_gbp']]
    write_clean_sheet(ws_dup, df_dup_clean, font_header, fill_header, font_data, border_data, ['£#,##0.00' if col == 'total_line_amount_billed_gbp' else None for col in df_dup_clean.columns])
    
    # Sheet 3: Tariff Misapplications
    ws_tariff = wb.create_sheet(title="Tariff Anomalies")
    ws_tariff.sheet_view.showGridLines = True
    df_tariff_clean = df_tariff_errors[['line_item_id', 'transaction_reference', 'order_date', 'service_tier', 'volume_units', 'total_line_amount_billed_gbp']]
    write_clean_sheet(ws_tariff, df_tariff_clean, font_header, fill_header, font_data, border_data, ['£#,##0.00' if col == 'total_line_amount_billed_gbp' else None for col in df_tariff_clean.columns])
    
    # Sheet 4: Volume Tier Variances
    ws_tier = wb.create_sheet(title="Volume Tier Variances")
    ws_tier.sheet_view.showGridLines = True
    df_tier_clean = df_tier_variance[['line_item_id', 'transaction_reference', 'volume_units', 'unit_rate_billed_gbp', 'expected_unit_rate_gbp', 'total_line_amount_billed_gbp', 'contractual_expected_amount_gbp', 'tier_omission_leakage_gbp']]
    write_clean_sheet(
        ws_tier, 
        df_tier_clean, 
        font_header, 
        fill_header, 
        font_data, 
        border_data, 
        ['£#,##0.00' if 'gbp' in col or 'rate' in col else None for col in df_tier_clean.columns]
    )
    
    # Set explicit layout column dimensions dynamically across sheets
    for sheet in wb.worksheets:
        for col in sheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            sheet.column_dimensions[col_letter].width = max(max_len + 4, 12)
            
    output_path = '../reports/Executive_Leakage_Variance_Report.xlsx'
    wb.save(output_path)
    print(f"✨ Automated audit run successful. Executive Excel report saved to: {output_path}")

def write_clean_sheet(ws, df, font_header, fill_header, font_data, border_data, formats):
    for col_idx, text in enumerate(df.columns, 1):
        cell = ws.cell(row=1, column=col_idx, value=text.replace('_', ' ').title())
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center", vertical="center")
        
    for row_idx, row_data in enumerate(dataframe_to_rows(df, index=False, header=False), 2):
        for col_idx, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font = font_data
            cell.border = border_data
            
            if isinstance(value, (int, float)):
                cell.alignment = Alignment(horizontal="right")
            else:
                cell.alignment = Alignment(horizontal="left")
                
            fmt = formats[col_idx - 1]
            if fmt:
                cell.number_format = fmt

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    run_commercial_audit_pipeline()