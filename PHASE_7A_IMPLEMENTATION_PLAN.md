# ProductPulse — Phase 7A Implementation Plan
## Annotation & Evaluation Scaffolding for Aspect-Based Sentiment Analysis

> **STATUS: PROPOSED IMPLEMENTATION PLAN — REVISED FOR USER REVIEW & APPROVAL**  
> **Workspace:** `D:\ProductPulse-nlp-bda`  
> **Phase:** 7A (Annotation & Evaluation Scaffolding)  
> **Target Scope:** Python scaffolding, schemas, tokenizer, leakage-safe partitioner, two-part sampler, evaluation metrics engine, annotation guidelines, and automated tests.  
> **Strict Precondition:** This is a design and planning document only. No code, annotation data, predictions, database migrations, package installations, or resource downloads have been executed. All implementation remains behind explicit user approval.

---

## 1. Executive Objective

Phase 7A establishes a rigorous, reproducible, and auditable foundation for Aspect-Based Sentiment Analysis (ABSA) before any modeling or dataset labeling takes place.

### Core Goals
1. **Deterministic Annotation Unit & Decoupled State**: Formalize the atomic evaluation unit as `(sentence_id, aspect_name)` linked to `review_id`, `parent_asin`, and verbatim character offsets. Strictly separate aspect detection status (`present` | `absent`), annotation status (`unannotated` | `annotated`), and sentiment label (`positive` | `neutral` | `negative` | `uncertain/unclassified`). An absent aspect must never be represented as a sentiment label.
2. **Four-Class Sentiment Taxonomy & Explicit Uncertainty**: Standardize sentiment labels into `positive`, `neutral`, `negative`, and `uncertain/unclassified` with explicit criteria for mixed sentiment and insufficient evidence, keeping `unannotated` structurally distinct.
3. **Leakage-Safe Partitioning Engine**: Create an algorithm that reconciles product grouping (`parent_asin`) with duplicate record quarantining (`canonical_hash`), guaranteeing zero train/val/test contamination. Retain component integrity: report component sizes and actual split proportions without silently splitting connected components.
4. **Conceptually Separate Two-Part Sampling Scaffolding**: Build deterministic generators for:
   - **Sample A (200 random sentences)**: For Aspect Detection evaluation.
   - **Sample B (200 aspect-enriched sentences)**: For Aspect Sentiment classification evaluation.
   - Prevent sentence overlap between Sample A and Sample B where feasible, record seeds and selection rationale, and report stratum shortfalls explicitly instead of silently backfilling.
5. **Unlabeled Evaluation Templates**: Specify that generated templates are strictly unlabeled placeholders until human annotation. Sampled examples must not be treated as ground truth, and evaluation metrics are not meaningful until annotations are completed.
6. **Pure Python Metrics Engine with Explicit Edge Handling**: Implement exact computation of Aspect Detection metrics (P, R, F1) and Sentiment metrics (Macro-F1, per-class P/R/F1, Confusion Matrix, Uncertainty Rate) without external dependencies. Explicitly handle zero denominators, absent classes, uncertain predictions, and unannotated examples without silently discarding records.
7. **Annotation Handbook**: Author a definitive human-annotation guide (`docs/ANNOTATION_GUIDELINES.md`).
8. **Automated Unit Testing**: Require all test cases to pass with zero failures. Report measured code coverage only if a coverage tool is already available in the environment; do not make unconditional 100% coverage claims.

---

## 2. Proposed File-Level Implementation Architecture

All proposed files will reside cleanly within the existing codebase architecture:

```
D:\ProductPulse-nlp-bda\
├── backend\app\nlp\
│   ├── __init__.py                # Package declaration
│   ├── schemas.py                 # Pydantic & dataclass definitions with decoupled detection, annotation, & sentiment states
│   ├── tokenizer.py               # Robust, offset-preserving sentence segmenter (pure Python standard library)
│   ├── partitioner.py             # Leakage-safe graph-component partitioner (parent_asin + canonical_hash)
│   ├── sampler.py                 # Reproducible two-part evaluation sampler with fixed deterministic seeds & shortfall reporting
│   └── metrics.py                 # Mathematical evaluation engine with explicit zero-denominator & edge-case handling
├── docs\
│   └── ANNOTATION_GUIDELINES.md   # Complete human-annotation instruction handbook
├── tests\
│   └── test_nlp_scaffolding.py    # Comprehensive test suite covering segmentation, partitioning, and metrics
└── PHASE_7A_IMPLEMENTATION_PLAN.md# This approved implementation plan
```

---

## 3. Detailed Component Specifications

### 3.1 Data Structures (`backend/app/nlp/schemas.py`)
- **Decoupled State Architecture**:
  The schema strictly enforces three independent states:
  1. `detection_status`: `present` | `absent` (indicates whether the aspect is referenced in the sentence).
  2. `annotation_status`: `unannotated` | `annotated` (indicates whether a human annotator has reviewed the record).
  3. `sentiment_label`: `positive` | `neutral` | `negative` | `uncertain/unclassified` | `None` (valid only when `detection_status == present`; if `detection_status == absent`, `sentiment_label` must be `None` and cannot be assigned a sentiment label).

- **`AnnotationUnit`**:
  - `annotation_id`: Deterministic string `f"{sentence_id}#{aspect_name}"`
  - `sentence_id`: Deterministic string `f"{review_id}_s{sentence_index}"`
  - `review_id`: Source review identifier (`reviews.review_id`)
  - `parent_asin`: Source product identifier (`products.parent_asin`)
  - `asin`: Specific variant SKU evaluated
  - `sentence_index`: 0-based integer index of the sentence within the review
  - `sentence_text`: Verbatim sentence text
  - `char_start`: Starting character offset in raw review text
  - `char_end`: Ending character offset in raw review text
  - `aspect_name`: One of the 6 taxonomy aspects (`build_durability`, `battery_charging`, `screen_display`, `camera_optics`, `connectivity_audio`, `performance_software`)
  - `detection_status`: `present` | `absent`
  - `annotation_status`: `unannotated` | `annotated` (defaults to `unannotated` in generated templates)
  - `sentiment_label`: Optional `positive` | `neutral` | `negative` | `uncertain/unclassified` | `None`
  - `source_rating`: Customer star rating (1.0–5.0) for context
  - `verified_purchase`: boolean flag
  - `sampling_source`: `sample_a_detection` | `sample_b_sentiment`
  - `notes`: Optional string documenting edge cases (`mixed_aspect_sentiment`, `sarcasm`, `title_only`, `insufficient_evidence`, `stratum_shortfall`)

- **`PartitionManifest`**:
  - Schema tracking partition allocations, actual review counts, actual product counts, connected-component size distribution, seed value, actual train/validation/test percentages, and conflict resolution logs.

- **`EvaluationReport`**:
  - Structured output schemas separating Aspect Detection metrics, 3-class Sentiment Classification metrics, and Uncertainty Rate.

---

### 3.2 Robust Sentence Segmenter (`backend/app/nlp/tokenizer.py`)
- **Requirement**: Must run locally using Python standard library `re` without requiring NLTK resource downloads.
- **Specification**:
  - Splits text on terminal punctuation (`.`, `!`, `?`, `\n`) followed by whitespace or uppercase characters.
  - Protects common e-commerce abbreviations: `e.g.`, `i.e.`, `vs.`, `approx.`, `oz.`, `ft.`, `in.`, `v1.0`, `No.`, `etc.`
  - Preserves exact character offsets `[char_start, char_end]` to guarantee full evidence traceability back to raw database text.
  - Handles blank text gracefully (returns empty list).
  - Handles title-only reviews (treats `raw_title` as sentence index 0 if review body is blank).

---

### 3.3 Leakage-Safe Partitioner (`backend/app/nlp/partitioner.py`)
- **Challenge**:
  - Naive product-group splitting (`parent_asin`) can leak data if duplicate reviews (`canonical_hash`) exist across different products.
  - Naive hash splitting can leak data if different reviews of the same product are split across train and test.
- **Solution — Connected-Component Grouping**:
  1. Build a bipartite graph where edges connect `parent_asin` nodes with `canonical_hash` nodes.
  2. Extract connected components (each component is an isolated cluster of products and review hashes that share data).
  3. Hash each cluster deterministically: `hash = sha256(cluster_id + salt)`.
  4. Assign entire clusters to partitions targetting ~70% Train, ~15% Validation, ~15% Test.
  5. **Component Integrity Guarantee**: Connected components are never split silently to hit exact target percentages. If an unusually large component shifts actual proportions (e.g., 68.5% / 15.8% / 15.7%), the exact component sizes and empirical percentages are reported in the partition manifest.
  6. **Duplicate Policy**: All duplicate records (`occurrence_index > 0`) reside in the exact same partition as their canonical record. Zero duplicate records are placed in training if their canonical record belongs to validation or test.
  7. **Auditable Reporting**: Emits component distribution and partition metrics in `data/manifests/phase7_partition_manifest.json`.

---

### 3.4 Reproducible Two-Part Evaluation Sampler (`backend/app/nlp/sampler.py`)
- **Conceptual & Operational Separation**:
  - **Sample A** and **Sample B** serve fundamentally different evaluation purposes and are maintained as separate datasets.
  - Sentence overlap between Sample A and Sample B is actively checked and prevented where feasible. If any sentence is selected in both, the duplicate selection is flagged and logged.
  - Selection seeds, random state, and selection rationale (random index vs keyword match) are recorded in the generated metadata.
- **Unlabeled Template Contract**:
  - Generated evaluation files are strictly **unlabeled templates** (`annotation_status == "unannotated"`).
  - Sampling does **not** create ground truth. Sampled records must never be treated as ground truth or used to compute pseudo-metrics prior to human annotation.
- **Sample A Generator (Aspect Detection Benchmark)**:
  - Draws $N = 200$ sentences uniformly at random from non-blank reviews without applying aspect keyword filters.
  - Purpose: Measures model ability to distinguish aspect-bearing sentences from non-aspect text (precision, recall, false alarm rate).
- **Sample B Generator (Aspect Sentiment Benchmark)**:
  - Targets $N = 200$ aspect-bearing sentences using the domain keyword lexicon.
  - Stratified across all 6 aspects (~30–35 per aspect) and stratified across star rating tiers (1–2★, 3★, 4–5★) to balance polarity distribution.
  - **No Silent Backfilling**: If a specific stratum (e.g., 1–2★ reviews mentioning `connectivity_audio`) has fewer candidate sentences than targeted, the shortfall is explicitly recorded in `stratum_shortfall` metadata. Missing strata are never silently backfilled with unrelated aspects or arbitrary ratings.
  - *Explicit Limitation*: Documented that Sample B keyword hit rates must never be cited as real-world aspect prevalence in the dataset.
- **Output Formats**:
  - Emits `data/evaluation/sample_a_aspect_detection_template.json`
  - Emits `data/evaluation/sample_b_aspect_sentiment_template.json`
  - Emits corresponding CSV templates for human annotators with columns: `annotation_id`, `sentence_id`, `review_id`, `parent_asin`, `sentence_text`, `aspect_name`, `detection_status`, `annotation_status`, `sentiment_label`, `source_rating`, `notes`.

---

### 3.5 Evaluation Metrics Engine (`backend/app/nlp/metrics.py`)
- **Pure Python Standard Library**: Computes all metrics using Python standard library math and data structures (`math`, `collections.Counter`, `dataclasses`). Zero external dependencies or scikit-learn requirements.

#### 3.5.1 Accounting Breakdown & Ground-Truth Disambiguation
To prevent confusion between gold annotations, model predictions, unannotated placeholders, and uncertain edge cases, every evaluation run partitions all submitted records into explicit, auditable accounting counts:
1. `total_records`: Total records submitted to the evaluation engine.
2. `unannotated_count`: Records where `annotation_status == "unannotated"`. These are placeholders awaiting human review. They are strictly excluded from ground-truth performance evaluation and logged in the accounting report. The engine will refuse to compute performance metrics if all records are unannotated.
3. `excluded_absent_count`: Records where gold `detection_status == "absent"`. Because an absent aspect carries no sentiment, these are ineligible for sentiment evaluation and are accounted for in aspect-detection metrics only.
4. `annotated_aspect_present_count`: Records where gold `annotation_status == "annotated"` and gold `detection_status == "present"`. This forms the total eligible population for aspect sentiment analysis ($N_{\text{aspect\_present}}$).
5. `gold_uncertain_count`: Records within $N_{\text{aspect\_present}}$ where human gold `sentiment_label == "uncertain/unclassified"` (e.g., conflicting polarity or insufficient evidence).
6. `eligible_3class_gold_count`: Records within $N_{\text{aspect\_present}}$ where human gold `sentiment_label \in {"positive", "neutral", "negative"}` ($|S_{\text{eligible}}|$).
7. `pred_uncertain_count`: Total predictions where the model outputs `uncertain/unclassified`.

#### 3.5.2 Primary Three-Class Sentiment Macro-F1
The primary sentiment benchmark is strictly restricted to gold examples with unambiguous polarities:
- **Eligible Gold Set ($S_{\text{eligible}}$)**:
  $$S_{\text{eligible}} = \{ u \mid u.\text{annotation\_status} = \text{"annotated"} \land u.\text{detection\_status} = \text{"present"} \land u.\text{gold\_sentiment} \in \{\text{"positive"}, \text{"neutral"}, \text{"negative"}\} \}$$
  Units outside $S_{\text{eligible}}$ (unannotated records, absent aspects, or gold `uncertain/unclassified`) are **not** eligible gold targets for the primary 3-class score.
- **Handling Model Predictions on $S_{\text{eligible}}$**:
  For each unit $u \in S_{\text{eligible}}$ with gold class $g \in \{\text{pos}, \text{neu}, \text{neg}\}$ and model prediction $p \in \{\text{pos}, \text{neu}, \text{neg}, \text{uncertain/unclassified}\}$:
  - If $p = g$: Counts as a True Positive ($TP_g$) for class $g$.
  - If $p \in \{\text{pos}, \text{neu}, \text{neg}\} \land p \neq g$: Counts as a False Negative ($FN_g$) for class $g$ and a False Positive ($FP_p$) for class $p$.
  - If $p = \text{"uncertain/unclassified"}$: The model abstained or was uncertain on an eligible gold instance. This counts as a **miss** (False Negative $FN_g$) for class $g$. It does **not** count as a True Positive for any class, does **not** generate a False Positive for positive/neutral/negative, and is **never** silently discarded or forced into standard classes.
- **Per-Class Metrics on $S_{\text{eligible}}$**:
  For each class $c \in \{\text{pos}, \text{neu}, \text{neg}\}$:
  - $\text{Precision}_c = \frac{TP_c}{TP_c + FP_c}$  
    *Denominator*: Total model predictions of class $c$ on $S_{\text{eligible}}$ ($TP_c + FP_c$). If $TP_c + FP_c = 0$, $\text{Precision}_c \equiv 0.0$.
  - $\text{Recall}_c = \frac{TP_c}{TP_c + FN_c}$  
    *Denominator*: Total gold instances of class $c$ in $S_{\text{eligible}}$ ($TP_c + FN_c$). If $TP_c + FN_c = 0$, $\text{Recall}_c \equiv 0.0$.
  - $F1_c = \frac{2 \cdot \text{Precision}_c \cdot \text{Recall}_c}{\text{Precision}_c + \text{Recall}_c}$. If $\text{Precision}_c + \text{Recall}_c = 0$, $F1_c \equiv 0.0$.
- **Primary Macro-Averaged Sentiment F1**:
  $$\text{Macro-F1}_{\text{3-class}} = \frac{F1_{\text{pos}} + F1_{\text{neu}} + F1_{\text{neg}}}{3}$$

#### 3.5.3 Four-Class Diagnostic Confusion Matrix & Uncertainty Metrics
To provide complete operational diagnostics without corrupting the primary 3-class score, a separate four-class matrix is evaluated over the entire annotated aspect-present population:
- **Eligible Population for Diagnostic Matrix ($S_{\text{diagnostic}}$)**:
  $$S_{\text{diagnostic}} = \{ u \mid u.\text{annotation\_status} = \text{"annotated"} \land u.\text{detection\_status} = \text{"present"} \}$$
  Total size: $|S_{\text{diagnostic}}| = |S_{\text{eligible}}| + \text{gold\_uncertain\_count}$. Unannotated and absent-aspect units remain strictly excluded.
- **Labels (4 Classes)**: `positive`, `neutral`, `negative`, `uncertain/unclassified`.
- **Confusion Matrix Construction ($M_{4 \times 4}$)**:
  Rows represent Gold Labels; Columns represent Model Predictions:
  - Row $g \in \{\text{pos}, \text{neu}, \text{neg}\}$, Col $p \in \{\text{pos}, \text{neu}, \text{neg}\}$: Standard class agreement and confusion.
  - Row $g \in \{\text{pos}, \text{neu}, \text{neg}\}$, Col `uncertain/unclassified`: Model abstentions on clear gold examples (model uncertainty on eligible instances).
  - Row `uncertain/unclassified`, Col `uncertain/unclassified`: Concordant uncertainty (both annotator and model identify ambiguity).
  - Row `uncertain/unclassified`, Col $p \in \{\text{pos}, \text{neu}, \text{neg}\}$: Over-confident model predictions on intrinsically ambiguous gold examples.
- **Operational Uncertainty Metrics**:
  1. **Prediction Uncertainty Rate on Eligible Set**:
     $$\text{Pred Uncertainty Rate}_{\text{eligible}} = \frac{\sum_{u \in S_{\text{eligible}}} \mathbb{I}(u.\text{prediction} = \text{"uncertain/unclassified"})}{|S_{\text{eligible}}|}$$
     *Denominator*: Total eligible 3-class gold units ($|S_{\text{eligible}}|$).
  2. **Overall Prediction Uncertainty Rate**:
     $$\text{Pred Uncertainty Rate}_{\text{overall}} = \frac{\sum_{u \in S_{\text{diagnostic}}} \mathbb{I}(u.\text{prediction} = \text{"uncertain/unclassified"})}{|S_{\text{diagnostic}}|}$$
     *Denominator*: Total annotated aspect-present units ($|S_{\text{diagnostic}}|$).
  3. **Gold Uncertainty Prevalence**:
     $$\text{Gold Uncertainty Prevalence} = \frac{\text{gold\_uncertain\_count}}{|S_{\text{diagnostic}}|}$$
     *Denominator*: Total annotated aspect-present units ($|S_{\text{diagnostic}}|$).

#### 3.5.4 Aspect Detection Metrics (Sample A Benchmark)
Evaluated across all 6 aspects on annotated Sample A sentences:
- For each aspect $a$:
  - $TP_a$: Gold `present` and Predicted `present`.
  - $FP_a$: Gold `absent` and Predicted `present`.
  - $FN_a$: Gold `present` and Predicted `absent`.
  - $TN_a$: Gold `absent` and Predicted `absent`.
  - $\text{Precision}_a = \frac{TP_a}{TP_a + FP_a}$  
    *Denominator*: Total predicted present for aspect $a$ ($TP_a + FP_a$). If $TP_a + FP_a = 0$, $\text{Precision}_a \equiv 0.0$.
  - $\text{Recall}_a = \frac{TP_a}{TP_a + FN_a}$  
    *Denominator*: Total gold present for aspect $a$ ($TP_a + FN_a$). If $TP_a + FN_a = 0$, $\text{Recall}_a \equiv 0.0$.
  - $F1_a = \frac{2 \cdot \text{Precision}_a \cdot \text{Recall}_a}{\text{Precision}_a + \text{Recall}_a}$. If $\text{Precision}_a + \text{Recall}_a = 0$, $F1_a \equiv 0.0$.
- **Detection Macro-F1**:
  $$\text{Macro-F1}_{\text{detection}} = \frac{1}{6} \sum_{a=1}^{6} F1_a$$

---

### 3.6 Annotation Handbook (`docs/ANNOTATION_GUIDELINES.md`)
A complete, standalone reference guide for human annotators:
- Step-by-step annotation walkthrough.
- Taxonomy definition table with positive, negative, and neutral mobile domain examples.
- Boundary rules for ambiguous terms (e.g., distinguishing phone cases from legal cases).
- Disambiguation of states:
  - First step: Mark `detection_status` as `present` or `absent`.
  - Second step (if `present`): Mark `sentiment_label` as `positive`, `neutral`, `negative`, or `uncertain/unclassified`.
  - Mark `annotation_status` as `annotated`.
- Rules for mixed sentiment:
  - If mixed on the *same* aspect $\implies$ label as `uncertain/unclassified` with note `mixed_aspect_sentiment`.
  - If mixed on *different* aspects $\implies$ label each aspect independently.
- Rules for sarcasm, title-only reviews, and truncated fragments.
- Intra-annotator consistency protocol (two-pass re-annotation after 7 days) if a second annotator is unavailable.

---

### 3.7 Scaffolding Test Suite (`tests/test_nlp_scaffolding.py`)
Automated tests integrated into the existing `unittest` framework:
1. `test_sentence_segmentation_offsets`: Verifies that extracted sentences match exact character slices from original raw text.
2. `test_abbreviation_preservation`: Confirms that `e.g.`, `i.e.`, `vs.`, and decimals are not split into erroneous fragments.
3. `test_blank_and_title_handling`: Confirms 7 blank-text reviews and title-only reviews are handled deterministically.
4. `test_partition_leakage_prevention`: Verifies that no `canonical_hash` or duplicate record exists in more than one partition, and verifies component integrity reporting.
5. `test_sampler_reproducibility`: Confirms that identical seeds produce bit-identical sample templates across runs and shortfall tracking works without silent filling.
6. `test_sampler_separation_and_unannotated_contract`: Confirms Sample A and B separation, and ensures all emitted units default to `unannotated`.
7. `test_detection_metrics_math_and_zero_denominators`: Validates mathematical correctness of detection precision, recall, and F1 against hand-computed mock data, including zero denominator edge cases.
8. `test_sentiment_macro_f1_math_and_uncertainty`: Validates mathematical correctness of 3-class macro-F1, per-class metrics, uncertainty rates, and unannotated guardrails against known confusion matrices.

> **Testing & Coverage Standard**:
> All unit tests in the suite must pass with 0 errors and 0 failures. Measured test coverage will be reported only if an approved coverage tool (`coverage.py`) is already available in `.venv`. No unconditional 100% coverage claim is made.

---

## 4. Conflict & Compatibility Check

Inspection of current project files reveals **zero conflicts**:
- **Database Schema**: Leverages existing columns (`reviews.review_id`, `parent_asin`, `canonical_hash`, `occurrence_index`, `raw_text`, `raw_title`). No database modifications required.
- **Category Lock**: Enforces `Cell_Phones_and_Accessories` across all schemas.
- **Dependencies**: All Phase 7A scaffolding runs on standard Python 3.12 library modules (`re`, `json`, `hashlib`, `math`, `collections`, `dataclasses`, `unittest`) and existing `.venv` Pydantic. Zero new package installations or downloads are required.

---

## 5. Execution Preconditions & Approval Gates

Phase 7A implementation will be partitioned into three sequential steps, each requiring explicit verification:

- **Step 7A.1 (Code Creation)**: Create `backend/app/nlp/` modules (`schemas.py`, `tokenizer.py`, `partitioner.py`, `sampler.py`, `metrics.py`) and `docs/ANNOTATION_GUIDELINES.md`.
- **Step 7A.2 (Unit Test Creation)**: Create `tests/test_nlp_scaffolding.py`.
- **Step 7A.3 (Automated Verification)**: Run `unittest` and verify that 100% of the unit tests pass without modifying the database or external environment.

> **CRITICAL HOLD POINT**:
> After Step 7A is completed and tested, execution will **stop**.
> Generating actual annotation files, labeling sentences, training models, downloading NLTK lexicons, or migrating SQLite tables will remain on hold until separate user authorization.

---

## 6. Decisions for User Approval Prior to Implementation

Please review and confirm:
1. **Directory Structure**: Confirm creating `backend/app/nlp/` for NLP pipeline scaffolding.
2. **Decoupled Schema & Metrics Contract**: Confirm the explicit separation between `detection_status`, `annotation_status`, and `sentiment_label`, with shortfall tracking and explicit edge-case metric definitions.
3. **Approval to Proceed**: Provide explicit approval before any code or tests are implemented.

---

*Plan complete. No code, data, or environment modifications have occurred. Awaiting explicit user approval.*
