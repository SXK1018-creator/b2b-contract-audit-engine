# Automated B2B Contract Audit & Cost Recovery Engine

An enterprise-grade financial data pipeline that audits supplier invoices against Master Services Agreements (MSAs) to discover billing errors, prevent vendor overcharges, and eliminate margin leakage.

## Executive Summary & Commercial Impact

In large-scale corporate procurement, manual review of high-volume supplier transactions is inefficient, exposing companies to systemic billing errors. This repository contains an end-to-end data engineering solution that automates invoice reconciliation by programmatically validating transactional inputs against contract rate cards.

By applying data analytics to transaction ledgers, the engine protects vendor governance and delivers quantifiable cost recovery:

* **Revenue Leakage Identified:** £14,642.84 across 155 transactional rows.
* **Audit Coverage Rate:** 100% automated monthly processing, replacing sample audits.
* **Core Risk Mitigations:** Resolves duplicate item submissions, uncontracted tariff inflation, and the omission of contractual step-down volume discounts.

---

## Analytical Architecture & Relational Schema

The solution models data inside an enterprise cloud data warehouse using a classic dimensional tracking architecture.

┌─────────────────────────────────┐           ┌─────────────────────────────────┐
│    dim_contract_rate_cards      │           │    fact_supplier_invoice_lines  │
├─────────────────────────────────┤           ├─────────────────────────────────┤
│ PK  contract_id (VARCHAR)       │1          │ PK  line_item_id (VARCHAR)      │
│     supplier_name (VARCHAR)     │──┐        │     invoice_id (VARCHAR)        │
│ PK  tier_name (VARCHAR)         │  │        │ FK  contract_id (VARCHAR)       │
│     min_volume (INT)            │  └───────∞│     transaction_reference (VAR) │
│     max_volume (INT)            │           │     order_date (DATE)           │
│     standard_unit_rate_gbp (NUM)│           │     service_tier (VARCHAR)      │
│     admin_fee_pct (NUM)         │           │     volume_units (INT)          │
└─────────────────────────────────┘           │     unit_rate_billed_gbp (NUM)  │
│     admin_fee_billed_pct (NUM)  │
│     total_billed_amount_gbp(NUM)│
└─────────────────────────────────┘


### Risk Detection Logic Matrix

1. **Duplicate Billing (Double Charging):** The engine tracks the `transaction_reference` token across the invoice fact table using a windowing partition. Rows where multiple entries map back to a single business event are flagged for immediate deduction.
2. **Tariff Misapplication:** A `LEFT JOIN` evaluates the billed `service_tier` field against the master contract rate card. Any entry without a match indicates unapproved, out-of-contract spending.
3. **Volume Tier Omissions:** The engine calculates the true deduplicated volume sum across the billing period and compares it to the contract thresholds. This prevents suppliers from ignoring step-down discounts when aggregate volumes breach high-volume boundaries.

---

## Cloud Infrastructure & Production Deployment Strategy

To scale this framework across an enterprise infrastructure without restructuring core code, the local python pipeline maps directly to a serverless, managed architecture within Microsoft Azure or Amazon Web Services (AWS).

[Raw Vendor Input] -> [Cloud Landing Zone] -> [Serverless Trigger] -> [Data Warehouse Layer] -> [C-Suite Analytics View]
(CSV Mail/SFTP)       (Azure Blob / S3)       (Azure Func / Lambda)   (Synapse / Snowflake)      (Excel Report / Power BI)

### 1. Ingestion and Land Orchestration
Incoming raw monthly CSV invoices from external suppliers are routed via secure SFTP drop-zones directly into cloud storage accounts, using **Azure Blob Storage** or **AWS S3** as an immutable raw landing zone.

### 2. Automated Pipeline Scheduling
The data orchestration pipelines are scheduled and managed through enterprise tooling, such as **Azure Data Factory (ADF)** or **AWS Glue**. Pipelines are scheduled on a monthly billing run frequency or triggered dynamically via storage event boundaries using **Azure Event Grid** or **AWS EventBridge**.

### 3. Serverless Compute Execution
The extraction, transformation, and validation code is wrapped inside serverless compute frameworks, such as **Azure Functions** or **AWS Lambda**. This allows the Python scripts to scale up automatically during high-volume processing runs and scale down to zero when idle, keeping platform costs minimal.

### 4. Enterprise Warehouse Staging
Processed tables are loaded into relational data warehouses, such as **Azure Synapse Analytics**, **Snowflake**, or **Google BigQuery**. Here, the structured SQL views execute over millions of historical transactions to maintain live compliance reporting and vendor scorecards.

---

## Repository Implementation Guide

Follow these steps to run the complete data pipeline and generate the corporate reporting artifacts locally.

### 1. Replicate the Environment
Clone this repository and verify your local directory configuration matches the project structure:
```bash
git clone https://github.com
cd b2b-contract-audit-engine
```

### 2. Generate the Baseline Dataset
Run the data generator to initialize your folders and populate the messy source datasets containing the financial overcharges:
```bash
python B2B-procurement/src/data_generator.py
```

### 3. Verify Database Queries via VS Code
To execute relational queries locally without external database software:
1. Open the repository root folder inside **VS Code**.
2. Install the **SQLite** extension.
3. Run the following command in the terminal to initialize your database tracking asset:
```bash
python -c "import pandas as pd, sqlite3; conn = sqlite3.connect('B2B-procurement/data/audit_warehouse.db'); pd.read_csv('B2B-procurement/data/contract_rate_card.csv').to_sql('dim_contract_rate_cards', conn, if_exists='replace', index=False); pd.read_csv('B2B-procurement/data/supplier_invoice_lines.csv').to_sql('fact_supplier_invoice_lines', conn, if_exists='replace', index=False); conn.close(); print('Warehouse Initialized.')"
```
4. Open any script within the `B2B-procurement/sql/` directory, right-click, and select **SQLite: Run Query** to view findings side-by-side.

### 4. Run the Automation Engine
Execute the processing script to perform the end-to-end audit and generate the formatted corporate Excel artifact:
```bash
python B2B-procurement/src/audit_engine.py
```
Open the `B2B-procurement/reports/` directory to inspect the generated **`Executive_Leakage_Variance_Report.xlsx`** spreadsheet, which includes structured metrics and sorted data tabs ready for executive management review.

