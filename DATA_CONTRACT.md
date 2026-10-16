# ProductPulse — Data Contract & Integrity Specification (`DATA_CONTRACT.md`)

> **PERMANENT CATEGORY LOCK NOTICE**  
> Authorized Category: **Mobile Phones & Accessories**  
> Permitted Source Dataset: **McAuley-Lab/Amazon-Reviews-2023** (Hugging Face)  
> All records outside this domain or originating from unofficial sources are strictly rejected.

---

## 1. Provenance and Ingestion Principles

1. **Source Immutability**: Raw files retrieved from Hugging Face must remain untouched in `data/raw/` with verifiable SHA-256 checksums and access timestamps.
2. **Provisional vs. Verified Status**: In Phase 0, all source field names and joins are **Provisional**. They become **Verified** only after Phase 1 inspects the actual dataset schema and records.
3. **No Fabricated Records**: Under no circumstances will mock ASINs, fake reviews, artificial star ratings, or synthetic timestamps be injected.
4. **Transparent Filtering**: Every dropped, truncated, or malformed record must be recorded in an ingestion manifest with an explicit drop reason.
5. **Denominators and Counts**:
   - Total source reviews vs. locally ingested reviews must be recorded separately.
   - Distinct review counts must never be confused with extracted aspect or complaint snippet counts.

---

## 2. Entity Specifications

### 2.1 Products (`products`)
Stores verified product metadata belonging strictly to *Mobile Phones & Accessories*.

| Field Name | Type | Status | Nullable | Description & Constraints |
| :--- | :--- | :--- | :--- | :--- |
| `product_id` | TEXT | Local Final | NO | Primary Key. Derived from verified source identifier (`parent_asin` or `asin`). |
| `source_asin` | TEXT | Provisional | NO | Direct ASIN from source record. |
| `parent_asin` | TEXT | Provisional | YES | Parent ASIN grouping variants (if provided by source). |
| `title` | TEXT | Provisional | NO | Cleaned product title. Must not be empty. |
| `brand` | TEXT | Provisional | YES | Verified brand name. Fallback: "Unknown Brand". |
| `main_category` | TEXT | Provisional | NO | Must match "Mobile Phones & Accessories" filter rule. |
| `categories` | JSON/TEXT | Provisional | YES | Hierarchical category breadcrumb list. |
| `price` | REAL | Provisional | YES | Numerical price in USD if available. Null if unlisted. |
| `average_rating` | REAL | Provisional | YES | Pre-computed source rating or calculated baseline. Range: 1.0 - 5.0. |
| `rating_number` | INTEGER | Provisional | YES | Total number of ratings reported by Amazon source. |
| `primary_image_url` | TEXT | Provisional | YES | Verified high-res image link from source metadata. |
| `has_valid_image` | BOOLEAN | Local Final | NO | True if image URL was validated; False triggers frontend fallback. |
| `created_at` | TIMESTAMP | Local Final | NO | Timestamp when record was ingested locally. |

---

### 2.2 Reviews (`reviews`)
Stores authentic customer review text and metadata.

| Field Name | Type | Status | Nullable | Description & Constraints |
| :--- | :--- | :--- | :--- | :--- |
| `review_id` | TEXT | Local Final | NO | Primary Key. Deterministic hash if upstream lacks a unique review ID. |
| `product_id` | TEXT | Local Final | NO | Foreign Key -> `products.product_id`. |
| `user_id` | TEXT | Provisional | YES | Anonymized user hash from source. PII must never be stored or displayed. |
| `rating` | REAL | Provisional | NO | Rating given by user (1.0 to 5.0). *Not ground-truth aspect sentiment.* |
| `title` | TEXT | Provisional | YES | Review summary/headline. |
| `text` | TEXT | Provisional | NO | Full body of the customer review. Must not be empty. |
| `timestamp_raw` | BIGINT | Provisional | NO | Raw timestamp from source (epoch ms or s). |
| `review_date` | DATE | Local Final | YES | Validated UTC ISO-8601 date parsed from `timestamp_raw`. |
| `helpful_vote` | INTEGER | Provisional | YES | Helpful vote count if available. Defaults to 0. |
| `verified_purchase` | BOOLEAN | Provisional | YES | Whether purchase was verified by Amazon. |
| `is_valid_timestamp` | BOOLEAN | Local Final | NO | True if timestamp falls within realistic range (1998-2024). |

---

### 2.3 Image References (`product_images`)
Stores image URLs associated with a product.

| Field Name | Type | Status | Nullable | Description & Constraints |
| :--- | :--- | :--- | :--- | :--- |
| `image_id` | TEXT | Local Final | NO | Primary Key. Local hash of `product_id` + image URL. |
| `product_id` | TEXT | Local Final | NO | Foreign Key -> `products.product_id`. |
| `raw_url` | TEXT | Provisional | NO | Original URL extracted from source metadata. |
| `variant_type` | TEXT | Local Final | YES | "large", "thumb", "hi-res" if specified. |
| `is_accessible` | BOOLEAN | Local Final | NO | Checked status. Defaults to False until verified. |

---

### 2.4 Sentiment Predictions (`sentiment_predictions`)
Stores model-generated overall sentiment classifications.

| Field Name | Type | Status | Nullable | Description & Constraints |
| :--- | :--- | :--- | :--- | :--- |
| `prediction_id` | TEXT | Local Final | NO | Primary Key. Local UUID or hash. |
| `review_id` | TEXT | Local Final | NO | Foreign Key -> `reviews.review_id`. |
| `predicted_sentiment` | TEXT | Local Final | NO | "positive", "neutral", or "negative". |
| `confidence_score` | REAL | Local Final | NO | Classifier probability or decision score ($0.0 \le s \le 1.0$). |
| `model_version` | TEXT | Local Final | NO | Semantic version string of model (e.g., `tfidf_logreg_v1.0`). |
| `run_id` | TEXT | Local Final | NO | Foreign Key -> `processing_runs.run_id`. |

---

### 2.5 Aspect Mentions & Sentiment (`aspect_evidence`)
Stores sentence-level aspect detections and their granular sentiments.

| Field Name | Type | Status | Nullable | Description & Constraints |
| :--- | :--- | :--- | :--- | :--- |
| `evidence_id` | TEXT | Local Final | NO | Primary Key. Local UUID. |
| `review_id` | TEXT | Local Final | NO | Foreign Key -> `reviews.review_id`. |
| `product_id` | TEXT | Local Final | NO | Foreign Key -> `products.product_id`. |
| `aspect_name` | TEXT | Local Final | NO | Target aspect: "battery", "camera", "display", "performance", "build_quality", "connectivity", "charging", "software". |
| `sentence_text` | TEXT | Local Final | NO | Exact unedited sentence extracted from review containing the mention. |
| `aspect_sentiment` | TEXT | Local Final | NO | "positive", "neutral", or "negative". |
| `polarity_score` | REAL | Local Final | YES | Continuous sentiment score if calculated. |
| `rule_or_model` | TEXT | Local Final | NO | Reference to aspect rule/dictionary identifier. |

---

### 2.6 Complaint Themes (`complaint_clusters`)
Stores aggregated recurring customer complaint themes.

| Field Name | Type | Status | Nullable | Description & Constraints |
| :--- | :--- | :--- | :--- | :--- |
| `cluster_id` | TEXT | Local Final | NO | Primary Key. |
| `product_id` | TEXT | Local Final | NO | Foreign Key -> `products.product_id`. |
| `theme_title` | TEXT | Local Final | NO | Human-readable label (e.g., "Rapid Battery Drain", "Camera Autofocus Failure"). |
| `aspect_name` | TEXT | Local Final | NO | Associated aspect. |
| `distinct_reviews_count` | INTEGER | Local Final | NO | Number of *unique reviews* expressing this complaint. |
| `snippet_count` | INTEGER | Local Final | NO | Total number of extracted evidence snippets. |
| `representative_snippet` | TEXT | Local Final | NO | Top-ranking authentic review snippet for UI preview. |

---

### 2.7 Aggregated Analytics (`product_analytics_summary`)
Pre-computed batch metrics serving high-performance API reads.

| Field Name | Type | Status | Nullable | Description & Constraints |
| :--- | :--- | :--- | :--- | :--- |
| `product_id` | TEXT | Local Final | NO | Primary Key. Foreign Key -> `products.product_id`. |
| `total_reviews` | INTEGER | Local Final | NO | Total valid reviews ingested for this product. |
| `positive_review_count` | INTEGER | Local Final | NO | Count of reviews classified as positive. |
| `negative_review_count` | INTEGER | Local Final | NO | Count of reviews classified as negative. |
| `neutral_review_count` | INTEGER | Local Final | NO | Count of reviews classified as neutral. |
| `positive_percentage` | REAL | Local Final | NO | Denominator = `total_reviews`. |
| `negative_percentage` | REAL | Local Final | NO | Denominator = `total_reviews`. |
| `neutral_percentage` | REAL | Local Final | NO | Denominator = `total_reviews`. |
| `aspect_breakdown_json` | JSON/TEXT | Local Final | NO | Structured JSON of positive/negative counts per aspect. |
| `computed_by` | TEXT | Local Final | NO | "HADOOP_MAPREDUCE", "HIVE_BATCH", or "SQLITE_BASELINE". |
| `last_updated` | TIMESTAMP | Local Final | NO | Processing timestamp. |

---

### 2.8 Processing Runs & Manifests (`processing_runs`)
Stores metadata about every batch extraction, NLP run, or ingestion job for reproducibility.

| Field Name | Type | Status | Nullable | Description & Constraints |
| :--- | :--- | :--- | :--- | :--- |
| `run_id` | TEXT | Local Final | NO | Primary Key. Unique execution identifier. |
| `pipeline_step` | TEXT | Local Final | NO | e.g., "ingestion", "sentiment_baseline", "mapreduce_batch". |
| `source_dataset` | TEXT | Local Final | NO | Fixed: "McAuley-Lab/Amazon-Reviews-2023". |
| `source_split` | TEXT | Provisional | NO | Subset name verified in Phase 1. |
| `records_processed` | INTEGER | Local Final | NO | Total rows read. |
| `records_admitted` | INTEGER | Local Final | NO | Total valid rows stored. |
| `records_rejected` | INTEGER | Local Final | NO | Total dropped due to schema/category violations. |
| `execution_time_sec` | REAL | Local Final | NO | Runtime in seconds. |
| `run_timestamp` | TIMESTAMP | Local Final | NO | UTC execution start time. |

---

## 3. Data Integrity & Validation Rules

1. **Deterministic Primary Key Generation for Reviews**:
   If upstream source lacks a unique review ID:
   $$\text{review\_id} = \text{SHA256}(\text{parent\_asin} \parallel \text{user\_id} \parallel \text{timestamp\_raw} \parallel \text{text\_first\_50\_chars})$$
   A uniqueness collision test must be executed on any ingested batch.
2. **Timestamp Verification**:
   - Upstream timestamps must be inspected for unit (seconds vs. milliseconds).
   - Valid epoch range: Between Jan 1, 1998 ($883612800$) and Dec 31, 2024 ($1735689600$).
   - Records with negative, zero, or future timestamps must have `is_valid_timestamp = False` and be excluded from historical trend aggregation.
3. **Rating Range Validation**:
   - Ratings must strictly satisfy $1.0 \le \text{rating} \le 5.0$.
4. **Text Integrity**:
   - Whitespace must be trimmed.
   - Reviews with empty or null body text must be rejected.
   - Reviews are treated strictly as unformatted text data, never executed as code or instructions.
5. **Deduplication**:
   - Duplicate $(\text{product\_id}, \text{user\_id}, \text{timestamp})$ tuples are logged and only the first admitted instance retained.
