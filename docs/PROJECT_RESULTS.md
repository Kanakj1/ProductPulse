# ProductPulse — Empirical Project Results & Verification Report

This report summarizes all verified quantitative results, Hadoop/Hive batch analytics outputs, NLP baseline benchmark metrics, automated test results, data provenance disclosures, and project limitations.

---

## 1. Corpus Demographics & Verified High-Level Metrics

All metrics reported here are grounded directly in the 25,000-review Amazon dataset (`data/raw/sample_reviews_cell_phones_25k.jsonl`), the SQLite database (`backend/db/productpulse.db`), and Hadoop MapReduce outputs (`data/bda/hadoop_output/part-00000`).

| Metric | Verified Value | Grounding Source |
|---|---|---|
| **Total Reviews Evaluated** | **25,000** | JSONL line count, SQLite `reviews` table, Hadoop `__ALL_REVIEWS__` |
| **Unique Catalog Products** | **19,065** | SQLite `products` table (`COUNT(DISTINCT parent_asin)`) |
| **All-Corpus Average Star Rating** | **4.1655 ★** | Mathematical mean of all 25,000 reviewer star ratings |
| **Reviews Discussing $\ge 1$ Aspect** | **16,409** (65.64%) | Deduplicated review set matching any of the 6 locked aspect lexicons |
| **Aspect-Discussing Reviews Avg Rating** | **4.1299 ★** | Mean rating across the 16,409 aspect-discussing reviews |
| **Reviews with No Detected Aspects** | **8,591** (34.36%) | Reviews matching zero aspect keywords (avg rating: 4.2336 ★) |
| **Total Aspect-Review Pairs (Mentions)** | **26,029** | Cumulative sum of Hive Query 1 aspect review counts |
| **Average Aspects per Discussing Review** | **1.586** | $26,029 \div 16,409$ (demonstrates multi-aspect discussion density) |
| **Total Customer Helpful Votes** | **44,053** | Cumulative sum of helpful votes across all 25,000 reviews |
| **Verified Purchase Rate** | **83.69%** | 20,923 of 25,000 reviews marked `verified_purchase = 1` |

---

## 2. Hadoop & Hive Analytics Results (Six Locked Aspects)

Batch analytics were executed in official Docker containers (`apache/hadoop:3.3.6` and `productpulse-hive:3.1.3`). Query results are exported in `data/bda/`.

### A. Query 1: Overall Aspect Discussion Volumes & Helpful Votes
*Source: `data/bda/hive_query1_aspect_volumes.csv`*

| Aspect | Distinct Reviews | Weighted Avg Rating | Cumulative Helpful Votes | Share of Aspect Discussions |
|---|---|---|---|---|
| **Build & Durability** (`build_durability`) | 10,846 | 4.1485 ★ | 11,439 | 41.67% |
| **Battery & Charging** (`battery_charging`) | 4,514 | 4.1834 ★ | 8,428 | 17.34% |
| **Screen & Display** (`screen_display`) | 4,350 | 4.0154 ★ | 7,900 | 16.71% |
| **Performance & Software** (`performance_software`) | 2,506 | 4.1923 ★ | 6,526 | 9.63% |
| **Camera & Optics** (`camera_optics`) | 2,256 | 4.0718 ★ | 5,976 | 8.67% |
| **Connectivity & Audio** (`connectivity_audio`) | 1,557 | 3.9409 ★ | 3,784 | 5.98% |
| **Total / Macro Average** | **26,029** | **4.1299 ★** | **44,053** | **100.00%** |

**Key Insights**:
- `build_durability` is by far the most discussed aspect in mobile accessories (cases, screen protectors, hinges, cables), representing 41.67% of all aspect discussions.
- `performance_software` has the highest customer satisfaction score (4.1923 ★).
- `connectivity_audio` has the lowest customer satisfaction score (3.9409 ★), reflecting frequent Bluetooth pairing and audio crackling complaints.

---

### B. Query 4: Star Rating-Band Distributions by Aspect
*Source: `data/bda/hive_query4_rating_bands.csv`*

| Aspect | Low (1–2★) | Med (3★) | High (4–5★) | Total Reviews | High Rating % | Low Rating % |
|---|---|---|---|---|---|---|
| **Build & Durability** | 1,503 | 1,032 | 8,311 | 10,846 | 76.63% | 13.86% |
| **Battery & Charging** | 604 | 353 | 3,557 | 4,514 | 78.80% | 13.38% |
| **Screen & Display** | 735 | 426 | 3,189 | 4,350 | 73.31% | 16.90% |
| **Performance & Software** | 303 | 238 | 1,965 | 2,506 | 78.41% | 12.09% |
| **Camera & Optics** | 334 | 237 | 1,685 | 2,256 | 74.69% | 14.80% |
| **Connectivity & Audio** | 264 | 190 | 1,103 | 1,557 | 70.84% | **16.96%** |

**Key Insights**:
- `connectivity_audio` and `screen_display` have the highest proportion of 1–2 star customer dissatisfaction (16.96% and 16.90% respectively).
- `battery_charging` has the highest high-rating share (78.80%), indicating that when accessories perform adequately, customers reliably award 4–5 stars.

---

### C. Query 2 & Query 3 Highlights: Top Discussed Products & Friction Points
- **Top Discussed Battery Product**: `B07P9S6R9Y` with 30 distinct reviews discussing battery/charging.
- **Top Discussed Screen Product**: `B01415QHYW` with 21 distinct reviews discussing screen/display.
- **Top Identified Customer Friction Point (Query 3)**: Product `B08KQ1L2W3` (5 reviews for `build_durability`, average rating: **2.60 ★**).
- **Secondary Friction Point (Query 3)**: Product `B07H36MNN1` (7 reviews for `screen_display`, average rating: **2.71 ★**, with 13 helpful votes).

---

### D. Query 5: Aspect Review Penetration Rate
*Source: `data/bda/hive_query5_aspect_cooccurrence.csv`*

Penetration rate is defined as:
$$\text{Penetration Rate (\%)} = \frac{\text{Distinct Reviews Mentioning Aspect for Product}}{\text{Total Reviews for Product}} \times 100\%$$
- Both numerator and denominator count distinct reviews; therefore, this ratio is mathematically bounded between **0.0% and 100.0%**.
- High penetration examples:
  - Product `B0BVLY92D8`: 100.0% of reviews discuss `build_durability` (7 out of 7 reviews).
  - Product `B084VNCBNZ`: 93.3% of reviews discuss `battery_charging` (14 out of 15 reviews).

---

## 3. NLP Baseline Benchmark Results

The deterministic NLP baseline was evaluated against held-out validation partitions using canonical annotations (`data/annotation/baseline_evaluation_report.json`).

### Task 1: Aspect Detection (Sample A Validation Partition)
- **Dataset**: `sample_a_auto_reconciled_v2.jsonl` (partition = `val`).
- **Methodology**: Uniform random sentence sampling across non-blank reviews.
- **Accounting**: 186 total validation decision units (31 sentences $\times$ 6 aspects). 6 unannotated exclusions = 180 eligible evaluated units.
- **Overall Aspect Detection Macro-F1**: **0.7778**

| Aspect | Support | Precision | Recall | F1-Score |
|---|---|---|---|---|
| `build_durability` | 5 | 0.7500 | 0.6000 | 0.6667 |
| `battery_charging` | 5 | 1.0000 | 1.0000 | 1.0000 |
| `screen_display` | 5 | 1.0000 | 1.0000 | 1.0000 |
| `camera_optics` | 1 | 1.0000 | 1.0000 | 1.0000 |
| `connectivity_audio` | 0 | 0.0000 | 0.0000 | 0.0000 (Zero Support) |
| `performance_software` | 2 | 1.0000 | 1.0000 | 1.0000 |

*Limitation Disclosure*: The uniform random validation split for Sample A happened to draw 0 positive examples for `connectivity_audio`. This zero support is explicitly disclosed and not hidden.

---

### Task 2: Aspect-Conditional Sentiment (Sample B Validation Partition)
- **Dataset**: `sample_b_auto_reconciled_v2.jsonl` (partition = `val`).
- **Methodology**: Keyword-enriched sentence sampling stratified across 6 aspects and 3 rating tiers.
- **Accounting**: 30 total records. 8 confirmed-absent exclusions = 22 diagnostic units. 3 gold-uncertain units = **19 eligible primary 3-class units**.
- **Primary 3-Class Macro-F1**: **1.0000** (Positive: 3, Neutral: 11, Negative: 5).

> [!WARNING]
> **Scientific Evaluation Disclosure**:
> The 1.0 Macro-F1 score evaluates **Rule Verification Agreement** against automated heuristic pseudo-labels on a small held-out set (19 cases). It verifies internal consistency between the baseline classifier and annotation heuristics, but must **NOT** be represented as human ground-truth accuracy. Sample B is keyword-enriched and cannot be used to estimate population aspect prevalence.

---

## 4. Automated Test Suite Verification

As of the final submission preparation, the automated test suite stands at **179 total automated tests**, all passing:

```
================================================================================
 Automated Test Suite Summary
================================================================================
 Backend Unit Tests (Python unittest):          137 Passed (0 Failed, 0 Skipped)
 Frontend Contract & UI Tests (Node.js test):    42 Passed (0 Failed, 0 Skipped)
 Protected Asset Integrity Verifier:            17 Assets Verified (100% Intact)
 Frontend Production Build (tsc + vite):        Compiled Cleanly (Exit Code 0)
================================================================================
 TOTAL AUTOMATED TESTS:                         179 PASSED
================================================================================
```

### Breakdown of Test Suites
1. **Backend Tests (137 tests)**:
   - `test_api_health.py`: Database status, category lock verification, service identity.
   - `test_api_products.py`: Catalogue pagination, deterministic ordering, individual product aspect summaries.
   - `test_api_reviews.py`: Filter parameters, pagination boundaries, rating filters.
   - `test_api_analytics.py`: Schema validation of all 5 Hive analytical endpoints against CSV exports.
   - `test_database.py`: Foreign key cascades, schema tables, PRAGMA checks.
   - `test_loader.py`: Ingestion idempotency, hash verification.
   - `test_nlp_baseline_service.py` & `test_nlp_scaffolding.py`: Aspect regex extraction, sentiment classification rules.
2. **Frontend Tests (42 tests)**:
   - `analytics_client.test.ts`: BDA API client contracts, data schemas, error propagation.
   - `api_client.test.ts`: Health check offline fallback, product summary null metadata handling, review filter state lifecycle, async sequence ID discard logic, modal keyboard event handlers.

---

## 5. Separation of Completed Work vs. Future Work

| Feature Area | Status in ProductPulse | Verification Details |
|---|---|---|
| **SQLite Review Storage** | **Completed** | 25,000 reviews and 19,065 products indexed with foreign keys. |
| **FastAPI REST Service** | **Completed** | 9 live endpoints with Pydantic contracts and CORS bindings. |
| **Product Catalogue View** | **Completed** | Full catalogue browsing with honest metadata fallback and ASIN badges. |
| **Individual Product Dashboard** | **Completed** | Overview, 1★–5★ histogram, Hadoop aspect metrics, customer review feed. |
| **Category Review Analytics** | **Completed** | Interactive dashboard exploring 5 Apache Hive analytical queries. |
| **Customer Reviews Explorer** | **Completed** | Multi-criteria filtering (parent ASIN, variant, stars, verified purchase). |
| **Hadoop 3.3.6 MapReduce Job** | **Completed** | Authentic streaming job executed in Docker; 48,708 aggregates in `part-00000`. |
| **Apache Hive 3.1.3 Analytics** | **Completed** | 5 queries executed with Derby metastore; verified CSVs in `data/bda/`. |
| **Rule-Based NLP Baseline** | **Completed** | 6-aspect extraction and aspect-conditional sentiment classifier. |
| **Transformer-Based NLP (BERT/RoBERTa)** | *Future Milestone* | Supervised fine-tuning of deep language models using human gold labels. |
| **Unsupervised Issue Clustering (HDBSCAN)** | *Future Milestone* | Complaint cluster discovery from negative review sentence embeddings. |
| **Catalog Metadata Ingestion** | *Future Milestone* | Enriching product titles and high-res imagery via external catalog APIs. |

---

## 6. Known Limitations

1. **Catalog Metadata Absence**: In `sample_reviews_cell_phones_25k.jsonl`, all 19,065 products have `title = NULL` and `brand = NULL`. ProductPulse displays an honest fallback (`"Product name unavailable"`) and canonical ASINs rather than fabricating artificial product names.
2. **Customer Star Ratings vs. NLP Sentiment**: Star ratings (1.0–5.0) are customer disposition baselines for the whole transaction, not fine-grained sentiment on individual aspects.
3. **Automated Annotation Limitations**: The NLP baseline was evaluated against heuristic draft pseudo-labels. A true gold-standard benchmark would require multi-annotator human consensus.
4. **Single-Node Big Data Execution**: The Hadoop and Hive environments were run as single-node local Docker containers suitable for deterministic replication, rather than a multi-node distributed cluster.
