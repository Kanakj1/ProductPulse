# ProductPulse — Same-Day Human Annotation Workflow

> **Purpose:** Step-by-step practical guide for human annotators to annotate evaluation samples and safely reconcile them today.  
> **Target Category:** Mobile Phones & Accessories (`Cell_Phones_and_Accessories`)  
> **Source Corpus:** Verified Amazon Reviews 2023 (`backend/db/productpulse.db`)  
> **Templates Location:** `data/annotation/`

---

## 1. Overview & Core Principles

1. **Evidence Grounding**: Annotate only what the customer explicitly stated in the sentence text. Never guess, extrapolate unstated defects, or rely on customer star ratings as sentiment ground truth.
2. **Never Edit Immutable Metadata**:
   - In **Sample A**, never edit: `sentence_id`, `review_id`, `parent_asin`, `asin`, `source_rating`, or `sentence_text`.
   - In **Sample B**, never edit: `annotation_id`, `sentence_id`, `review_id`, `parent_asin`, `asin`, `source_rating`, `sentence_text`, or `target_aspect`.
   - Any modification to these columns triggers a `ReconciliationError` and aborts reconciliation.
3. **Blank Cells Remain Unannotated**: Leaving decision cells blank is fully supported. The reconciliation tool marks blank cells as `unannotated`, and evaluation metrics exclude unannotated units from metric denominators.
4. **Pilot Scope & Realistic Expectations**:
   - The goal today is a small, honest pilot to verify the annotation and evaluation pipeline.
   - A small pilot sample does **not** guarantee statistical validity or robust production performance; reliability depends on the number and distribution of genuinely annotated, eligible examples across aspects and classes.
5. **Sample B Sampling Caveat**:
   - **Sample B is keyword-enriched** to efficiently gather aspect candidates for sentiment evaluation.
   - **Do not use Sample B to estimate aspect prevalence** in the overall dataset. Only Sample A (which uses uniform random sentence sampling) reflects unbiased aspect distribution.

---

## 2. Aspect Taxonomy (The 6 Fixed Aspects)

Every decision must map to one of our six domain aspects:

| Aspect Key | Display Name | Scope & Key Components | Negative Example | Positive Example |
| :--- | :--- | :--- | :--- | :--- |
| `build_durability` | Build & Durability | Materials, casing, drop resistance, scratch resistance, buttons, hinges, build quality. | *"The plastic case cracked after one drop."* | *"Sturdy aluminum frame, feels premium."* |
| `battery_charging` | Battery & Charging | Battery life, drainage, charging speed, chargers, charging cables, wireless charging, heat while charging. | *"Battery drains in four hours on standby."* | *"Fast charging reaches 80% in 30 minutes."* |
| `screen_display` | Screen & Display | Brightness, resolution, OLED/LCD, touch responsiveness, refresh rate, glare, outdoor visibility. | *"The display is completely washed out in sunlight."* | *"Vibrant OLED screen with super smooth 120Hz."* |
| `camera_optics` | Camera & Optics | Photo quality, low-light/night mode, zoom, lenses, video stabilization, focus speed. | *"Pictures look grainy and blurry in low light."* | *"Takes crisp, sharp portraits with natural colors."* |
| `connectivity_audio` | Connectivity & Audio | Bluetooth pairing, Wi-Fi, 5G/cellular reception, speaker loudness, call clarity, microphone. | *"Bluetooth constantly disconnects while driving."* | *"Call clarity is clear and speaker is very loud."* |
| `performance_software` | Performance & Software | Speed, UI smoothness, gaming lag, app crashes, OS updates, system freezes, RAM management. | *"The phone freezes frequently after the update."* | *"Snappy processor, no lag with multitasking."* |

### Common Disambiguation Edge Cases
- **"Case"**:
  - Protective phone case $\implies$ `build_durability`.
  - Idiomatic expression (*"in this case"*, *"just in case"*) $\implies$ **NOT an aspect** (`0` or blank).
- **"Cord" / "Cable"**:
  - Charging cable $\implies$ `battery_charging`.
  - Audio/headphone cable $\implies$ `connectivity_audio`.
- **"Touch"**:
  - Touchscreen responsiveness $\implies$ `screen_display`.
  - Physical texture/feel $\implies$ `build_durability`.

---

## 3. How to Annotate Sample A (Aspect Detection Benchmark)

**File**: `data/annotation/sample_a_aspect_detection_template.csv`  
**Goal**: Mark which of the 6 aspects are discussed in each review sentence.

### The Columns
Each row represents 1 customer review sentence. You will fill in 6 aspect decision columns:
1. `build_durability`
2. `battery_charging`
3. `screen_display`
4. `camera_optics`
5. `connectivity_audio`
6. `performance_software`
7. `annotator_notes` (optional notes)

### Code-Verified Accepted Values (`normalize_presence`)
For each aspect decision column, the reconciliation code accepts (case-insensitive):
- **Present**: **`1`**, **`true`**, **`present`**, **`yes`**, or **`y`** $\rightarrow$ maps to `DetectionStatus.PRESENT`.
- **Absent**: **`0`**, **`false`**, **`absent`**, **`no`**, or **`n`** $\rightarrow$ maps to `DetectionStatus.ABSENT`.
- **Unannotated**: An empty/blank cell $\rightarrow$ remains `AnnotationStatus.UNANNOTATED`.

*Recommendation*: Use **`1`** for present, **`0`** for absent, and leave blank for unannotated rows.  
*(Note: Sample A measures aspect detection only; sentiment is not evaluated in Sample A).*

---

## 4. How to Annotate Sample B (Aspect Sentiment Benchmark)

**File**: `data/annotation/sample_b_aspect_sentiment_template.csv`  
**Goal**: Confirm aspect presence and assign aspect-specific sentiment for candidate sentences.

### The Columns
Each row contains a candidate sentence pre-selected for a specific `target_aspect`. You will fill in:
1. `aspect_confirmed`
2. `human_sentiment`
3. `annotator_notes` (optional notes)

### Step 1: Aspect Confirmation (`aspect_confirmed`)
Code-verified accepted values (case-insensitive):
- **`1`** (or `true`, `present`, `yes`, `y`): Aspect is confirmed present in the sentence.
  - **Requirement**: You **MUST** enter a valid `human_sentiment`.
- **`0`** (or `false`, `absent`, `no`, `n`): False positive keyword match; aspect is not discussed.
  - **Requirement**: You **MUST leave `human_sentiment` BLANK**. Schema Rule 1 forbids sentiment on absent aspects.
- **Blank**: Leave blank to leave the record unannotated.

### Step 2: Sentiment Assignment (`human_sentiment`)
When `aspect_confirmed == 1`, enter one of the accepted sentiment values:

| Canonical Schema Value | Accepted Aliases in Code | When to Use | Example |
| :--- | :--- | :--- | :--- |
| **`positive`** | `pos`, `positive` | Clear customer satisfaction, praise, or favorable performance. | *"Battery lasts all day long."* |
| **`neutral`** | `neu`, `neutral` | Objective physical facts, technical specs, or statements without praise or critique. | *"This charger outputs 20 watts."* |
| **`negative`** | `neg`, `negative` | Clear customer dissatisfaction, defect, disappointment, or malfunction. | *"The screen cracked on day two."* |
| **`uncertain/unclassified`** | `uncertain`, `unclassified`, `uncertain/unclassified`, `ambiguous`, `?` | Mixed sentiment for the same aspect, sarcasm, or ambiguous/truncated context. | See Section 5 below. |

*Recommendation*: Use standard lowercase labels: `positive`, `neutral`, `negative`, or `uncertain/unclassified`.

---

## 5. When to Mark `uncertain/unclassified` (Do Not Guess)

Ground truth must be reliable. If you cannot determine sentiment objectively, mark `uncertain/unclassified` (or `uncertain`) and add a brief note in `annotator_notes`:

1. **Mixed / Conflicting Polarity for the Same Aspect in One Sentence**:
   - *"The camera takes gorgeous daylight photos, but terrible night shots."*  
     $\rightarrow$ `aspect_confirmed: 1`, `human_sentiment: uncertain/unclassified`, `notes: mixed camera daylight vs night`.
2. **Sarcasm or Ambiguous Irony**:
   - *"Love how the battery dies right when I need GPS navigation."*  
     $\rightarrow$ `aspect_confirmed: 1`, `human_sentiment: uncertain/unclassified`, `notes: sarcasm`.
3. **Conditional or Hypothetical Statements**:
   - *"If the screen were brighter, this would be a great phone."*  
     $\rightarrow$ `aspect_confirmed: 1`, `human_sentiment: uncertain/unclassified`, `notes: hypothetical critique`.
4. **Insufficient / Truncated Context**:
   - *"Audio volume."*  
     $\rightarrow$ `aspect_confirmed: 1`, `human_sentiment: uncertain/unclassified`, `notes: fragment without polarity`.

---

## 6. Recommended Same-Day Order of Work (Pilot Phasing)

To complete a practical, honest pilot today without fatigue:

### Phase 1: Pilot Calibration (20–30 minutes)
1. Open `sample_a_aspect_detection_template.csv`.
2. Annotate the first **20 sentences** (rows 2 to 21). Enter `1` for mentioned aspects and `0` for unmentioned aspects.
3. Open `sample_b_aspect_sentiment_template.csv`.
4. Annotate the first **20 candidate rows** (rows 2 to 21). Confirm presence (`1` or `0`) and enter sentiment for confirmed rows.
5. Run the reconciliation commands (Section 7) to verify zero syntax errors and validate SQLite offsets.

### Phase 2: Preliminary Evaluation Subset (45–60 minutes)
1. Extend Sample A through sentence **60** (40 additional sentences $\rightarrow$ total 60 sentences = 360 binary decisions).
2. Extend Sample B through unit **60** (40 additional units $\rightarrow$ total 60 candidate units).
3. Run reconciliation and inspect completed counts.
4. *Milestone reached*: A 60-item subset serves as a **small, preliminary evaluation subset** for pipeline smoke testing and initial baseline sanity checks.  
   *(Note: Reliability depends heavily on class distribution; aspects or sentiment classes with few positive instances will have wide confidence intervals).*

### Phase 3: Extended Batch (Optional, if time permits)
- Annotate additional items towards the full 200 items in each sample if time and focus allow.

---

## 7. How to Safely Reconcile Completed CSVs

Always run reconciliation using the project virtual environment. The reconciliation tool automatically verifies:
- Metadata immutability and ID parity.
- Permitted controlled vocabulary.
- Cross-state consistency rules (e.g. absent aspects must have null sentiment).
- **Default SQLite source-text verification**: connects read-only (`mode=ro`) to `backend/db/productpulse.db` and validates that `raw_text[char_start:char_end]` exactly matches the canonical sentence text.

### Reconcile Sample A (Aspect Detection)
```powershell
.venv\Scripts\python.exe scripts/reconcile_annotations.py `
  --sample A `
  --csv data/annotation/sample_a_aspect_detection_template.csv `
  --canonical data/annotation/sample_a_aspect_detection_template.jsonl `
  --output data/annotation/sample_a_reconciled.jsonl `
  --overwrite
```

### Reconcile Sample B (Aspect Sentiment)
```powershell
.venv\Scripts\python.exe scripts/reconcile_annotations.py `
  --sample B `
  --csv data/annotation/sample_b_aspect_sentiment_template.csv `
  --canonical data/annotation/sample_b_aspect_sentiment_template.jsonl `
  --output data/annotation/sample_b_reconciled.jsonl `
  --overwrite
```

> [!IMPORTANT]
> Do **NOT** use `--skip-db-verify` during normal reconciliation. Bypassing SQLite verification risks accepting corrupted offsets or unverified review text. Always keep the default database verification active.

---

## 8. What Metrics Will Be Reported (And What Will Not)

### What Can Be Reported:
- **Sample A Aspect Detection**:
  - Per-aspect Precision, Recall, Support, and F1 for all 6 aspects.
  - Overall unweighted Macro-F1 across detected aspects.
  - Denominators are derived **strictly** from annotated sentences.
- **Sample B Aspect Sentiment**:
  - Primary Three-Class Macro-F1 (`positive`, `neutral`, `negative`) on unambiguous gold units.
  - 4x4 Diagnostic Confusion Matrix (including `uncertain/unclassified`).
  - Operational uncertainty rates and coverage accounting breakdown.

### What Cannot Be Reported (Integrity Warning):
- Unannotated records are **never** evaluated as gold labels.
- Heuristic keyword matches from the sampler are **not** ground truth.
- Synthetic ratings or model predictions cannot evaluate other model predictions.
- Metrics are calculated only on units where a human explicitly reviewed the text.

---

## 9. Immediate Next Step: NLP Baseline (Phase 7D)

Once the reconciled gold files (`sample_a_reconciled.jsonl` and `sample_b_reconciled.jsonl`) are generated from the pilot:
- **The exact next step** is implementing the **Phase 7D NLP Baseline**: a deterministic rule/lexicon-based ABSA model that predicts aspect presence and aspect sentiment on the annotated test sentences.
- The baseline will be evaluated using [`evaluate_detection`](file:///d:/ProductPulse-nlp-bda/backend/app/nlp/metrics.py#L246-L330) and [`evaluate_sentiment`](file:///d:/ProductPulse-nlp-bda/backend/app/nlp/metrics.py#L80-L244) against our reconciled gold labels to establish our initial Macro-F1 performance benchmark.
