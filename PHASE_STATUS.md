# ProductPulse — Phase Status Tracker (`PHASE_STATUS.md`)

> **PERMANENT CATEGORY LOCK NOTICE**  
> Target Domain: **Mobile Phones & Accessories**  
> Source Dataset: **McAuley-Lab/Amazon-Reviews-2023** on Hugging Face  
> No phase may alter this domain without explicit user approval supported by documented dataset evidence.

---

## Phase Roadmap Overview

| Phase | Title | Status | Prerequisites | Blockers / Critical Risks |
| :---: | :--- | :---: | :--- | :--- |
| **0** | Environment Inspection & Architecture Foundation | `complete_pending_approval` | None | Ports 5173 and 8000 occupied by pre-existing processes; hadoop and hive commands not found in PATH; Java compatibility must be established. |
| **1** | Official Dataset Feasibility & Category Verification | `not_started` | Phase 0 approved | Multi-GB archive transfer costs; selective access feasibility unverified. |
| **2** | Bounded Data Ingestion & Quality Validation | `not_started` | Phase 1 approved & plan accepted | Upstream missing keys, corrupt records, image availability. |
| **3** | Final Data Contract, Architecture & Database Design | `not_started` | Phase 2 validated data sample | Schema evolution, foreign key integrity, query performance. |
| **4** | Backend API Implementation & Verification | `not_started` | Phase 3 approved database layer | Port 8000 conflict with external uvicorn process. |
| **5** | Frontend Foundation & Product Catalogue | `not_started` | Phase 4 approved API | Port 5173 conflict with external vite process. |
| **6** | Product Details, Reviews & Fallback Handling | `not_started` | Phase 5 approved catalogue | Missing/broken image links from source dataset. |
| **7** | NLP Processing: Sentiment & Aspect Extraction | `not_started` | Phase 3/6 verified reviews | Weak-label bias; aspect ambiguity in short reviews. |
| **8** | Complaint Discovery & Evidence Retrieval | `not_started` | Phase 7 verified aspects | Distinguishing complaints from feature queries; evidence snippet alignment. |
| **9** | Big Data Analytics (Hadoop, MapReduce, Hive) | `not_started` | Phase 2 data & approved environment | Hadoop/Hive commands not found in Windows/WSL PATH; host has Java 24; version compatibility must be established using authoritative documentation. |
| **10** | Product Comparison & Supported Historical Trends | `not_started` | Phases 4, 7, 8, 9 complete | Sparse temporal review distributions; non-comparable metrics. |
| **11** | Independent Evaluation, Testing & Bug Fixing | `not_started` | Full stack implementation | Coverage gaps; divergence between SQLite and Hive aggregates. |
| **12** | Final Documentation, Reproducibility & Viva Prep | `not_started` | Phase 11 verified pass | Documentation-code divergence; environment reproducibility. |

---

## Detailed Phase Status & Acceptance Evidence

### Phase 0: Environment Inspection & Architecture Foundation
- **Status**: `complete_pending_approval` (All Phase 0 requirements verified; awaiting user & external review)
- **Objective**: Inspect host hardware, operating system, runtimes, dependencies, services, ports, and Hadoop/Hive readiness without modifying system state or scaffolding future application code.
- **Prerequisites**: Access to workspace `d:\ProductPulse-nlp-bda`.
- **Key Evidence Required**:
  - [x] Host OS, CPU, RAM, and exact drive free space documented.
  - [x] Python, pip, Node.js, npm, and Git versions confirmed.
  - [x] Docker daemon and WSL distribution status inspected.
  - [x] Java version and absence of Hadoop/Hive on Windows and WSL documented.
  - [x] Local port occupancy for 5173 and 8000 safely inspected and owning PIDs identified.
  - [x] Five foundational documents created and mutually consistent (`PROJECT_SPEC.md`, `PHASE_STATUS.md`, `DATA_CONTRACT.md`, `ARCHITECTURE.md`, `ENVIRONMENT_REPORT.md`).
  - [x] Permanent Mobile Phones & Accessories scope lock recorded in all files.
  - [x] Zero application scaffolding, zero dependencies installed, zero dataset downloads.
- **Identified Blockers**:
  - Port 5173 is occupied by an external Node/Vite process (PID 5988; pre-existed Phase 0; left untouched).
  - Port 8000 is occupied by an external Python/Uvicorn process (PID 40392, 41424; pre-existed Phase 0; left untouched).
  - Hadoop and Hive CLI commands were not found in the checked Windows PATH or WSL Ubuntu PATH; no running Hadoop/Hive daemons or services were detected; host Java is 24.0.1, so compatibility must be established for specific Hadoop/Hive versions selected using authoritative documentation before Phase 9.

---

### Phase 1: Official Dataset Feasibility, Schema Verification & Category Coverage
- **Status**: `not_started`
- **Objective**: Inspect Hugging Face dataset configuration for `McAuley-Lab/Amazon-Reviews-2023`, determine the exact subset naming for *Mobile Phones & Accessories*, inspect metadata/review schemas, determine streaming/partial download feasibility, and present an evidence-based ingestion proposal ($\le 500$ sample).
- **Prerequisites**: Phase 0 formally approved by user.
- **Evidence Required**: Real dataset card inspection, schema field confirmation, subset name confirmation, file size metrics, and sample plan.

---

### Phase 2: Bounded Data Ingestion & Quality Validation
- **Status**: `not_started`
- **Objective**: Execute approved bounded ingestion of mobile phone products and review records (maximum 500 reviews initially). Generate data quality manifest.
- **Prerequisites**: Phase 1 findings reviewed, ingestion plan approved by user.
- **Evidence Required**: Raw JSONL artifacts, quality manifest, duplicate counts, missing key analysis, checksums.

---

### Phase 3: Final Data Contract, Architecture & Database Design
- **Status**: `not_started`
- **Objective**: Implement SQLite database schema, foreign key relations, indexes, and normalization pipeline based on Phase 2 verified data.
- **Prerequisites**: Phase 2 data quality passed and approved.
- **Evidence Required**: SQLite DDL, test migration scripts, foreign key verification queries, contract conformance test results.

---

### Phase 4: Backend API Implementation & Testing
- **Status**: `not_started`
- **Objective**: Build FastAPI application with typed Pydantic models, pagination, parameterised SQLite queries, and test endpoints.
- **Prerequisites**: Phase 3 database verified; Port 8000 blocker resolved or cleared.
- **Evidence Required**: Automated test suite execution (pytest), API response schemas, error handling (404/422) verification.

---

### Phase 5: Frontend Foundation & Product Catalogue
- **Status**: `not_started`
- **Objective**: Implement React + TypeScript + Vite + Tailwind frontend for product browsing, filtering, search, and pagination.
- **Prerequisites**: Phase 4 API endpoints verified; Port 5173 blocker resolved or cleared.
- **Evidence Required**: Component rendering tests, API integration tests, responsive layout, loading/empty states.

---

### Phase 6: Product Detail Pages & Review Browsing
- **Status**: `not_started`
- **Objective**: Build comprehensive product detail route (`/products/:productId`), review listing, verified image gallery, and fallback image handler.
- **Prerequisites**: Phase 5 catalogue approved.
- **Evidence Required**: Product view verification, review pagination, image error boundary tests.

---

### Phase 7: NLP Processing: Sentiment & Aspect Extraction
- **Status**: `not_started`
- **Objective**: Develop NLTK / scikit-learn sentiment analysis and category-specific aspect extraction models. Store predictions and aspects in SQLite.
- **Prerequisites**: Phase 6 review browsing validated.
- **Evidence Required**: Evaluation metrics (Precision/Recall/F1), confusion matrix, aspect keyword dictionary rules, sample predictions.

---

### Phase 8: Complaint Discovery & Evidence Retrieval
- **Status**: `not_started`
- **Objective**: Cluster negative reviews into distinct customer complaint themes and link every theme to verifiable review excerpts.
- **Prerequisites**: Phase 7 aspect analysis verified.
- **Evidence Required**: Complaint cluster summaries, TF-IDF / keyword extraction evidence, clickable review text verification.

---

### Phase 9: Real Big Data Analytics (Hadoop, MapReduce, Hive)
- **Status**: `not_started`
- **Objective**: Execute genuine Hadoop MapReduce/Streaming jobs and Hive analytical aggregations on review data. Compare outputs against SQLite reference computations.
- **Prerequisites**: Phase 2 data ready; Hadoop runtime environment decision approved.
- **Evidence Required**: Job execution logs, Hive SQL query scripts, HDFS directory listings, output parity checks against Python reference.

---

### Phase 10: Product Comparison & Supported Historical Trends
- **Status**: `not_started`
- **Objective**: Implement side-by-side comparison route (`/compare`) and temporal trend visualization based on valid review timestamps.
- **Prerequisites**: Phases 4, 7, 8, 9 verified.
- **Evidence Required**: Comparison metric parity tests, temporal density threshold validation, empty trend handling.

---

### Phase 11: Independent Evaluation, Integration Testing & Bug Fixing
- **Status**: `not_started`
- **Objective**: Conduct comprehensive end-to-end testing, error recovery tests, and external review remediation.
- **Prerequisites**: All previous functional phases implemented.
- **Evidence Required**: End-to-end test execution reports, bug fix verification log.

---

### Phase 12: Final Documentation, Reproducibility & Viva Preparation
- **Status**: `not_started`
- **Objective**: Finalize academic documentation, setup guides, reproducibility verification, and viva defence script.
- **Prerequisites**: Phase 11 tests passed.
- **Evidence Required**: Finalized `PROJECT_SPEC.md`, `ARCHITECTURE.md`, clean installation walkthrough, reproducible demo commands.
