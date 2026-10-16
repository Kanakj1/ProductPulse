-- ProductPulse Analytical Serving Database Schema (Tier 1 Core DDL)
-- Database Engine: SQLite 3.35+
-- Foreign Keys MUST be enabled: PRAGMA foreign_keys = ON;

PRAGMA foreign_keys = ON;

--------------------------------------------------------------------------------
-- 1. INGESTION RUNS (Audit & Provenance Table)
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id TEXT PRIMARY KEY,
    manifest_version TEXT NOT NULL DEFAULT '1.0',
    dataset_name TEXT NOT NULL,
    category TEXT NOT NULL,
    source_url TEXT NOT NULL,
    target_records INTEGER NOT NULL,
    max_body_bytes_cap INTEGER NOT NULL,
    cumulative_timeout_seconds REAL NOT NULL,
    final_status INTEGER NOT NULL,
    content_range TEXT NOT NULL,
    total_bytes_streamed INTEGER NOT NULL,
    admitted_records_count INTEGER NOT NULL,
    total_lines_processed INTEGER NOT NULL,
    trailing_incomplete_bytes INTEGER NOT NULL,
    parse_errors_count INTEGER NOT NULL,
    validation_errors_count INTEGER NOT NULL,
    duplicates_count INTEGER NOT NULL,
    unique_parent_asins_count INTEGER NOT NULL,
    unique_asins_count INTEGER NOT NULL,
    unique_users_count INTEGER NOT NULL,
    raw_jsonl_path TEXT NOT NULL,
    raw_jsonl_bytes INTEGER NOT NULL,
    raw_jsonl_sha256 TEXT NOT NULL,
    manifest_path TEXT NOT NULL,
    start_utc TEXT NOT NULL,
    end_utc TEXT NOT NULL,
    elapsed_seconds REAL NOT NULL,
    sampling_nature TEXT NOT NULL,
    population_claims_allowed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

--------------------------------------------------------------------------------
-- 2. PRODUCTS (Parent ASIN Entity - Grouping Reviews)
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    parent_asin TEXT PRIMARY KEY,
    title TEXT,                         -- NULL until metadata is ingested
    brand TEXT,                         -- NULL until metadata is ingested
    price REAL,                         -- NULL until metadata is ingested
    main_category TEXT DEFAULT 'Cell_Phones_and_Accessories',
    has_metadata INTEGER NOT NULL DEFAULT 0 CHECK (has_metadata IN (0, 1)),
    first_seen_run_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (first_seen_run_id) REFERENCES ingestion_runs(run_id) ON DELETE RESTRICT
);

--------------------------------------------------------------------------------
-- 3. PRODUCT VARIANTS (Specific SKU ASINs)
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS product_variants (
    asin TEXT PRIMARY KEY,
    parent_asin TEXT NOT NULL,
    first_seen_run_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (parent_asin) REFERENCES products(parent_asin) ON DELETE CASCADE,
    FOREIGN KEY (first_seen_run_id) REFERENCES ingestion_runs(run_id) ON DELETE RESTRICT,
    UNIQUE (asin, parent_asin)          -- Target for composite foreign key from reviews
);

--------------------------------------------------------------------------------
-- 4. REVIEWS (Authentic Review Records & Provenance)
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reviews (
    review_id TEXT PRIMARY KEY,         -- Deterministic SHA256 or <hash>_#<N>
    canonical_hash TEXT NOT NULL,       -- Raw SHA256 of canonical JSON
    occurrence_index INTEGER NOT NULL DEFAULT 0,
    parent_asin TEXT NOT NULL,
    asin TEXT NOT NULL,
    user_id TEXT NOT NULL,
    rating REAL NOT NULL CHECK (rating >= 1.0 AND rating <= 5.0),
    raw_title TEXT,
    raw_text TEXT,
    timestamp_raw INTEGER NOT NULL,     -- Unix epoch milliseconds (exact source integer)
    review_timestamp_utc TEXT NOT NULL, -- Full-precision ISO-8601 UTC string (YYYY-MM-DDTHH:MM:SS.sssZ)
    review_epoch_seconds REAL NOT NULL, -- Unix epoch seconds with millisecond decimals
    helpful_vote INTEGER NOT NULL DEFAULT 0 CHECK (helpful_vote >= 0),
    verified_purchase INTEGER NOT NULL CHECK (verified_purchase IN (0, 1)),
    raw_images_json TEXT NOT NULL DEFAULT '[]',
    has_images INTEGER NOT NULL DEFAULT 0 CHECK (has_images IN (0, 1)),
    is_blank_text INTEGER NOT NULL DEFAULT 0 CHECK (is_blank_text IN (0, 1)),
    source_line_number INTEGER NOT NULL,
    source_byte_offset INTEGER NOT NULL,
    source_byte_length INTEGER NOT NULL,
    ingestion_run_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    -- Composite FK: Enforces that asin and parent_asin match the exact pair in product_variants
    FOREIGN KEY (asin, parent_asin) REFERENCES product_variants(asin, parent_asin) ON DELETE RESTRICT,
    -- Direct Product FK: Explicit defense-in-depth link to catalog products
    FOREIGN KEY (parent_asin) REFERENCES products(parent_asin) ON DELETE RESTRICT,
    FOREIGN KEY (ingestion_run_id) REFERENCES ingestion_runs(run_id) ON DELETE RESTRICT
);

--------------------------------------------------------------------------------
-- CORE INDEXES (Serving Query Optimization)
--------------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_reviews_parent_asin_date 
ON reviews (parent_asin, review_epoch_seconds DESC);

CREATE INDEX IF NOT EXISTS idx_reviews_parent_asin_rating 
ON reviews (parent_asin, rating);

CREATE INDEX IF NOT EXISTS idx_product_variants_parent 
ON product_variants (parent_asin);

CREATE INDEX IF NOT EXISTS idx_reviews_user_id 
ON reviews (user_id);

CREATE INDEX IF NOT EXISTS idx_reviews_has_images 
ON reviews (parent_asin, has_images) WHERE has_images = 1;
