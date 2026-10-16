# ProductPulse — 5–7 Minute Demonstration Script & Viva Defense

This script is tailored for a college presentation, project viva, or evaluator walkthrough. It provides a timed demonstration sequence, exact on-screen click paths, spoken talking points, and anticipated evaluator questions with truthful, grounded answers.

---

## 1. Quick Setup Before Presentation

Ensure the two development servers are running:
1. **FastAPI Backend**: `http://127.0.0.1:8000` (PID verified in `.venv`)
2. **React Frontend**: `http://127.0.0.1:5173`
3. Have the browser open at `http://127.0.0.1:5173`.
4. Keep a terminal open at `D:\ProductPulse-nlp-bda` for test/verification commands.

---

## 2. Timed Presentation Sequence (5–7 Minutes)

```
[0:00 - 0:45] Step 1: Introduction & Problem Statement
[0:45 - 1:45] Step 2: Product Catalogue & Metadata Integrity
[1:45 - 3:00] Step 3: Individual Product Dashboard Drill-Down
[3:00 - 3:45] Step 4: Customer Reviews Explorer & Filtering
[3:45 - 4:45] Step 5: Category-Level Review Analytics (Hadoop & Hive)
[4:45 - 5:45] Step 6: Aspect-Level NLP Baseline & Methodology
[5:45 - 6:30] Step 7: Distributed Big Data Pipeline Provenance
[6:30 - 7:00] Step 8: Limitations & Conclusion
```

---

### Step 1: Introduction & Problem Statement (0:00 – 0:45)

- **Screen**: Frontend landing page at `http://127.0.0.1:5173` (Products tab).
- **Action**: Point to the navigation bar and the project title **ProductPulse**.
- **What to Say**:
  > *"Good morning, evaluators. Today I am presenting **ProductPulse**, an end-to-end Big Data Analytics and Natural Language Processing platform for mining e-commerce customer reviews.*
  >
  > *In e-commerce, raw star ratings are misleading. A smartphone with an overall 4.2-star rating might have a great camera and screen, but severe battery overheating or poor build quality. Customers and product engineers need granular, aspect-level intelligence.*
  >
  > *ProductPulse processes a verified sample of 25,000 Amazon customer reviews from the Cell Phones & Accessories category using Apache Hadoop MapReduce and Apache Hive, combined with an aspect-based NLP baseline and a React analytics dashboard."*

---

### Step 2: Product Catalogue & Metadata Integrity (0:45 – 1:45)

- **Screen**: `Products` (`catalogue`) tab.
- **Action**: Scroll through the product list. Highlight the top product `B01415QHYW` (282 reviews) and `B07P9S6R9Y` (248 reviews).
- **What to Say**:
  > *"Here is the Product Catalogue, containing **19,065 unique mobile products** catalogued from the 25,000 review records.*
  >
  > *You will notice an honest disclosure here: **'Product name unavailable'** accompanied by the canonical Amazon ASIN badge. In the source Amazon 2023 dataset, review records contain review texts and parent ASINs, but no official catalog titles. Rather than hallucinating synthetic names or fabricating stock photography, our platform strictly preserves data integrity and uses canonical parent ASINs as unique identifiers."*

---

### Step 3: Individual Product Dashboard Drill-Down (1:45 – 3:00)

- **Screen**: Click on product `B01415QHYW` or click **"Dashboard"**.
- **Action**: Walk through Sections A, B, C, and D of `ProductDashboardView`.
- **What to Say**:
  > *"Clicking any product opens its dedicated **Individual Product Dashboard**:*
  >
  > * **Section A (Overview)**: We see 282 genuine customer reviews, a 4.19 ★ average rating, 1,006 helpful votes, and an 80.9% verified purchase rate.*
  > * **Section B (Star Rating Distribution)**: An empirical 1★ to 5★ histogram. 73.8% of customers gave 5 stars, while 10.3% gave 1 star.*
  > * **Section C (Individual Aspect Analytics)**: These metrics come directly from our **Hadoop MapReduce streaming job**. We see discussions across Screen & Display (21 reviews, 4.24 ★), Build & Durability (20 reviews, 4.05 ★), Battery & Charging (12 reviews, 3.92 ★), and Camera & Optics (4 reviews, 4.25 ★). Notice the stacked sentiment bar showing positive, neutral, and low-rating friction points.*
  > * **Section D (Customer Reviews)**: Real, paginated customer submissions for this product with helpful vote counters and timestamps."*

---

### Step 4: Customer Reviews Explorer & Filtering (3:00 – 3:45)

- **Screen**: Click on **"Customer Reviews"** tab in the navbar.
- **Action**: Select `Rating: 1 Star` filter and click **Apply Filters**.
- **What to Say**:
  > *"In the **Customer Reviews** view, users can explore all 25,000 customer reviews with multi-criteria filtering.*
  >
  > *When I filter for 1-star reviews, we immediately see customer complaints regarding shattered glass, battery drain, or unresponsive touchscreens. If a review has no text and only a rating, our system explicitly displays 'No customer review text provided (rating-only submission)' rather than generating fake text."*

---

### Step 5: Category-Level Review Analytics (Hadoop & Hive) (3:45 – 4:45)

- **Screen**: Click on **"Review Analytics"** tab in the navbar.
- **Action**: Point out the 5 KPI summary cards at the top, then click through sub-tabs: *Aspect Volumes*, *Customer Pain Points*, and *Mentions per Review*.
- **What to Say**:
  > *"The **Review Analytics** tab presents macro-level intelligence computed via distributed batch jobs:*
  >
  > * *Our 5 verified KPIs: 25,000 reviews evaluated, a 4.1655 ★ corpus average, 19,065 products, 16,409 aspect-discussing reviews, and 26,029 total aspect-review pairs.*
  > * *Under **Aspect Volumes (Hive Query 1)**: 'Build & Durability' is the most discussed aspect (10,846 reviews, 4.15 ★), while 'Connectivity & Audio' has the lowest average rating (3.94 ★).*
  > * *Under **Customer Pain Points (Hive Query 3)**: We filter for product aspects with at least 5 reviews that have the lowest customer ratings, pinpointing potential manufacturing or software defects.*
  > * *Under **Aspect Penetration (Hive Query 5)**: Shows what percentage of a product's reviews discuss a specific aspect."*

---

### Step 6: Aspect-Level NLP Baseline & Methodology (4:45 – 5:45)

- **Screen**: Switch to PowerShell terminal.
- **Action**: Run `.\.venv\Scripts\python.exe scripts/run_nlp_baseline_demo.py` or `scripts/evaluate_nlp_baseline.py`.
- **What to Say**:
  > *"For our NLP pipeline, we defined a strict 6-aspect taxonomy with Unicode word-boundary regexes. When we run the benchmark:*
  >
  > * *On **Sample A (Aspect Detection)**, the baseline achieves **0.7778 Macro-F1** across 180 evaluated validation decision units.*
  > * *On **Sample B (Aspect-Conditional Sentiment)**, it evaluates 3-class polarity (positive, neutral, negative).*
  >
  > *An important academic disclosure: These evaluation scores measure rule-verification agreement on held-out validation data against automated heuristic pseudo-labels, rather than human gold labels."*

---

### Step 7: Distributed Big Data Pipeline Provenance (5:45 – 6:30)

- **Screen**: Show `data/bda/hadoop_job_execution.log` or `scripts/bda/README.md`.
- **Action**: Mention Dockerized Apache Hadoop 3.3.6 and Apache Hive 3.1.3 execution.
- **What to Say**:
  > *"To ensure authentic Big Data execution, our BDA pipeline was executed on official **Apache Hadoop 3.3.6** and **Apache Hive 3.1.3** Docker containers:*
  >
  > * *The Hadoop Streaming job ingested the 25,000 records from HDFS, mapped aspect mentions via Python streaming, and aggregated 48,708 keys in `part-00000`.*
  > * *Apache Hive mapped an external table with an isolated Derby metastore and executed 5 analytical SQL queries, generating the CSVs served by our FastAPI backend."*

---

### Step 8: Limitations & Conclusion (6:30 – 7:00)

- **Screen**: Return to the dashboard `About & Methodology` view.
- **What to Say**:
  > *"In conclusion, ProductPulse demonstrates an end-to-end pipeline connecting raw review datasets, distributed Hadoop/Hive batch analytics, deterministic NLP extraction, and a production-grade React dashboard.*
  >
  > *Our primary limitations are the absence of catalog metadata in the raw review JSONL, and reliance on rule-based heuristics rather than fine-tuned transformer models. Future work will integrate transformer models (e.g. RoBERTa) and catalog metadata APIs.*
  >
  > *The system is fully tested with **179 automated tests** passing. Thank you, and I welcome your questions."*

---

## 3. Expected Evaluator / Viva Questions & Truthful Answers

### Q1: "Why do product rows display 'Product name unavailable' instead of real phone models like iPhone 15 or Samsung Galaxy?"
**Truthful Answer**:
> *"The raw Amazon Reviews 2023 dataset consists strictly of review records (`parent_asin`, `user_id`, `rating`, `text`), and does not include the separate metadata catalog file containing product marketing titles. Rather than hallucinating fake phone names or scraping Amazon in violation of reproducible scientific protocols, we made an intentional engineering decision to display 'Product name unavailable' alongside the genuine, canonical parent ASIN. The parent ASIN uniquely and accurately binds all 25,000 reviews and MapReduce records."*

---

### Q2: "Did you actually run Hadoop and Hive, or did you just write Python scripts that output CSV files?"
**Truthful Answer**:
> *"We executed genuine, containerized Hadoop and Hive jobs. We used the official `apache/hadoop:3.3.6` Docker image running single-node HDFS and Hadoop Streaming MapReduce (`aspect_mapper.py` and `aspect_reducer.py`), which generated the 2.15 MB `part-00000` output file. We then ran official Apache Hive 3.1.3 with an embedded Derby metastore schema and executed the SQL script `scripts/bda/hive_analytics.hql`. All stdout logs, job IDs, map/reduce record counters, and HDFS timestamps are preserved and verifiable in `data/bda/hadoop_job_execution.log` and `data/bda/hive_job_execution.log`."*

---

### Q3: "In Query 1, why is the sum of aspect review counts (26,029) higher than the total number of aspect-discussing reviews (16,409)?"
**Truthful Answer**:
> *"Because customer reviews frequently discuss multiple aspects in a single review. For example, a customer might praise the battery life while criticizing the display quality. That single review contributes +1 to `battery_charging` and +1 to `screen_display`. Across the 16,409 reviews that mention at least one aspect, there are 26,029 total aspect-review pairs, representing an average of 1.59 aspect discussions per review."*

---

### Q4: "Does your NLP model achieve 100% human accuracy on sentiment analysis?"
**Truthful Answer**:
> *"No, and we explicitly document this in our evaluation reports. The 1.0 Macro-F1 score on Sample B measures **Rule Verification Agreement** against automated heuristic draft pseudo-labels on a held-out validation partition of 19 eligible cases. It demonstrates that the baseline service correctly adheres to the formal annotation rules and polarity dictionaries, but it should not be claimed as independent human ground-truth accuracy. True human accuracy would require independent human annotator consensus and inter-annotator agreement (Cohen's Kappa)."*

---

### Q5: "What is the difference between Customer Star Ratings and Aspect Sentiment?"
**Truthful Answer**:
> *"Star ratings are overall customer disposition scores ranging from 1.0 to 5.0 submitted by the user for the entire product experience. In contrast, aspect sentiment is fine-grained and aspect-conditional: a customer can give a 5-star review while making a negative comment about the charging cable, or give a 2-star review while praising the camera. In ProductPulse, star ratings serve as baseline disposition metrics, while our NLP pipeline evaluates text polarity specifically within detected aspect contexts."*

---

### Q6: "How does the frontend avoid stale data or race conditions when switching between products?"
**Truthful Answer**:
> *"We implemented request sequence tracking using React refs (`activeRequestIdRef`). Every time a user changes pages or selects a product, the sequence counter increments. If an earlier asynchronous API request resolves after a newer request has already been dispatched, the response ID does not match the active ref and is discarded. Additionally, switching products immediately clears the previous product state to prevent cross-product data leakage."*

---

### Q7: "How many automated tests are in the codebase, and what do they verify?"
**Truthful Answer**:
> *"We have **179 automated tests** in total:
> * **137 Backend Tests** (`python -m unittest discover tests`): Testing API routes, Pydantic schemas, database foreign keys, deterministic ordering, and NLP baseline functions.
> * **42 Frontend Tests** (`npm test` in `frontend/`): Testing API client offline error handling, schema contract parity between TypeScript and Pydantic, filter state lifecycles, and asynchronous sequence discard logic."*
