# ProductPulse — Phase 1 Feasibility & Category Verification Report (`PHASE_1_FEASIBILITY_REPORT.md`)

**Date of Verification**: 2026-10-14  
**Workspace**: `D:\ProductPulse-nlp-bda`  
**Phase Status**: Phase 1 Authorized Investigation Only (No data downloaded, no packages installed, no application code implemented)  
**Permanent Category Lock**: **Mobile Phones & Accessories Only**  
**Sole Authorized Data Source**: `McAuley-Lab/Amazon-Reviews-2023` (Hugging Face)  

---

## 1. Phase and Authorization Status

- **Phase Objective**: Investigate official repository metadata, configuration schemas, and category mapping for `McAuley-Lab/Amazon-Reviews-2023` to establish whether *Mobile Phones & Accessories* can be accessed in a bounded, academically defensible manner without full-dataset downloads.
- **Authorization Boundary**: Phase 1 is authorized for metadata inspection and public documentation analysis only. No review records or product metadata were downloaded, cached, streamed, or ingested. No dependencies were installed, no services were started, and the Phase 0 foundational documents were preserved without modification.

---

## 2. Permanent Category Lock and Sole Data Source

> **MANDATORY PROJECT-WIDE GOVERNANCE**  
> 1. **Exclusive Category**: **Mobile Phones & Accessories Only**.  
>    Broader categories (e.g., `Electronics`) or adjacent categories (e.g., `Computers`, `Office_Products`) are strictly prohibited as primary substitutes.  
> 2. **Sole Authorized Dataset**: `McAuley-Lab/Amazon-Reviews-2023`, hosted on Hugging Face.  
>    No web scraping, synthetic records, external mirrors, or substitute review corpora are permitted.

---

## 3. Official Sources Consulted

The following official primary sources were consulted using read-only HTTP metadata requests and documentation views on 2026-10-14:

1. **Official Dataset Project Site**:
   - URL: `https://amazon-reviews-2023.github.io/`
   - Subpages: `https://amazon-reviews-2023.github.io/main.html`, `https://amazon-reviews-2023.github.io/data_loading/huggingface.html`
2. **Official Hugging Face Dataset Repository**:
   - URL: `https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023`
   - Raw README: `https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/raw/main/README.md`
   - Repository API: `https://huggingface.co/api/datasets/McAuley-Lab/Amazon-Reviews-2023`
   - File Tree API: `https://huggingface.co/api/datasets/McAuley-Lab/Amazon-Reviews-2023/tree/main`
   - Loader Script: `https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/raw/main/Amazon-Reviews-2023.py`
   - Category List: `https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/raw/main/all_categories.txt`
3. **Official HTTP Endpoints (HEAD Metadata Inspection Only)**:
   - Review File: `https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/main/raw/review_categories/Cell_Phones_and_Accessories.jsonl`
   - Meta File: `https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/main/raw/meta_categories/meta_Cell_Phones_and_Accessories.jsonl`
   - Parquet Shard: `https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/main/raw_meta_Cell_Phones_and_Accessories/full-00000-of-00007.parquet`

---

## 4. Verified Category Taxonomy and Mapping

### 4.1 Official Category Name & Taxonomy Findings
- **Observed Category Identifier**: `Cell_Phones_and_Accessories` `[DIRECTLY OBSERVED METADATA]`
- **Evidence in `all_categories.txt`**:
  Line 11 of `all_categories.txt` contains exactly:
  ```text
  Cell_Phones_and_Accessories
  ```
  `all_categories.txt` defines 33 distinct product categories plus "Unknown". `[DIRECTLY OBSERVED METADATA]`
- **Separation from Broader Categories**:
  Line 15 of `all_categories.txt` lists `Electronics` as an entirely separate top-level category. `Cell_Phones_and_Accessories` is **not** nested inside `Electronics` or subordinate to it in the dataset's category taxonomy. They exist as separate configurations and files. `[DIRECTLY OBSERVED METADATA]`
- **Domain Scope in Amazon Taxonomy**:
  In Amazon's standard retail taxonomy, *Cell Phones & Accessories* encompasses mobile handsets (unlocked, carrier-locked, smartphones, basic feature phones) as well as direct mobile accessories (cases, screen protectors, wall chargers, wireless charging pads, cables, car mounts, power banks). `[DOCUMENTED FACT]`
- **Mapping to ProductPulse Requirement**:
  The project requirement is **Mobile Phones & Accessories**. The official dataset partition is **`Cell_Phones_and_Accessories`**. This represents a direct 1-to-1 canonical taxonomy match (standard American English "Cell" vs. "Mobile"). `[INFERENCE / CANONICAL TAXONOMY MATCH]`

### 4.2 Official Category Statistics
From the official dataset table published in the official README and documentation:

| Category | # Users | # Items | # Reviews / Ratings | # Review Tokens | # Meta Tokens | Evidence Classification |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`Cell_Phones_and_Accessories`** | 11.6 Million | 1.3 Million | 20.8 Million | 935.4 Million | 1.3 Billion | `[DOCUMENTED FACT]` |

---

## 5. Repository Configuration and File Inventory

### 5.1 Remote Directory Structure
Inspection of `https://huggingface.co/api/datasets/McAuley-Lab/Amazon-Reviews-2023/tree/main` revealed the following top-level layout: `[DIRECTLY OBSERVED METADATA]`

```
McAuley-Lab/Amazon-Reviews-2023/
├── .gitattributes
├── Amazon-Reviews-2023.py       # Custom dataset loader script (39,620 bytes)
├── README.md                    # Dataset card & metadata (30,343 bytes)
├── all_categories.txt           # 34 taxonomy category names (585 bytes)
├── asin2category.json           # Parent ASIN to category map (1,246,846,569 bytes)
├── raw/
│   ├── review_categories/       # Raw uncompressed JSONL review files per category
│   └── meta_categories/         # Raw uncompressed JSONL metadata files per category
├── raw_meta_Cell_Phones_and_Accessories/  # Parquet shards (7 shards)
└── benchmark/                   # Preprocessed recommendation benchmark CSVs (0core, 5core)
```

### 5.2 Exact Target Files for Mobile Phones & Accessories

| Purpose | Exact Remote File Path | File Format | Remote Content Length | Git LFS OID (SHA-256) | Remote HTTP ETag |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **Reviews** | `raw/review_categories/Cell_Phones_and_Accessories.jsonl` | JSONL | 9,342,568,048 bytes (~9.34 GB / 8.70 GiB) | `bda42ca8d28a1e57db970c78703b7aaac9c9beb6595e1be00364a0a55a682cd5` | `"7ed72d79a1973b1da28738cbb97114ada55aef0f37137ee0dd0c9f8d5f2a1304"` |
| **Metadata** | `raw/meta_categories/meta_Cell_Phones_and_Accessories.jsonl` | JSONL | 4,015,159,840 bytes (~4.02 GB / 3.74 GiB) | `f8f411a2e3a90560de4b18a0c2c885a4ba410bb26f965a8e7290080898d22688` | `"124151b753f7f457585f69666f7f2b18-479"` |
| **Metadata (Parquet)** | `raw_meta_Cell_Phones_and_Accessories/full-00000-of-00007.parquet` through `full-00006-of-00007.parquet` | Parquet | 1,262,072,469 bytes total (~1.26 GB across 7 shards) | Observed in repository file tree | Varies per shard |

### 5.3 Critical Distinctions Among File Identifiers and Checksums
To prevent conflating distinct cryptographic and transport identifiers:
1. **Git LFS Object Identifier (OID)**: A SHA-256 hash of the pointed LFS object payload as tracked in the Git repository metadata (e.g., `bda42ca8...` for the review file). Sourced directly from the Hugging Face Tree API. `[DIRECTLY OBSERVED METADATA]`
2. **HTTP Entity Tag (ETag)**: A cache validator string emitted in the HTTP response headers by Amazon CloudFront (e.g., `"7ed72d79..."` or `"124151b7...-479"`). On AWS S3/CloudFront, multi-part uploads yield composite hashes that do **not** equal a standard SHA-256 file checksum. Sourced from HTTP HEAD response headers. `[DIRECTLY OBSERVED METADATA]`
3. **Local File SHA-256 Checksum**: The cryptographic SHA-256 hash computed over raw file bytes saved to local disk. This hash can only be computed locally once a file is actually downloaded and verified. It is not currently available because zero data bytes have been downloaded. `[UNVERIFIED UNTIL DOWNLOAD]`
4. **Non-Interchangeability Rule**: Git LFS OIDs, HTTP ETags, and local file SHA-256 checksums must never be treated as equivalent or substituted for one another in data manifests or validation routines. `[DOCUMENTED RULE]`

---

## 6. Review and Product-Metadata Schema Findings

> **Methodological Boundary Note on Schema Definitions vs. Record-Level Nullability**:  
> The schemas below represent documented field specifications and types published in the official README and documentation (`[DOCUMENTED FACT]`). Whether specific fields (such as `title`, `images`, `features`, `description`, `price`, or `helpful_vote`) are populated, set to `null`, stored as empty strings (`""`), stored as empty lists (`[]`), or omitted entirely in individual JSONL lines is an empirical property of the data records. This record-level nullability cannot be measured or guaranteed without reading actual record payloads. `[UNVERIFIED UNTIL INGESTION]`

### 6.1 User Reviews Schema (`raw_review_Cell_Phones_and_Accessories`)

| Field Name | Documented Type | Documented Definition Status | Join Suitability | Observed Description & Nullability Caveats | Evidence Classification |
| :--- | :---: | :---: | :---: | :--- | :---: |
| `rating` | float | Documented Field | Not a join key | Rating from 1.0 to 5.0. | `[DOCUMENTED FACT]` |
| `title` | string | Documented Field | Not a join key | Review summary headline. Record-level nullability/empty string unverified. | `[DOCUMENTED FACT]` / `[EMPIRICALLY UNVERIFIED]` |
| `text` | string | Documented Field | Not a join key | Main review body. May be empty string for rating-only entries; record-level nullability unverified. | `[DOCUMENTED FACT]` / `[EMPIRICALLY UNVERIFIED]` |
| `images` | list of dicts | Documented Field | Not a join key | Images posted by reviewer (`small_image_url`, `medium_image_url`, `large_image_url`). Frequently empty list `[]`. | `[DOCUMENTED FACT]` / `[EMPIRICALLY UNVERIFIED]` |
| `asin` | string | Documented Field | Variant key | Specific product variant SKU purchased (e.g., specific color/storage). | `[DOCUMENTED FACT]` |
| `parent_asin` | string | Documented Field | **PRIMARY JOIN KEY** | Parent product ID grouping all color/storage variants. | `[DOCUMENTED FACT]` |
| `user_id` | string | Documented Field | Provenance key | Anonymized alphanumeric reviewer hash. | `[DOCUMENTED FACT]` |
| `timestamp` | integer | Documented Field | Temporal key | Documented as "Unix time of the review". Millisecond unit (13 digits) is inferred from examples. | `[DOCUMENTED FACT]` (unit is `[INFERENCE]`) |
| `helpful_vote`| integer | Documented Field | Metric | Count of helpful votes; non-negative integer. Record nullability unverified. | `[DOCUMENTED FACT]` / `[EMPIRICALLY UNVERIFIED]` |
| `verified_purchase` | boolean | Documented Field | Quality filter | True if Amazon confirmed purchase; False otherwise. | `[DOCUMENTED FACT]` |

### 6.2 Product Metadata Schema (`raw_meta_Cell_Phones_and_Accessories`)

| Field Name | Documented Type | Documented Definition Status | Join Suitability | Observed Description & Nullability Caveats | Evidence Classification |
| :--- | :---: | :---: | :---: | :--- | :---: |
| `parent_asin` | string | Documented Field | **PRIMARY KEY** | Unique parent product identifier. Matches review `parent_asin`. | `[DOCUMENTED FACT]` |
| `main_category`| string | Documented Field | Category filter | Documented domain, e.g., `"Cell Phones & Accessories"`. | `[DOCUMENTED FACT]` |
| `title` | string | Documented Field | Display name | Product title. Empirical nullability in raw records unverified. | `[DOCUMENTED FACT]` / `[EMPIRICALLY UNVERIFIED]` |
| `average_rating`| float | Documented Field | Aggregate metric| Pre-computed star rating on Amazon product page (1.0–5.0). Empirical null rate unverified. | `[DOCUMENTED FACT]` / `[EMPIRICALLY UNVERIFIED]` |
| `rating_number` | integer | Documented Field | Aggregate metric| Total rating count on Amazon product page. Empirical null rate unverified. | `[DOCUMENTED FACT]` / `[EMPIRICALLY UNVERIFIED]` |
| `features` | list of strings | Documented Field | Feature search | Bullet points describing technical specifications. Frequently empty `[]`. | `[DOCUMENTED FACT]` / `[EMPIRICALLY UNVERIFIED]` |
| `description` | list of strings | Documented Field | Feature search | Paragraph descriptions. Frequently empty `[]`. | `[DOCUMENTED FACT]` / `[EMPIRICALLY UNVERIFIED]` |
| `price` | string / float | Documented Field | Filter/Display | Documented inconsistently as string in YAML and float in table; empirical format unverified. | `[DOCUMENTED FACT]` / `[EMPIRICALLY UNVERIFIED]` |
| `images` | dict of lists | Documented Field | Image gallery | Contains lists: `hi_res`, `large`, `thumb`, `variant`. May contain null elements. | `[DOCUMENTED FACT]` / `[EMPIRICALLY UNVERIFIED]` |
| `videos` | dict of lists | Documented Field | Non-essential | Lists: `title`, `url`, `user_id`. Non-essential for ProductPulse. | `[DOCUMENTED FACT]` / `[EMPIRICALLY UNVERIFIED]` |
| `store` | string | Documented Field | Brand/Store filter| Store or brand name. Empirical null rate unverified. | `[DOCUMENTED FACT]` / `[EMPIRICALLY UNVERIFIED]` |
| `categories` | list of strings | Documented Field | Hierarchy filter | Hierarchical category breadcrumbs (e.g. `["Cell Phones & Accessories", "Unlocked Phones"]`). | `[DOCUMENTED FACT]` / `[EMPIRICALLY UNVERIFIED]` |
| `details` | string / dict | Documented Field | Spec extraction | Technical specifications. Documented as string in JSONL (serialized JSON string). | `[DOCUMENTED FACT]` / `[EMPIRICALLY UNVERIFIED]` |
| `bought_together`| string / list | Documented Field | Recommendation | Recommended bundles. Frequently null in ecommerce corpora. | `[DOCUMENTED FACT]` / `[EMPIRICALLY UNVERIFIED]` |
| `subtitle` | string | Documented Field | Metadata | Book/product subtitle. Frequently null in mobile domain. | `[DOCUMENTED FACT]` / `[EMPIRICALLY UNVERIFIED]` |
| `author` | string | Documented Field | Metadata | Book author. Typically null or omitted in mobile domain. | `[DOCUMENTED FACT]` / `[EMPIRICALLY UNVERIFIED]` |

---

## 7. Identifier and Join Feasibility

### 7.1 Review-to-Product Join Key
- **Official Documentation Finding**:
  In the official documentation table for User Reviews (`main.html` line 701):
  > *"parent_asin: Parent ID of the product. Note: Products with different colors, styles, sizes usually belong to the same parent ID. The 'asin' in previous Amazon datasets is actually parent ID. **Please use parent ID to find product meta.**"* `[DOCUMENTED FACT]`
- **Conclusion**: The primary join between reviews and product metadata is strictly **`parent_asin`**. `[DOCUMENTED FACT]`
- **Variant Handling**: A product model (e.g., "Google Pixel 7") has a single `parent_asin`. Different color/memory combinations share this `parent_asin` while possessing distinct `asin` values. Reviews associated with any variant share the same `parent_asin`. Joining on `parent_asin` correctly aggregates all variant feedback under the unified product page. `[INFERENCE FROM OFFICIAL SPEC]`

### 7.2 Review Primary Key Resolution and Collision Analysis
- **Official Finding**: The raw review schema does **not** include an explicit `review_id` field. `[DOCUMENTED FACT]`
- **Vulnerability of Truncated Prefix Hashing (`text[:50]`)**:
  A candidate hash using only the first 50 characters of review text ($\text{parent\_asin} \parallel \text{user\_id} \parallel \text{timestamp} \parallel \text{text[:50]}$) creates an unacceptably high risk of collision for distinct records:
  1. *Rating-Only Reviews*: Amazon permits rating-only submissions with no review body (`text = ""`). For any rating-only review, `text[:50]` evaluates to an empty string, providing zero textual distinguishing power.
  2. *Boilerplate and Generic Feedback*: Distinct reviews frequently share identical initial phrases (e.g., "Great product, works as expected.", "Five stars! Highly recommend.", "Arrived on time.").
  3. *Batch Submissions*: If a reviewer rates multiple variant purchases within the same millisecond or batch, identical prefixes would collapse distinct records into duplicate keys.
  4. *Information Loss*: Truncating at 50 characters discards the unique body of the review where real differentiating content resides.
- **Preferred Proposal: Canonical JSON Hash of the Entire Source Record**:
  To ensure absolute reproducibility, prevent collision across distinct records, and preserve every original field, the **preferred proposal** is to compute the digest over the **entire parsed source record** using deterministic canonical JSON serialization:
  $$\text{review\_id} = \text{SHA256}(\text{canonical\_json}(\text{full\_source\_record}))$$
  where $\text{canonical\_json}$ serializes all key-value pairs of the complete parsed JSON object (including `parent_asin`, `asin`, `user_id`, `timestamp`, `rating`, `title`, `text`, `images`, `helpful_vote`, `verified_purchase`) with strictly sorted keys and compact, whitespace-free separators (`separators=(',', ':')`). This ensures every source attribute contributes to the hash.
- **Alternative Proposal (Reduced-Field Composite) and Associated Collision Risks**:
  An alternative approach discussed is a reduced-field composite string:
  $$\text{review\_id}_{\text{alt}} = \text{SHA256}(\text{parent\_asin} \parallel \text{asin} \parallel \text{user\_id} \parallel \text{str(timestamp)} \parallel \text{str(rating)} \parallel \text{SHA256(text)} \parallel \text{SHA256(title)})$$
  *Identified Collision Risk for Alternative*: If two distinct source records share identical values for these primary fields but differ in unhashed attributes (such as `helpful_vote`, reviewer `images`, or `verified_purchase` status), this reduced-field composite would generate identical keys, causing an identity collision. Therefore, this formulation is strictly an alternative, and the full canonical record hash remains preferred.
- **Handling of Exact Duplicate Rows and Provenance Preservation**:
  In large scraped or crawled ecommerce datasets, exact byte-for-byte duplicate rows occasionally occur in raw files. If two rows have identical values across all parsed fields (and thus identical canonical hashes):
  1. *Provenance Tracking*: The ingestion pipeline must preserve source traceability by tracking the raw file line number (`source_line_number`) and byte offset.
  2. *Deduplication and Auditing*: Rather than silently dropping records or letting a collision overwrite existing rows, the pipeline will log duplicate occurrences in the ingestion audit manifest (`data/manifests/`), recording the duplicate line index.
  3. *Composite Primary Key*: For local database storage, if both occurrences must be retained for strict source correspondence, an occurrence ordinal (`occurrence_index` $\in \{0, 1, \dots\}$) will be appended to the identifier (`<hash>_#0`, `<hash>_#1`), ensuring 100% collision-free uniqueness while preserving complete provenance.
  *(Note: This design is proposed for Phase 2 evaluation; no hashing code has been implemented and no data ingested or tested in Phase 1.)*

### 7.3 Timestamp Representation
- **Official Documentation Statement**: The schema table in `README.md` and `main.html` lists:
  > `timestamp: Unix time of the review` `[DOCUMENTED FACT]`
- **Unit Inference**: The documentation does **not** state the time unit in prose. However, sample records published in documentation demonstrate 13-digit integers (e.g., `1588687728923` and `1544957102913`). Converting 13 digits to epoch seconds yields year 52,279, whereas dividing by 1000 yields valid timestamps in 2018–2020. Therefore, millisecond precision is an `[INFERENCE FROM SAMPLE VALUES]`.
- **Validation Rule for Ingestion**: Ingestion logic must dynamically inspect the integer magnitude: if `timestamp > 10^11`, divide by $1000.0$ to produce standard epoch seconds; otherwise interpret directly as seconds. `[PROPOSED INGESTION RULE]`

---

## 8. Remote Access, File-Size, and Bounded-Sampling Feasibility

### 8.1 Remote File-Size Verification via Safe HEAD Requests
Using `curl.exe -I` (read-only HEAD requests, zero data payload transferred), remote hosting headers were inspected:

1. **Review File**: `raw/review_categories/Cell_Phones_and_Accessories.jsonl`
   - Response: `HTTP/1.1 302 Found` $\rightarrow$ Redirect to CloudFront signed URL
   - Signed CloudFront HEAD Response:
     - `HTTP/1.1 200 OK`
     - `content-length: 9342568048` ($9.34\text{ GB}$) `[DIRECTLY OBSERVED METADATA]`
     - `accept-ranges: bytes` `[DIRECTLY OBSERVED METADATA]`
     - `etag: "7ed72d79a1973b1da28738cbb97114ada55aef0f37137ee0dd0c9f8d5f2a1304"` `[DIRECTLY OBSERVED METADATA]`
2. **Product Metadata File**: `raw/meta_categories/meta_Cell_Phones_and_Accessories.jsonl`
   - Response: `HTTP/1.1 302 Found` $\rightarrow$ Redirect to CloudFront signed URL
   - Signed CloudFront HEAD Response:
     - `HTTP/1.1 200 OK`
     - `content-length: 4015159840` ($4.02\text{ GB}$) `[DIRECTLY OBSERVED METADATA]`
     - `accept-ranges: bytes` `[DIRECTLY OBSERVED METADATA]`
     - `etag: "124151b753f7f457585f69666f7f2b18-479"` `[DIRECTLY OBSERVED METADATA]`
3. **Parquet Shard 0**: `raw_meta_Cell_Phones_and_Accessories/full-00000-of-00007.parquet`
   - Signed CloudFront HEAD Response:
     - `HTTP/1.1 200 OK`
     - `content-length: 205041738` ($205.04\text{ MB}$) `[DIRECTLY OBSERVED METADATA]`
     - `accept-ranges: bytes` `[DIRECTLY OBSERVED METADATA]`

### 8.2 Bounded Sampling Feasibility via HTTP Range Requests
- **Critical Risk of Standard Loader**:
  Inspection of `Amazon-Reviews-2023.py` (lines 516–527) revealed:
  ```python
  dl_dir = dl_manager.download_and_extract(self.config.data_dir)
  ```
  Calling `load_dataset("McAuley-Lab/Amazon-Reviews-2023", "raw_review_Cell_Phones_and_Accessories")` invokes `download_and_extract()`, which downloads the **entire 9.34 GB review file** before yielding any record. This would violate the project's strict bounding requirement. `[DOCUMENTED CODE BEHAVIOR]`
- **Advertised vs. Tested Range Capability**:
  The CloudFront CDN response explicitly includes the header `accept-ranges: bytes` (`[DIRECTLY OBSERVED METADATA]`). This confirms that the server advertises support for byte-range queries. However:
  > **Important Methodological Distinction**:  
  > An advertised `accept-ranges` header is an indicator of server capability, **not an empirically verified Range payload transfer**. Because downloading review data was strictly prohibited during Phase 1, **no HTTP Range request with payload data was executed, and no `HTTP 206 Partial Content` response body was parsed or tested.**  
  > Consequently, bounded sampling via HTTP Range requests is classified as **CONDITIONALLY FEASIBLE**, explicitly **PENDING A LATER AUTHORIZED RANGE PAYLOAD TEST IN PHASE 2**.
- **Analytical Sample Transfer Budget (Calculated Estimates, Not Empirical Measurements)**:
  - Total Review File Size: $9,342,568,048\text{ bytes}$ `[DIRECTLY OBSERVED METADATA]`
  - Total Reviews in File: $20,800,000\text{ reviews}$ `[DOCUMENTED FACT]`
  - Calculated Mean Review Record Size:
    $$\text{Mean Record Size} = \frac{9,342,568,048\text{ bytes}}{20,800,000\text{ reviews}} \approx 449.16\text{ bytes/review}$$
    *(Note: This is an analytical average across the entire 20.8M dataset, not a measured property of individual records.)*
  - Projected Raw Payload for 500 Reviews:
    $$500 \times 449.16\text{ bytes} \approx 224,580\text{ bytes} \approx 219.3\text{ KB}$$
  - Projected Transfer Budget ($10\times$ buffer for review text variance and line boundary alignment):
    $$\text{Estimated Transfer Budget} = 2\text{ MB to } 5\text{ MB}$$
    *(Note: This 2–5 MB figure is a theoretical projection to guide safety thresholds, not an empirically verified measurement.)*

---

## 9. Storage, Bandwidth, and Transfer Time Estimates

> **Notice on Status of Estimates**:  
> All transfer times and data volumes in the table below are **analytical estimates and projections**, not empirical benchmark measurements.

| Scenario | Estimated Data Transferred | Estimated Local Disk Required | Estimated Transfer Time (at 10 MB/s) | Architectural / Feasibility Status |
| :--- | :---: | :---: | :---: | :--- |
| **Unbounded Ingestion (Full Reviews JSONL)** | 9.34 GB | 9.34 GB | ~16 minutes | **PROHIBITED** without explicit approval. |
| **Unbounded Ingestion (Full Meta JSONL)** | 4.02 GB | 4.02 GB | ~7 minutes | **PROHIBITED** without explicit approval. |
| **Full Parquet Metadata Shards (7 shards)** | 1.26 GB | 1.26 GB | ~2.1 minutes | Exceeds Phase 2 bounded inspection limits. |
| **Single Parquet Metadata Shard (Shard 0)** | 205 MB | 205 MB | ~20 seconds | Feasible fallback if approved, but product overlap unverified. |
| **Bounded Range Ingest: Reviews (500 records)** | **2 MB – 5 MB (estimate)** | **< 1 MB (JSONL)** | **< 1 second (estimate)** | **CONDITIONALLY FEASIBLE** (pending payload test). |
| **Bounded Ingest: Metadata for Review Sample** | **UNRESOLVED** | **UNRESOLVED** | **UNRESOLVED** | **UNRESOLVED ARCHITECTURAL QUESTION** (see Section 9.1). |

### 9.1 Reassessment of Metadata Retrieval for Bounded Review Samples
In earlier preliminary planning, it was tentatively assumed that metadata for the products in a 500-review sample could be retrieved via a simple 2–5 MB range request to `meta_Cell_Phones_and_Accessories.jsonl`. **This assumption is invalid and has been discarded for the following reasons:**
1. *Unindexed 4.02 GB File*: The metadata JSONL file contains ~1.3 million products stored without an external index or byte offset table. Reading the first 2–5 MB of the metadata file will return only the products that happen to reside at the beginning of the file. There is no evidence that these will correspond to the `parent_asin`s appearing in the first 500 reviews.
2. *Unpartitioned Parquet Shards*: The 7 Parquet shards total 1.26 GB (~180 MB each). The official documentation does not state that products are sorted or partitioned by `parent_asin`. Therefore, Parquet Shard 0 cannot be assumed to contain the metadata for products sampled from reviews.
3. *Status*: Retrieving matching metadata for an arbitrary review sample in a strictly bounded manner ($\le 5\text{ MB}$) without an unbounded scan is **UNRESOLVED**. Safe candidate options requiring future authorization are detailed in Section 11.2.

---

## 10. Known Limitations and Unresolved Questions (Tagged UNVERIFIED)

1. **HTTP Range Payload Delivery and Status 206 Behavior**: `UNVERIFIED / PENDING TEST`. While `accept-ranges: bytes` was observed in HEAD headers, no HTTP 206 Partial Content request carrying payload data was executed. Whether CloudFront CDN permits multi-range queries or terminates streaming range connections remains untested.
2. **Bounded Metadata Retrieval for Arbitrary Review `parent_asin`s**: `UNRESOLVED`. The 4.02 GB metadata JSONL file is unindexed. A defensible bounded retrieval mechanism for matching metadata for sampled reviews has not been established and requires an approved strategy.
3. **Record-Level Nullability and Completeness**: `EMPIRICALLY UNVERIFIED`. Schema definitions list documented fields, but the actual proportion of records with null prices, empty descriptions (`[]`), or omitted features in `Cell_Phones_and_Accessories` cannot be determined without reading records.
4. **Individual Review Length Distribution**: `EMPIRICALLY UNVERIFIED`. The calculated 449.16 bytes/review is an analytical mean. Actual record lengths vary significantly. The 2–5 MB transfer budget remains a projection.
5. **Product Overlap Density in Initial Review Stream**: `EMPIRICALLY UNVERIFIED`. Whether the first 500 reviews span 10 products with 50 reviews each or 500 distinct products with 1 review each is unknown until record payloads are inspected.
6. **Image URL Availability & CDN Accessibility**: `EMPIRICALLY UNVERIFIED`. Whether media URLs (`https://m.media-amazon.com/...`) return HTTP 200 or 404/403 cannot be tested without making HTTP requests to image CDNs (prohibited in Phase 1).

---

## 11. Proposed Phase 2 Ingestion Plan (Proposal Only — Not Executed)

### 11.1 Proposed Review Ingestion Steps
1. **Target Review Configuration**: `raw/review_categories/Cell_Phones_and_Accessories.jsonl`
2. **Access Verification (Probe Request)**:
   - Before requesting a multi-megabyte chunk, issue a minimal range probe:
     ```http
     Range: bytes=0-1023
     ```
   - Verify that the server returns `HTTP 206 Partial Content` and that the response contains valid UTF-8 JSON text.
3. **Bounded Sampling Request**:
   - Issue a bounded request (`Range: bytes=0-2097151`, 2 MB).
   - Stream bytes line-by-line, parsing JSON objects.
   - Halt reading immediately upon accumulating **500 valid review records**.
4. **Review Primary Key & Duplicate Handling**:
   - **Preferred Method**: Compute `review_id` using deterministic canonical JSON serialization of the complete parsed source record, preserving every original field:
     $$\text{review\_id} = \text{SHA256}(\text{canonical\_json}(\text{full\_source\_record}))$$
   - **Alternative Method**: A reduced-field composite string ($\text{parent\_asin} \parallel \text{asin} \parallel \text{user\_id} \dots$) is documented strictly as an alternative, noting that it carries potential identity collision risks if unhashed fields differ between records.
   - **Provenance Tracking**: Track `source_line_number` and byte offset for each parsed review.
   - **Duplicate Handling**: In the event of exact duplicate records, record an entry in `data/manifests/` and append an occurrence ordinal (`_#0`, `_#1`) to maintain collision-free uniqueness while preserving complete source line provenance.
5. **Raw Data Preservation & Manifest**:
   - Write raw ingested lines to `data/raw/sample_reviews_cell_phones_500.jsonl`.
   - Calculate the local SHA-256 checksum of the resulting local file.
   - Create `data/manifests/ingestion_manifest_phase2.json` documenting bytes transferred, HTTP status codes, records admitted, records rejected, and elapsed time.

### 11.2 Proposed Metadata Retrieval Options (Pending Future User Approval)
Because an arbitrary review sample cannot be joined against the 4.02 GB unindexed metadata file via naive range requests, the following safe options are presented for user review and approval prior to Phase 2:

- **Option A: Inverted "Metadata-First" Candidate Sampling**:
  - Read candidate products (e.g., $N = 20$ products) from the beginning of `meta_Cell_Phones_and_Accessories.jsonl` using a bounded Range request (2 MB).
  - Stream the 9.34 GB review file via Range requests, filtering for reviews whose `parent_asin` matches one of the $N$ candidate products.
  - *Transfer Uncertainty and Safety Bounds*: While any matched review is guaranteed to have metadata, searching the unindexed 9.34 GB review file for reviews matching a specific subset of products requires an unknown and potentially large amount of data transfer. Scanning until 500 matching reviews are located could require scanning gigabytes across the review file.
  - *Mandatory Guardrails*: To prevent unbounded network transfer, this approach strictly requires explicit, pre-authorized guardrails:
    1. A hard byte-transfer cap (e.g., maximum 10 MB or 20 MB total transferred).
    2. A strict elapsed time ceiling (e.g., 30–60 seconds).
    3. An inspection record limit (e.g., evaluate at most $M$ review lines).
  - *Sampling Consequence*: If any safety limit is reached before accumulating 500 matching reviews, the ingestion stream must halt immediately. Consequently, the resulting sample may end with fewer than 500 reviews.
  - *(Note: No review searches or payload requests were executed in Phase 1.)*
- **Option B: Parquet Remote Column / Row-Group Pruning**:
  - Use `pyarrow.parquet` or DuckDB over HTTP with byte-range support to read only the Parquet file metadata and dictionary pages from `full-00000-of-00007.parquet` through `full-00006-of-00007.parquet`.
  - *Advantage*: Leverages columnar indexing to retrieve metadata for specific `parent_asin`s without downloading entire 180 MB shards.
  - *Requirement*: Requires dependency installation and remote range support verification.
- **Option C: Authorized Single Parquet Shard Download**:
  - Request explicit user approval to download a single compressed Parquet shard (`full-00000-of-00007.parquet`, 205 MB).
  - Filter the 500 reviews to only include products present in this shard, or accept that products outside this shard will have unpopulated metadata fields.
  - *Advantage*: Completely local, fast queries; no complex network seeks.
  - *Trade-off*: Requires transferring 205 MB (still well below the 4.02 GB JSONL).
- **Option D: Streaming Metadata Filter with Strict Transfer Cap**:
  - Stream bytes from `meta_Cell_Phones_and_Accessories.jsonl` searching for the specific `parent_asin`s from the review sample, but enforce a hard cutoff (e.g., abort after transferring 25 MB max).
  - Catalogue products whose metadata was located within the cutoff; display placeholder catalog cards for any remaining products.

*(Note: None of these options will be executed without explicit user authorization before Phase 2.)*

---

## 12. Safety and Authorization Audit

- [x] No data files (Parquet, JSONL, CSV, image, archive) downloaded.
- [x] No packages or libraries installed.
- [x] No dataset loading scripts executed (`trust_remote_code=True` was not run).
- [x] No HTTP Range payload requests executed (only read-only HEAD requests).
- [x] No application code scaffolded.
- [x] Phase 0 foundational documents left untouched.
- [x] Port 5173 / Port 8000 processes untouched.
- [x] No Git initialization performed.
- [x] Phase 2 remains `not_started`.

---

## 13. Acceptance Checklist

| Requirement | Result | Verified Evidence |
| :--- | :---: | :--- |
| **Defensible category mapping** | **PASS** | `Cell_Phones_and_Accessories` verified in `all_categories.txt` (line 11), distinct from `Electronics` (line 15). `[DIRECTLY OBSERVED METADATA]` |
| **Review & metadata configs identified** | **PASS** | `raw_review_Cell_Phones_and_Accessories` and `raw_meta_Cell_Phones_and_Accessories` confirmed in README and `Amazon-Reviews-2023.py`. `[DOCUMENTED FACT]` |
| **Schemas and join keys documented** | **PASS** | `parent_asin` verified as canonical review-to-meta join key; schema definitions mapped; empirical record nullability marked unverified. |
| **Review primary key collisions addressed** | **PASS** | Vulnerabilities of `text[:50]` prefix analyzed; full canonical record hash and provenance tracking proposed. |
| **Bounded sampling feasibility assessed** | **PASS (CONDITIONAL)** | `accept-ranges: bytes` confirmed via CloudFront HEAD; classified as conditionally feasible pending authorized payload test; transfer budgets labeled as analytical estimates. |
| **Metadata retrieval evaluated** | **PASS (UNRESOLVED EVALUATION)** | Unindexed 4.02 GB JSONL identified as architectural challenge; naive range scan discarded; four safe candidate options documented for user approval. |
| **Exact remote file sizes verified** | **PASS** | Reviews JSONL: 9,342,568,048 bytes; Meta JSONL: 4,015,159,840 bytes; Parquet: 1,262,072,469 bytes total. `[DIRECTLY OBSERVED METADATA]` |
| **Cryptographic / Transport hashes distinguished** | **PASS** | Git LFS OID, CloudFront HTTP ETag, and local SHA-256 explicitly distinguished as non-interchangeable. |
| **Zero data downloaded** | **PASS** | 0 bytes of dataset content retrieved; only HTTP headers and public documentation read. |
| **Zero packages installed** | **PASS** | No pip or npm commands executed. |
| **Category lock preserved** | **PASS** | **Mobile Phones & Accessories Only** maintained without substitution. |
| **Sole data source preserved** | **PASS** | `McAuley-Lab/Amazon-Reviews-2023` strictly maintained. |

---

## 14. Final Decision and Required User Approval

Phase 1 technical feasibility investigation is complete and revised to address all independent audit findings. The evidence confirms that `McAuley-Lab/Amazon-Reviews-2023` officially supports `Cell_Phones_and_Accessories` and that `parent_asin` is the verified join key. Bounded access ($\le 500$ records) is **conditionally feasible** based on advertised `accept-ranges: bytes` headers, pending an authorized Range payload test in Phase 2. Metadata retrieval strategies for matching `parent_asin`s have been evaluated, marked as unresolved, and accompanied by four concrete, safe options requiring future approval.

Zero dataset records have been downloaded, no HTTP Range payload tests were performed, and Phase 2 remains `not_started`. Phase 1 is ready for independent review. **Phase 2 will not begin without explicit user approval.**

---

PHASE 1 READY FOR INDEPENDENT APPROVAL — NO DATA DOWNLOADED

