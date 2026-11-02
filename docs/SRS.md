# Pharmacy Intelligence Software Requirements Specification

## 1. Document Information

- Project Name: Pharmacy Intelligence
- Document Title: Software Requirements Specification
- Version: 1.0
- Date: 2026-11-02
- Document Status: Draft for review

## 2. Introduction

### 2.1 Purpose

This document describes the functional and non-functional requirements for the Pharmacy Intelligence prototype. The system is designed to help pharmacy managers understand product performance, stock risk, sales trends, expiry exposure, imperfect data quality, and demand patterns using synthetic or imported pharmacy datasets.

### 2.2 Scope

The current implementation includes:

- dashboard analytics for pharmacy operations,
- inventory monitoring and reorder recommendations,
- sales performance analysis,
- expiry-risk analysis,
- profit intelligence,
- demand forecasting,
- association-rule discovery,
- CSV/Excel import and mapping support.

The system does not yet provide persistent storage, authentication, or enterprise-grade role management.

### 2.3 Intended Audience

- developers reviewing the implementation,
- project stakeholders evaluating the prototype,
- future maintainers extending the analytics layer,
- technical reviewers assessing feasibility and architecture.

### 2.4 Definitions and Acronyms

- KPI: Key Performance Indicator
- POS: Point-of-Sale system
- CSV: Comma-separated values
- API: Application Programming Interface
- RTL: Right-to-left layout
- SRS: Software Requirements Specification

### 2.5 References

- README.md
- backend/routes/api.py
- backend/data_processing/normalizer.py
- backend/data_processing/validator.py
- scripts/generate_data.py

## 3. Overall Description

### 3.1 Product Perspective

Pharmacy Intelligence operates as an analytics layer above existing pharmacy data sources. It does not replace the operational system; rather, it consumes exported or generated data and produces actionable operational insight.

### 3.2 Product Functions

The product provides the following functions:

1. import raw sales, purchases, inventory, and product data,
2. detect likely table type and column mappings,
3. validate the imported dataset,
4. compute operational KPIs,
5. surface risk signals for low stock and expiry,
6. visualize trends and product performance,
7. estimate future demand.

### 3.3 User Classes and Characteristics

- Pharmacy owner: reviews inventory and revenue indicators.
- Pharmacy manager: monitors performance and stock risk.
- Analyst: inspects data quality and operational trends.
- Developer: maintains and extends analytics modules.

### 3.4 Operating Environment

The application runs locally in a Python environment using Flask and pandas. The frontend is browser-based and static, served from the same local server for demo usage.

### 3.5 Design and Implementation Constraints

- Data is stored in memory at runtime; there is no database layer yet.
- Frontend is intentionally plain HTML/CSS/JavaScript without a framework.
- The system is built as a demo/prototype, not a production SaaS platform.
- The analytics layer must remain independent of the raw source file structure.

### 3.6 Assumptions and Dependencies

- CSV/Excel files will be available for import.
- Source data will contain common pharmacy-derived fields such as product name, barcode, quantity, price, category, and date.
- The analytics engine depends on pandas and numpy for tabular operations.

## 4. System Features

### Feature ID: F-001

Feature Name: Demo Dashboard

- Description: Shows a KPI dashboard derived from synthetic pharmacy data.
- Actor: Pharmacy manager or owner
- Preconditions: data files are present and backend is running
- Main Workflow: load demo dataset, compute KPIs, display dashboard
- Alternative Workflow: if load fails, show an error state
- Postconditions: dashboard metrics are visible
- Business Rules: metrics are derived from the current dataset and compared to previous periods

### Feature ID: F-002

Feature Name: Sales Analytics

- Description: Summarizes revenue, units, product trends, weekday behavior, and peak sales hours.
- Actor: Analyst or manager
- Preconditions: sales records are available
- Main Workflow: group sales by date/category/product and compute summary metrics
- Alternative Workflow: selected time-range changes the analysis window
- Postconditions: trend and distribution information is shown
- Business Rules: periods are computed from the underlying date field without hard-coded values

### Feature ID: F-003

Feature Name: Inventory Monitoring

- Description: Identifies low-stock and reorder opportunities.
- Actor: Inventory manager
- Preconditions: inventory and sales data are available
- Main Workflow: compute average sales and estimate days of stock left
- Alternative Workflow: reorder suggestions are generated from safety stock assumptions
- Postconditions: risk items are exposed to the user
- Business Rules: a product with little stock remaining relative to recent velocity is flagged

### Feature ID: F-004

Feature Name: Expiry Risk Detection

- Description: Estimates products at risk of expiry within short horizons.
- Actor: Pharmacy operator
- Preconditions: inventory includes expiry dates
- Main Workflow: bucket product records by expiry horizon and compare with demand estimates
- Alternative Workflow: no expiry data leads to a limited or empty report
- Postconditions: expiry risk counts and affected products are returned
- Business Rules: results are presented as estimates, not definitive clinical determinations

### Feature ID: F-005

Feature Name: Profit Intelligence

- Description: Highlights the most profitable and highest-value products and categories.
- Actor: Operations lead
- Preconditions: sales data includes quantity and price fields
- Main Workflow: compute revenue, margin and categorize high-volume-low-margin items
- Alternative Workflow: if fields are missing, quality validation will flag the issue
- Postconditions: profit summary and matrix are generated
- Business Rules: margin values must be derived from the available sales data

### Feature ID: F-006

Feature Name: Association Rules

- Description: Identifies products that are frequently purchased together.
- Actor: Marketing or merchandising manager
- Preconditions: sales records contain invoice/product lineage
- Main Workflow: count co-occurrence of items in a sales basket
- Alternative Workflow: sparse data reduces rule count or confidence
- Postconditions: rules are returned with support, confidence, and lift values
- Business Rules: rules are calculated as purchasing correlations, not medical recommendations

### Feature ID: F-007

Feature Name: Demand Forecast

- Description: Forecasts upcoming demand using a lightweight linear trend.
- Actor: Planner or manager
- Preconditions: valid date and sales values exist
- Main Workflow: aggregate demand over time and extrapolate based on recent pattern
- Alternative Workflow: insufficient data yields a conservative forecast
- Postconditions: forecast values with confidence bounds are returned
- Business Rules: output is marked as an estimate

### Feature ID: F-008

Feature Name: Data Import and Mapping

- Description: Accepts CSV or Excel files and suggests a mapping from source headers to normalized fields.
- Actor: Analyst or user
- Preconditions: a valid file is uploaded
- Main Workflow: read file, detect table type, map columns, validate content, apply data
- Alternative Workflow: unsupported file type or empty file yields a user-facing error
- Postconditions: in-memory dataset is replaced or updated
- Business Rules: mapping must respect required schema and discard unmapped columns

## 5. Functional Requirements

- FR-001: The system shall load a demo dataset when the application starts if the CSV files are present.
- FR-002: The system shall provide a dashboard endpoint returning KPI and product summary data.
- FR-003: The system shall expose sales analytics by time range and category.
- FR-004: The system shall detect low-stock products based on stock levels and sales velocity.
- FR-005: The system shall generate reorder suggestions based on a minimum safety buffer and lead-time assumptions.
- FR-006: The system shall detect dead-stock products based on inactivity thresholds.
- FR-007: The system shall calculate expiry risk buckets for near-term product expiry.
- FR-008: The system shall calculate revenue, profit, and margin information from sales data.
- FR-009: The system shall identify frequently co-purchased product combinations.
- FR-010: The system shall produce a basic forecast based on recent demand trends.
- FR-011: The system shall validate imported data for missing fields, invalid dates, duplicates, and missing product names.
- FR-012: The system shall accept CSV and Excel imports.
- FR-013: The system shall provide column-mapping suggestions based on common pharmacy header aliases.
- FR-014: The system shall allow the in-memory dataset to be replaced after validation.
- FR-015: The system shall serve the frontend and API via the local Flask app.

## 6. Non-Functional Requirements

### 6.1 Performance

- The system should respond to dashboard and analytics requests within a few seconds for the demo dataset.
- Import processing should remain responsive for moderate spreadsheet sizes.

### 6.2 Security

- The application is not intended to be a production security boundary.
- Secrets must not be committed to source control.
- External hosting should restrict CORS to approved origins.

### 6.3 Reliability

- The system should handle empty files and invalid imports gracefully with informative messages.
- API routes should return structured errors rather than stack traces in production.

### 6.4 Availability

- The prototype is intended for local use and demonstration deployment.
- Data loss occurs on process restart because the dataset is held in memory.

### 6.5 Maintainability

- Analytics logic should remain separated from source-specific schema details.
- New external import profiles should follow the normalizer pattern.

### 6.6 Usability

- The interface should be responsive and readable on desktop and tablet screens.
- The frontend should provide Arabic and English-friendly UI labels for the demo scenario.

### 6.7 Accessibility

- Color should not be the only indicator of a state change.
- Layout should be readable and keyboard-friendly where possible.

### 6.8 Scalability

- The current design is suitable for demo-scale and moderate operational datasets.
- Large-scale production use would require a database and optimized analytics workflow.

### 6.9 Compatibility

- The app must work with recent Python 3 and common modern browsers.
- Import support currently targets CSV and Excel file exports.

### 6.10 Data Integrity

- Required fields must be present before analysis is run.
- Duplicate line items should be detected and reported.
- Invalid dates and missing product names should trigger data-quality warnings.

## 7. External Interface Requirements

### 7.1 User Interfaces

- landing page with demo and import flows,
- dashboard screen,
- analytics screen for sales and inventory,
- data-quality and import wizard screens.

### 7.2 Software Interfaces

- Flask app serves static frontend assets and JSON API routes.
- pandas DataFrames represent the in-memory datasets.

### 7.3 APIs

Main backend interfaces include dashboard, sales, inventory, expiry, profit, association, forecast, and import endpoints.

### 7.4 Database Interfaces

The current implementation does not use a persistent database. It interfaces with CSV data files loaded into memory at runtime.

### 7.5 Third-party Integrations

- Chart.js is used for frontend plotting.
- openpyxl is used for Excel file reading.

## 8. Data Requirements

### 8.1 Main Entities

- Products
- Sales
- Purchases
- Inventory

### 8.2 Relationships

- Each sales row may reference a product by barcode or product name.
- Inventory rows represent stock-on-hand with product metadata and expiry dates.
- Purchases provide supplier and order-level information.
- Products provide item attributes such as category, price, and manufacturer.

### 8.3 Data Validation

The validator checks for:

- missing required columns,
- missing price values,
- duplicate invoice/product rows,
- invalid dates,
- missing product names.

### 8.4 Data Constraints

- Product names should not be empty.
- Dates should parse correctly when required.
- Quantity and price fields should be numeric where applicable.

### 8.5 Data Retention

The prototype does not persist imported data beyond the current runtime session.

## 9. System Architecture

The architecture follows a layered structure:

1. Source data acquisition: CSV/Excel or generated demo data.
2. Import and mapping: file detection, alias mapping, normalization.
3. Validation: required field and data quality checks.
4. Analytics layer: behavior for inventory, sales, expiry, profit, forecast, and rules.
5. API layer: JSON responses to frontend requests.
6. Frontend layer: static browser UI and interactive charts.

This separation keeps the business logic independent from the source format while preserving a lightweight prototype design.
