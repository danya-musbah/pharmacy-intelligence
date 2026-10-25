# Pharmacy Intelligence — منصة تحليلات ذكية للصيدليات

نسخة أولية (demo) تجارية لمنصة تحليل بيانات صيدليات، موجهة لأصحاب ومديري
الصيدليات في ليبيا. المنصة **لا تستبدل** منظومة نقاط البيع الحالية؛ بل تعمل
كطبقة تحليل وذكاء فوق البيانات التي تنتجها تلك المنظومة أصلًا (sales /
purchases / inventory / products).

> جميع البيانات المعروضة في وضع التجربة (Demo) **اصطناعية بالكامل** ولا تمثل
> صيدلية حقيقية ولا تحتوي على بيانات عملاء حقيقيين.

---

## 1. Architecture

```
Existing pharmacy POS / software
        |
        v  (CSV / Excel export, or synthetic demo data)
Data Import  ->  Column Mapping  ->  Normalization  ->  Validation
        |
        v
Standard data model (sales, purchases, inventory, products)
        |
        v
Analytics layer (pandas) -- sales, inventory, expiry, profit,
        |                    forecast, association rules
        v
Flask REST API (/api/*)
        |
        v
Frontend (vanilla HTML/CSS/JS, RTL, Chart.js) -- served separately
```

Key design decision: **analytics are never coupled to a specific source file**.
Every import goes through `Importer -> Normalizer -> Standard Schema ->
Analytics`, so a pharmacy using a different POS system only needs a new
column-mapping profile, not a rewrite of the analytics.

### Tech stack
- Frontend: HTML5, CSS3 (custom, RTL-first), vanilla JavaScript, Chart.js
  (via CDN). No React/Vue/Angular, no TypeScript, no build step.
- Backend: Python, Flask, pandas, numpy, openpyxl.
- Data: CSV files in `data/` for the demo dataset; in-memory pandas
  DataFrames at runtime (see "Limitations" below — no database yet).

### Folder structure
```
pharmacy-intelligence/
├── index.html                 # redirects to frontend/index.html
├── README.md
├── requirements.txt
├── frontend/
│   ├── index.html             # actual app entry point
│   ├── css/ (style, components, responsive)
│   └── js/  (api, app, charts, data-import)
├── backend/
│   ├── app.py                 # Flask entry point + static file serving
│   ├── routes/api.py          # all /api/* endpoints
│   ├── analytics/             # sales, inventory, expiry, profit,
│   │                            demand_forecast, association_rules
│   ├── data_processing/       # loader, normalizer, validator
│   └── importers/             # CSV/Excel file reading + table-type guess
├── data/                       # generated synthetic CSVs (git-ignored)
└── scripts/generate_data.py    # synthetic dataset generator
```

---

## 2. Running the project

### Backend (required — the frontend calls it for all data and analytics)
```bash
cd pharmacy-intelligence
pip install -r requirements.txt --break-system-packages   # or use a venv
python backend/app.py
```
This serves both the API and the frontend at `http://localhost:5000`.

### Regenerating the synthetic dataset
```bash
python scripts/generate_data.py
```
Produces `data/products.csv`, `data/sales.csv`, `data/purchases.csv`,
`data/inventory.csv` (~3,200 products, ~19,700 sales invoices / ~41,000 line
items over Jan–Jun 2026, ~1,300 purchase orders). The generator uses
per-product demand archetypes (fast/medium/slow mover, dead stock, seasonal,
sudden-spike) plus weekday/hour/seasonal multipliers, so every KPI, chart,
and "needs attention" item in the demo is computed *from this dataset* —
nothing in the UI is a hardcoded number.

### GitHub Pages (frontend only)
The frontend can be published on GitHub Pages, but Pages cannot run the
Python/Flask backend. Until a separate backend is deployed and configured,
API-powered screens, demo data, imports, and analytics will not load.

1. Push this repository to GitHub, making sure the `main` branch is selected.
2. In the repository, open **Settings → Pages** and set the build and deployment
   source to **GitHub Actions**.
3. The `Deploy frontend to GitHub Pages` workflow publishes the contents of
   `frontend/`. Open the Pages URL shown in the repository's Pages settings.

To enable data later, deploy the Flask backend to a Python hosting service and
set `window.PHARMACY_API_BASE` to its `/api` URL before `js/api.js` loads.
Configure Flask CORS to allow the Pages site origin.

### Split deployment (Cloudflare Pages + separate backend)
The frontend never talks to the filesystem or the analytics code directly —
it only calls `/api/*`. To deploy the frontend and backend separately:
1. Deploy `frontend/` as a static site (e.g. Cloudflare Pages).
2. Deploy `backend/` as a Python service (any host that runs Flask/WSGI).
3. Before `frontend/js/api.js` loads, set:
   ```html
   <script>window.PHARMACY_API_BASE = "https://your-backend-host/api";</script>
   ```
4. Enable CORS on the backend for the frontend's origin (already wired via
   `flask-cors`; restrict `CORS(app)` to a specific origin in production
   instead of allowing all origins).

No secrets, API keys, or credentials are hardcoded anywhere in `frontend/`.
All analytics logic, the synthetic/imported datasets, and validation rules
live in `backend/` and are never sent to the browser — the frontend only
ever receives computed JSON results.

---

## 3. Importing a real pharmacy's data

"أريد تحليل بيانات صيدليتي" walks through:
1. Upload a CSV or Excel file.
2. The backend guesses the table type (sales/purchases/inventory) and
   suggests a column mapping using common Arabic/English header aliases
   (see `backend/data_processing/normalizer.py`).
3. The user confirms/adjusts the mapping.
4. The backend validates the normalized data (missing prices, duplicate
   invoice/product lines, invalid dates, missing product names) and reports
   a data-quality score.
5. On success, the imported table replaces the in-memory demo table for the
   current server process, and every other page (dashboard, sales,
   inventory, ...) recomputes from it immediately.

Adding a new importer (e.g. a specific POS's export format) means adding
entries to `COLUMN_ALIASES` in `normalizer.py` — the analytics layer never
needs to change.

---

## 4. Features implemented

- Landing screen with three entry paths (demo / upload / "explore
  integration" — the last is informational only, see limitation below).
- Demo dataset preview: searchable, paginated tables for sales, purchases,
  inventory, products.
- Simulated "processing" sequence before landing on the dashboard.
- Dashboard: 30-day KPIs vs. previous period, "needs your attention" feed
  (low stock, expiry risk, dead stock, sales trend), top products.
- Executive summary (highlights / risks / opportunities / actions), computed
  from the same analytics functions as the rest of the app.
- Sales analytics: trend over time, weekday breakdown, peak hours, top
  products/categories, range selector (30/90 days, 6 months).
- Inventory: low-stock detection (days-of-stock-left from 30-day average
  daily sales), reorder-quantity suggestions (lead time + safety buffer).
- Dead-stock detection (idle ≥ 45 days by default).
- Expiry intelligence: 7/30/90-day buckets, estimated units sold before
  expiry vs. units at risk — phrased as estimates, never certainties, and
  with no medical framing.
- Profit intelligence: top profit, top revenue, top margin, and "high
  volume / low margin" products, plus the sales-vs-profit quadrant data.
- Association rules (frequently-bought-together) via co-occurrence support/
  confidence/lift — phrased as a purchasing correlation, not a treatment
  recommendation.
- Lightweight demand forecast (linear trend + confidence band) — labeled as
  an estimate.
- Data-quality report (missing prices, duplicate lines, invalid dates).
- CSV/Excel import wizard: upload → column-mapping → validation → apply →
  dashboard, with Arabic error messages for empty/invalid/unsupported files.
- Responsive layout: sidebar becomes a drawer + bottom nav under 900px,
  horizontally-scrollable KPI cards and tables, resizing charts, tested down
  to 360px width with no horizontal page overflow.

### Demo-only / not fully built
- "ربط منظومة الصيدلية" (API / database export / local connector / custom
  integration) is **informational only** — no real connector exists yet, and
  the UI is careful never to claim a live integration ("يمكن إعداد
  التكامل"/"يمكن إعداد اتصال لاحقًا"), per the no-false-claims requirement.
- The "الإعدادات" (settings) item from the original nav list was not built
  out — there's nothing yet to configure since there's no persistent
  account/store.
- JSON/API/database/local-connector importers are stubbed as roadmap cards
  in the import screen, not implemented — only CSV and Excel are.

---

## 5. Before using this with a real pharmacy's data

- **No database.** Imported/demo data lives in server-process memory
  (`backend/data_processing/loader.py`). Restarting the server resets to the
  demo dataset. A real deployment needs persistent storage (Postgres/SQLite)
  per pharmacy account, plus multi-tenant isolation.
- **No authentication.** There's no login, no per-pharmacy account
  separation, and no access control on `/api/*`. Required before handling
  real business data.
- **No production WSGI server.** `python backend/app.py` runs Flask's
  development server. Use gunicorn/uwsgi behind a reverse proxy in
  production.
- **CORS is open (`CORS(app)`).** Restrict to the deployed frontend origin.
- **Forecast model is intentionally simple** (linear trend + residual-based
  band on the last 60 days) — adequate for an explainable demo, not a
  production forecasting system. A real deployment should validate forecast
  accuracy against held-out data before pharmacies rely on it for ordering
  decisions.
- **Import normalization covers common header variants**, not every POS
  export in use in Libya. Expect to extend `COLUMN_ALIASES` as real files
  are seen.
- **File size / row limits:** the import endpoints have no explicit cap yet;
  add one (and streaming/chunked parsing) before accepting arbitrarily large
  exports.

---

## 6. Known limitations / things to double check

- The demo dataset regenerates deterministically (`random.seed(42)`), so
  numbers are stable across runs unless `generate_data.py` is edited.
- The association-rule engine is a simple co-occurrence calculation, not a
  library implementation of Apriori/FP-Growth — fine at this dataset size,
  but would need a real implementation (e.g. `mlxtend`) at much larger scale.
- The "sudden demand increase" and "seasonal" patterns are visible in the
  data but there's no dedicated anomaly-detection endpoint surfacing them by
  name yet beyond the sales trend chart and the dashboard's "المبيعات ارتفعت
  X%" line.
- No automated test suite yet (`tests/` is a placeholder) — the flows above
  were verified manually via the API (`curl`) and by checking generated
  JSON payloads end to end (import → validate → apply → dashboard → reset).

---

## 7. Customization

- **Colors**: edit the CSS variables at the top of `frontend/css/style.css`
  (`--color-primary`, `--color-success`, etc.) — everything else references
  these.
- **Demo data shape**: edit the archetype weights, category price ranges,
  or seasonal factors in `scripts/generate_data.py`, then re-run it.
- **Add an analytics module**: add a function to the relevant file in
  `backend/analytics/`, expose it via a new route in `backend/routes/api.py`,
  and call it from a new or existing page renderer in `frontend/js/app.js`.
- **Add an importer**: extend `COLUMN_ALIASES` in
  `backend/data_processing/normalizer.py` for a new source system's header
  names.

---

## 8. Security & privacy notes

- The synthetic dataset contains no real person's name, phone number,
  address, ID number, or medical record — only product/business data.
- The repository is intended to stay private; the deployment split (static
  frontend + separate Python backend) keeps analytics logic and datasets
  server-side, never shipped to the browser.
- No secrets or credentials are hardcoded in `frontend/` — the only runtime
  configuration is the API base URL (`window.PHARMACY_API_BASE`).
