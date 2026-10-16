# ProductPulse — Review Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.143.1-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3.1-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7.2-3178C6.svg)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-6.0.7-646CFF.svg)](https://vitejs.dev/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-3.4.17-38B2AC.svg)](https://tailwindcss.com/)
[![Apache Hadoop](https://img.shields.io/badge/Hadoop-3.3.6-FF6F00.svg)](https://hadoop.apache.org/)
[![Apache Hive](https://img.shields.io/badge/Hive-3.1.3-FDEE21.svg)](https://hive.apache.org/)
[![Tests](https://img.shields.io/badge/Tests-179%20Passed-success.svg)](#8-test-suite--verification)

> **Academic Project**: Big Data Analytics (BDA) & Natural Language Processing (NLP)  
> **Domain**: E-Commerce Customer Review Mining for Mobile Phones & Accessories  
> **Dataset**: `McAuley-Lab/Amazon-Reviews-2023` (`Cell_Phones_and_Accessories` 25k Stratified Sample)

---

## 1. Project Overview & Problem Statement

E-commerce platforms receive millions of customer reviews. However, raw star ratings alone are insufficient:
- A product rated **4.2 ★** might have excellent camera optics and display quality, but suffer from severe battery overheating or fragile build quality.
- Potential buyers and product managers lack fine-grained, aspect-level intelligence to pinpoint specific product strengths and recurring customer friction points.

**ProductPulse** solves this by building an authentic, reproducible end-to-end analytics platform:
1. **Big Data Processing**: Distributed batch aggregation using **Apache Hadoop Streaming 3.3.6 (MapReduce)** and **Apache Hive 3.1.3** to extract aspect frequencies, review penetrations, and rating-band distributions across 25,000 reviews.
2. **Aspect-Level NLP**: A standardized 6-aspect taxonomy (`battery_charging`, `camera_optics`, `screen_display`, `performance_software`, `build_durability`, `connectivity_audio`) with rule-based aspect extraction and aspect-conditional sentiment evaluation.
3. **Interactive Analytics Dashboard**: A responsive **React 18 + TypeScript + Vite + Tailwind** web application providing catalog browsing, individual product analytics dashboards, category-wide review intelligence, and full-text customer review filtering.

---

## 2. System Architecture & Tech Stack

```
   ┌─────────────────────────────────────────────────────────────┐
   │             Raw Amazon Reviews 2023 Dataset                 │
   │  Cell_Phones_and_Accessories (25,000 reviews, 14.2 MB JSONL) │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│     Relational Ingestion        │       │   Big Data Analytics Pipeline   │
│   SQLite Database (27.5 MB)     │       │   (Dockerized Hadoop & Hive)    │
│   - products (19,065 rows)      │       │   - HDFS Ingestion              │
│   - reviews (25,000 rows)       │       │   - Hadoop MapReduce Streaming  │
│   - product_variants (19,065)   │       │   - Apache Hive 3.1.3 SQL       │
└────────────────┬────────────────┘       └────────────────┬────────────────┘
                 │                                         │
                 ▼                                         ▼
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│       FastAPI Backend API       │       │       Verified BDA Exports      │
│   - /api/products               │       │   data/bda/                     │
│   - /api/reviews                │◄──────┤   - 5 Analytical CSV Exports    │
│   - /api/analytics              │       │   - Hadoop MapReduce part-00000 │
│   - /api/health                 │       │   - Full Job Execution Logs     │
└────────────────┬────────────────┘       └─────────────────────────────────┘
                 │
                 ▼
┌───────────────────────────────────────────────────────────────────┐
│              ProductPulse Web Dashboard (React + Vite)            │
│  - Products Catalogue: Browse 19,065 products with ASIN badges    │
│  - Product Dashboard: 1★-5★ distribution & Hadoop aspect metrics  │
│  - Review Analytics: Category-wide BDA metrics & Hive queries     │
│  - Customer Reviews: Full-text search, star filter, pagination    │
│  - About & Methodology: Architecture, integrity & provenance      │
└───────────────────────────────────────────────────────────────────┘
```

| Layer | Technologies Used | Description |
|---|---|---|
| **Frontend** | React 18, TypeScript 5.7, Vite 6, Tailwind CSS 3.4 | Single-page application with responsive catalogue, product dashboards, and analytics views. |
| **Backend API** | FastAPI 0.143, Pydantic v2, Uvicorn, Python 3.12 | RESTful service with strict contract validation, CORS controls, and SQLite integration. |
| **Database** | SQLite 3 (`backend/db/productpulse.db`) | 25,000 reviews and 19,065 parent products with foreign key enforcement and indexes. |
| **Distributed BDA** | Apache Hadoop 3.3.6, Apache Hive 3.1.3 | Single-node HDFS, Python MapReduce streaming, Derby metastore, and 5 analytical queries. |
| **NLP Baseline** | Python 3.12, Unicode regex boundaries | Deterministic rule-based aspect extraction and aspect-conditional sentiment evaluation. |

---

## 3. Repository Structure

```
D:\ProductPulse-nlp-bda
├── backend/
│   ├── app/
│   │   ├── api/                 # FastAPI routes (health, products, reviews, analytics)
│   │   ├── nlp/                 # NLP baseline service, schemas, and metrics
│   │   ├── schemas/             # Pydantic v2 contract schemas
│   │   ├── main.py              # Backend entrypoint and CORS configuration
│   │   └── database.py          # SQLite connection and integrity handlers
│   └── db/
│       └── productpulse.db      # SQLite database (25,000 reviews, 19,065 products)
├── data/
│   ├── annotation/              # Stratified samples, templates, and baseline reports
│   ├── bda/                     # Genuine Hadoop outputs & 5 Hive analytical CSVs
│   │   ├── hadoop_output/       # Hadoop MapReduce part-00000 (48,708 aggregates)
│   │   ├── hadoop_job_execution.log # Full execution log of Hadoop 3.3.6 job
│   │   ├── hive_job_execution.log   # Full execution log of Hive 3.1.3 queries
│   │   └── hive_query[1-5]*.csv     # Exported analytical query tables
│   ├── manifests/               # Ingestion and reproducibility manifests
│   └── raw/
│       └── sample_reviews_cell_phones_25k.jsonl # 25,000 review source corpus
├── docs/                        # Architecture, demo scripts, results & submission checklist
│   ├── PROJECT_ARCHITECTURE.md  # Detailed technical data flow and Mermaid diagrams
│   ├── DEMO_SCRIPT.md           # 5-7 minute presentation script & viva defense
│   ├── PROJECT_RESULTS.md       # Full verified metrics, test counts & limitations
│   └── FINAL_SUBMISSION_CHECKLIST.md # Submission and demonstration checklist
├── frontend/                    # React 18 + TypeScript + Vite + Tailwind dashboard
│   ├── src/
│   │   ├── api/client.ts        # Typed frontend API client with safe error handling
│   │   ├── components/          # Layout, catalogue, analytics, and review views
│   │   │   ├── catalogue/       # ProductCatalogueView & ProductDashboardView
│   │   │   ├── analytics/       # BigDataAnalyticsView (5 Hive query explorers)
│   │   │   ├── reviews/         # ReviewsView (filter, search, pagination)
│   │   │   └── layout/          # Navbar and Footer
│   │   └── types/api.ts         # TypeScript schema parity interfaces
│   └── tests/                   # Node.js automated test suites (42 tests)
├── scripts/
│   ├── bda/                     # Hadoop mapper/reducer, Hive HQL, and Docker scripts
│   ├── evaluate_nlp_baseline.py # NLP baseline evaluation benchmark
│   ├── run_nlp_baseline_demo.py # Interactive NLP inference CLI tool
│   └── verify_project_integrity.py # SHA-256 and SQLite asset integrity verifier
├── tests/                       # Backend unittest suite (137 tests)
└── requirements-api.txt         # Pinned API dependencies
```

---

## 4. Setup & Run Instructions (Windows Environment)

### Prerequisites
- **OS**: Windows 10/11
- **Python**: Python 3.12 (in `.venv`)
- **Node.js**: v18+ or v20+ with npm
- **Docker Desktop**: Required *only* if re-running the Hadoop/Hive batch pipeline (pre-computed genuine results are already committed in `data/bda/`).

### Step 1: Start the FastAPI Backend

From the workspace root (`D:\ProductPulse-nlp-bda`):

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Verify backend health in a browser or terminal:
- **API Health Endpoint**: `http://127.0.0.1:8000/api/health`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/api/docs`
- **Redoc Documentation**: `http://127.0.0.1:8000/api/redoc`

### Step 2: Start the React Frontend

Open a separate PowerShell terminal:

```powershell
cd D:\ProductPulse-nlp-bda\frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

- **Frontend URL**: `http://127.0.0.1:5173`

---

## 5. Web Application Exploration Guide

When opened in a browser, ProductPulse provides four primary navigation tabs:

### 1. Products (`catalogue`) — Default Landing View
- Displays all **19,065 catalogue products** in deterministic order (reviews descending, ASIN ascending).
- **Honest Provenance**: Shows `"Product name unavailable"` with an honest sub-label explaining that raw review records do not contain upstream catalog titles, avoiding synthetic hallucinations.
- **Canonical ASIN Badges**: Easily identify products by canonical ASIN (`ASIN: B01415QHYW`).
- **One-Click Drill-Down**: Click any product card, title, or the **"Dashboard"** button to open the dedicated **Individual Product Dashboard**:
  - **Section A (Overview)**: Total reviews, average customer star rating, helpful votes, verified purchase percentage, and variant child ASINs.
  - **Section B (Rating Distribution)**: Empirical 1★ to 5★ histogram with review counts, percentage bars, and earliest/latest review dates.
  - **Section C (Aspect Analytics)**: Authentic Hadoop MapReduce extractions across the 6 locked aspects showing mention volume, aspect star rating, helpful votes, and positive/medium/friction-point rating breakdown bars.
  - **Section D (Customer Reviews)**: Paginated list of real customer reviews for that specific product.

### 2. Review Analytics (`bda`) — Category-Wide Big Data Intelligence
Explore pre-computed, verified analytical results from Apache Hive and Hadoop MapReduce:
- **5 KPI Header Cards**: Total reviews evaluated (25,000), corpus star rating (4.1655 ★), unique products (19,065), aspect-discussing reviews (16,409), and total aspect mentions (26,029).
- **Query 1 (Aspect Discussion Volumes)**: Review counts and weighted average ratings across the 6 locked aspects.
- **Query 2 (Top Products by Aspect)**: Products with the highest discussion volume per aspect. Click "Inspect Product" to jump directly to its individual dashboard.
- **Query 3 (Customer Friction Points)**: Lowest-rated product aspects (with $\ge 5$ reviews) highlighting empirical pain points.
- **Query 4 (Rating Band Distributions)**: Proportion of 1–2★, 3★, and 4–5★ reviews across each aspect.
- **Query 5 (Aspect Review Penetration)**: Percentage of a product's reviews that discuss a specific aspect (bounded between 0.0% and 100.0%).
- **Technical Architecture & Provenance**: Infrastructure details, execution logs, and data integrity guarantees.

### 3. Customer Reviews (`reviews`) — Full-Text Review Explorer
- Filter all 25,000 genuine customer reviews by:
  - Parent ASIN
  - Variant ASIN
  - Star rating (1★ to 5★)
  - Verified Purchase status
- Displays user ID, review timestamp, helpful vote counter, and verified purchase badge.
- Discloses rating-only submissions honestly without synthesizing review text.

### 4. About & Methodology (`overview`)
- Background context, dataset boundaries, system health verification, and project deliverables.

---

## 6. How the NLP Baseline Works & Execution

ProductPulse includes a deterministic, lexicon-based NLP baseline for aspect detection and aspect-conditional sentiment evaluation across the 6 locked aspects:

### Six Locked Taxonomy Aspects
1. `build_durability` (Build & Durability: case, drop, rugged, scratch, metal, hinge, cracked)
2. `battery_charging` (Battery & Charging: battery life, drain, mah, charger, cable, overheat)
3. `screen_display` (Screen & Display: screen, oled, amoled, brightness, resolution, touch)
4. `performance_software` (Performance & Software: lag, freeze, reboot, ram, processor, ui, bug)
5. `camera_optics` (Camera & Optics: camera, photo, lens, megapixel, zoom, selfie, focus)
6. `connectivity_audio` (Connectivity & Audio: bluetooth, wifi, 5g, signal, speaker, mic, headphone)

### Running the Evaluation Benchmark
Evaluates the baseline against held-out validation partitions:

```powershell
.\.venv\Scripts\python.exe scripts/evaluate_nlp_baseline.py
```

- **Task 1 (Aspect Detection)**: Sample A validation partition (180 eligible decision units). **Macro-F1: 0.7778**.
- **Task 2 (Aspect-Conditional Sentiment)**: Sample B validation partition (19 eligible 3-class units). **Macro-F1: 1.0000**.
- **Scientific Limitation Warning**: These metrics measure *rule-verification agreement* against automated draft heuristic pseudo-labels, NOT human gold truth accuracy.

### Running the Interactive NLP Demo CLI

```powershell
.\.venv\Scripts\python.exe scripts/run_nlp_baseline_demo.py
```

Test custom smartphone review sentences to see extracted aspect mentions and polarity classification in real time.

---

## 7. How the Hadoop & Hive Pipeline Works

The Big Data Analytics pipeline was executed on authentic Apache Hadoop and Apache Hive environments in Docker:

1. **HDFS Ingestion**: Uploaded 25,000 review records to `/productpulse/input/sample_reviews_cell_phones_25k.jsonl`.
2. **Hadoop Streaming MapReduce**:
   - Docker container: `apache/hadoop:3.3.6`.
   - Mapper: `scripts/bda/aspect_mapper.py` (Unicode boundary regex, 6 aspects + `__ALL_REVIEWS__`).
   - Reducer: `scripts/bda/aspect_reducer.py` (Key aggregation into 48,708 rows).
   - Produced `part-00000` (2.15 MB), persisted in `data/bda/hadoop_output/`.
3. **Apache Hive 3.1.3 Analytics**:
   - Container: `productpulse-hive:3.1.3` with Derby embedded metastore.
   - Script: `scripts/bda/hive_analytics.hql`.
   - Mapped external table `productpulse_bda.product_aspect_metrics` over `part-00000`.
   - Executed 5 analytical queries and exported verified CSVs into `data/bda/`.

### Verifying Existing Hadoop Output

```powershell
.\.venv\Scripts\python.exe scripts/bda/verify_hadoop_output.py
```

### Re-running the Full Pipeline (Requires Docker Desktop)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bda\run_bda_pipeline.ps1
```

*Note: Pre-computed outputs are already committed under `data/bda/` and served directly by the FastAPI backend, so Docker is not required for daily demo execution.*

---

## 8. Test Suite & Verification

The project includes **179 automated tests** covering backend API routes, database integrity, NLP services, and frontend contracts:

### A. Run Backend Unit Tests (137 Tests)

```powershell
.\.venv\Scripts\python.exe -m unittest discover tests
```
*Result: `Ran 137 tests — OK` (All 137 passed in ~5s).*

### B. Run Frontend Tests (42 Tests)

```powershell
cd frontend
npm test
```
*Result: `tests 42, pass 42, fail 0` (All 42 passed in 11 test suites).*

### C. Run Frontend Production Build Check

```powershell
cd frontend
npm run build
```
*Result: `tsc && vite build` completed with zero TypeScript errors.*

### D. Verify 17 Protected Assets & SQLite Database

```powershell
.\.venv\Scripts\python.exe scripts/verify_project_integrity.py
```
*Result: All 17 protected assets and SQLite database verified 100% intact.*

---

## 9. Key Results & Verified Findings

| Metric | Verified Value | Source / Grounding |
|---|---|---|
| **Corpus Sample Size** | 25,000 reviews | `data/raw/sample_reviews_cell_phones_25k.jsonl` |
| **Catalog Products** | 19,065 unique parent ASINs | `backend/db/productpulse.db` (`products` table) |
| **Corpus Average Star Rating** | 4.1655 ★ | All 25,000 reviews average |
| **Reviews Discussing Aspects** | 16,409 reviews (65.6%) | Reviews with $\ge 1$ aspect mention |
| **Aspect-Discussing Avg Rating** | 4.1299 ★ | Average across the 16,409 aspect reviews |
| **Reviews with No Detected Aspects** | 8,591 reviews (34.4%) | Reviews with 0 aspect keywords (avg 4.2336 ★) |
| **Total Aspect Mentions / Pairs** | 26,029 pairs | Hive Query 1 sum (average 1.59 aspects per review) |
| **Most Discussed Aspect** | `build_durability` (10,846 reviews) | 4.1485 ★ weighted average, 11,439 helpful votes |
| **Highest-Rated Aspect** | `performance_software` (4.1923 ★) | 2,506 reviews, 6,526 helpful votes |
| **Lowest-Rated Aspect** | `connectivity_audio` (3.9409 ★) | 1,557 reviews, 16.96% low-rating share (1–2★) |

---

## 10. Known Limitations & Scientific Disclosures

1. **Missing Catalog Metadata**: In the raw Amazon 2023 review JSONL, products lack official catalog titles and brands (`title = NULL`, `brand = NULL`). ProductPulse presents an honest fallback (`"Product name unavailable"`) and uses canonical parent ASINs, deliberately avoiding fabricated product names.
2. **Review Ratings vs. Sentiment**: Star ratings represent reviewer scores (1.0 to 5.0) and are disposition baselines, not text-derived ground-truth aspect sentiment.
3. **Automated Pseudo-Labels in NLP Baseline**: Evaluated NLP metrics measure rule agreement against automated heuristic draft pseudo-labels, NOT human gold truth accuracy.
4. **Single-Node Execution**: Hadoop Streaming and Hive were executed in single-node containerized environments suitable for local reproducibility rather than multi-terabyte production clusters.

---

## 11. Troubleshooting Common Startup Issues

- **Port 8000 Conflict**: If another service occupies port 8000, inspect running processes via `Get-NetTCPConnection -LocalPort 8000`. Do not terminate unrelated services.
- **Port 5173 Conflict**: If port 5173 is occupied, run `npm run dev -- --host 127.0.0.1 --port 5174` and update CORS origins in `backend/app/main.py`.
- **Python ModuleNotFoundError**: Ensure commands are run using the project virtual environment (`.\.venv\Scripts\python.exe`) rather than global system Python.
- **Missing BDA CSV Exports**: If `GET /api/analytics/*` returns an HTTP 500 error, verify that the 5 CSV exports are present in `data/bda/`.
