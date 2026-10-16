# ProductPulse — Project Specification (`PROJECT_SPEC.md`)

## 1. Project Overview and Purpose

**ProductPulse** is an academically rigorous, full-stack product-review analytics platform inspired by modern e-commerce catalogues. It bridges Big Data Analytics (BDA), Natural Language Processing (NLP), database management, and web engineering to extract actionable, verifiable customer intelligence from genuine product reviews.

The system empowers users to:
1. Browse and search an authentic product catalogue.
2. View genuine product metadata, images, and reviews.
3. Analyse sentiment distributions (positive, negative, neutral) with explicit classification baselines.
4. Detect aspect-level discussions relevant to the target category.
5. Identify recurring customer complaint themes grounded in actual review excerpts (evidence tracing).
6. Compare two products side-by-side using consistent metrics and review evidence.
7. Observe historical sentiment/volume trends only where timestamps and sample sizes legitimately support them.
8. Validate Big Data batch processing executed via Hadoop, MapReduce/Streaming, and Hive.
9. Inspect complete data provenance, analytical calculations, denominators, and transparent system limitations.

---

## 2. Mandatory Scope Lock: Mobile Phones & Accessories Only

> **PERMANENT PROJECT-WIDE CONSTRAINT**  
> The sole authorized category for ProductPulse is **Mobile Phones & Accessories**.  
> This restriction is permanent and strictly applies across all 12 project phases.

### Scope Governance Rules:
1. **Source Restriction**: Only the official `McAuley-Lab/Amazon-Reviews-2023` dataset hosted on Hugging Face may be used.
2. **Category Fidelity**: Products outside the verified *Mobile Phones & Accessories* domain (e.g., laptops, generic home appliances, headphones, or office supplies) are strictly excluded unless verified as mobile accessories within this explicit category.
3. **No Silent Switching**: The project will never switch categories without explicit prior user approval supported by documented dataset evidence.
4. **No Synthetic / Scraped Data**: No scraping of Amazon or third-party web pages; no fabrication or hallucination of ASINs, products, reviews, images, timestamps, or ratings.
5. **Phase 1 Validation**: Phase 1 must verify the exact source category naming, metadata availability, review density, and filtering rules before ingestion.

---

## 3. Technology Stack and Architecture Principles

| Layer | Authorized Technology | Scope & Role |
| :--- | :--- | :--- |
| **Frontend** | React (v18+), TypeScript, Vite, Tailwind CSS | Single-page application, responsive catalog, analytics dashboards, comparison view. |
| **Backend API** | Python (3.12+), FastAPI, Pydantic, SQLAlchemy | REST API, input validation, analytical query serving, pagination, error handling. |
| **Serving Database** | SQLite (via SQLAlchemy / parameterized SQL) | Local analytical serving layer, indexed query execution. |
| **NLP Engine** | NLTK, scikit-learn | Tokenization, POS tagging, TF-IDF, baseline sentiment classification, aspect extraction, semantic retrieval. |
| **Big Data Analytics (BDA)** | Hadoop (HDFS), Hadoop Streaming / MapReduce, Apache Hive | Scalable distributed batch aggregation, MapReduce word/ngram frequencies, Hive analytical queries. |
| **Storage & Provenance** | JSONL (Raw & Normalized), Manifests, Checksums | Audit trail, ingestion logging, intermediate batch artifacts. |

### Localhost Binding Constraints
- Frontend Host: `http://localhost:5173`
- Backend Host: `http://localhost:8000`
- Both services must explicitly bind to `127.0.0.1` by default.
- CORS must be strictly configured for `http://localhost:5173` during local development.

---

## 4. User Journeys and Functional Objectives

### Journey 1: Product Catalogue & Search (`/`)
- Browse verified Mobile Phones & Accessories products.
- Keyword search by product title, brand, and feature keywords.
- Filtering by verified price range, brand, average rating, and review count.
- Clear pagination and sorting (rating, review count, price).
- Explicit loading, empty, and error states.

### Journey 2: Product Analytics & Review Inspection (`/products/:productId`)
- Detailed product metadata: verified title, brand, pricing, genuine product images (with robust fallback placeholders).
- Overall sentiment breakdown (positive, negative, neutral) with defined classifier confidence.
- Category-appropriate aspect breakdown (e.g., battery life, camera quality, display, build quality, charging speed, software/UI).
- Aspect sentiment scores with direct clickable review evidence.
- Recurring complaint clusters with snippet references and review links.
- Historical trend chart (month-by-month volume and sentiment) only if valid timestamps exist and review density exceeds minimum thresholds ($N \ge 10$ reviews/period).

### Journey 3: Head-to-Head Product Comparison (`/compare?product_ids=...`)
- Side-by-side comparison of two verified products in the Mobile Phones & Accessories category.
- Normalised, consistent metric evaluation (overall sentiment %, aspect sentiment breakdown, rating distributions, complaint density).
- Direct side-by-side review evidence retrieval.

---

## 5. Non-Goals and Explicit Prohibitions

1. **No External Paid APIs**: No reliance on OpenAI, Google Gemini API, Claude API, or any paid third-party NLP/LLM service for core run-time application functionality.
2. **No Streamlit**: The application must be a standard React + FastAPI architecture.
3. **No Scraping**: No automated scraping or crawling of Amazon or retail websites.
4. **No Fabricated Records**: Never invent mock ASINs, fake reviews, artificial star ratings, or imaginary evaluation numbers.
5. **No Star Rating Equivalence**: A reviewer's star rating is never treated as ground-truth aspect sentiment. Ratings represent general customer disposition, not granular aspect polarity.
6. **No Silent Drops**: Records dropped during ingestion, parsing, or filtering must be logged in manifests with explicit failure reasons.
7. **No Overstating Capabilities**: A complaint cluster is an empirical cluster of negative review text, not a proven hardware/manufacturing defect.

---

## 6. Data Integrity and Verification Rules

1. **Provenance Tracking**: Every product and review in SQLite or JSONL must carry its source dataset identifier, split, and ingest timestamp.
2. **Stable Local Identifiers**: Review records lacking a unique upstream review ID must receive a deterministic composite key (e.g., hash of reviewer ID, product ID, timestamp, and review text).
3. **Transparent Denominators**: Every percentage, ratio, and average displayed in the UI or API must specify its exact denominator (e.g., total aspect mentions vs. total reviews).
4. **Unique Reviews vs. Extracted Snippets**: A single review may yield multiple complaint snippets; the system must report both snippet count and distinct review count.
5. **Reproducibility**: All batch transformations and MapReduce/Hive jobs must produce deterministic outputs from identical inputs.

---

## 7. Major Acceptance Criteria Across Phases

- **Phase 0**: Complete environment inspection, port collision detection, architecture foundation, and scope lock documented.
- **Phase 1**: Verified Hugging Face dataset metadata schema, confirmed Mobile Phones & Accessories subcategory, verified download sizes and access methods.
- **Phase 2**: Bounded, approved ingestion of a sample ($\le 500$ reviews initially) with complete data quality manifest.
- **Phase 3**: Final SQLite schema, foreign key integrity, migrations, and validated contracts.
- **Phase 4**: FastAPI backend operational, passing automated integration tests for health, catalog, product details, and analytics endpoints.
- **Phase 5 & 6**: React frontend responsive, accessible, fully connected to backend endpoints, with functional search, filters, and review browsing.
- **Phase 7 & 8**: Validated NLTK/scikit-learn NLP pipeline for sentiment, aspect extraction, and complaint theme discovery with review evidence linking.
- **Phase 9**: Real execution of Hadoop MapReduce / Streaming and Hive batch aggregations, verified against reference computations.
- **Phase 10**: Comparative analytics and trend views verified against data density rules.
- **Phase 11 & 12**: End-to-end testing, documentation, reproducible setup scripts, and academic viva readiness.

---

## 8. Uncertainties and Required Phase 1 Investigations

1. **Exact Hugging Face Dataset Subset Name**: Determine whether the category is named `Cell_Phones_and_Accessories`, `Electronics`, or a nested partition in `McAuley-Lab/Amazon-Reviews-2023`.
2. **Metadata Schema & Join Key**: Confirm whether product metadata and reviews join on `parent_asin`, `asin`, or another identifier.
3. **Image URL Availability & Validity**: Inspect whether metadata records provide valid, reachable image URLs or require local fallback icons.
4. **Selective Access / Chunking Feasibility**: Verify whether Hugging Face parquet/json files can be streamed or sampled without transferring entire multi-gigabyte archives.
5. **Timestamp Format**: Inspect whether review timestamps are Unix epoch seconds, milliseconds, or formatted ISO strings.
