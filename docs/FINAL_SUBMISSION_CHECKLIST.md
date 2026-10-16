# ProductPulse — Final Submission & Demonstration Checklist

This checklist is designed for same-day college project submission, lab evaluation, and viva preparation. Follow these steps in order to ensure a flawless demonstration.

---

## 1. Pre-Submission Sanity Check

Run these quick checks in your terminal to verify that the environment is healthy before presenting:

- [ ] **Asset Integrity Verification**:
  ```powershell
  .\.venv\Scripts\python.exe scripts/verify_project_integrity.py
  ```
  *Expected Output: `All 17 protected assets and SQLite database verified 100% intact.`*

- [ ] **Backend Unit Tests (137 tests)**:
  ```powershell
  .\.venv\Scripts\python.exe -m unittest discover tests
  ```
  *Expected Output: `Ran 137 tests — OK` (All 137 passed).*

- [ ] **Frontend Contract & Unit Tests (42 tests)**:
  ```powershell
  cd D:\ProductPulse-nlp-bda\frontend
  npm test
  ```
  *Expected Output: `tests 42, pass 42, fail 0`.*

- [ ] **Frontend Production Build**:
  ```powershell
  npm run build
  ```
  *Expected Output: `✓ built in ~2s` (Zero TypeScript compilation errors).*

---

## 2. Launching Services for Live Demonstration

- [ ] **Terminal 1 — FastAPI Backend**:
  ```powershell
  cd D:\ProductPulse-nlp-bda
  .\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
  ```
  Verify in browser: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health) returns `status: "healthy"`.

- [ ] **Terminal 2 — Vite Frontend**:
  ```powershell
  cd D:\ProductPulse-nlp-bda\frontend
  npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
  ```
  Open in browser: [http://127.0.0.1:5173](http://127.0.0.1:5173).

---

## 3. Demonstration Walkthrough Steps (Order of Clicks)

- [ ] **Step 1: Products Catalogue**
  - Open [http://127.0.0.1:5173](http://127.0.0.1:5173).
  - Point out the total catalogue count: **19,065 products**.
  - Show the honest `"Product name unavailable"` fallback and the prominent canonical ASIN badges (e.g. `ASIN: B01415QHYW`).
  - Explain why: The raw review JSONL does not include catalog title metadata; canonical ASINs avoid hallucinated names.

- [ ] **Step 2: Individual Product Dashboard**
  - Click on the top product `B01415QHYW` (or click its **"Dashboard"** button).
  - **Section A**: Show total reviews (282), average customer star rating (4.19 ★), helpful votes (1,006), and verified purchase rate (80.9%).
  - **Section B**: Show the 1★ to 5★ rating histogram and review activity dates.
  - **Section C**: Highlight the authentic Hadoop MapReduce aspect metrics:
    - Screen & Display: 21 reviews (4.24 ★)
    - Build & Durability: 20 reviews (4.05 ★)
    - Battery & Charging: 12 reviews (3.92 ★)
    - Camera & Optics: 4 reviews (4.25 ★)
    - Show the stacked High / Med / Low sentiment breakdown bars.
  - **Section D**: Show genuine customer reviews for this specific product.
  - Click `← Back to Products Catalogue` to demonstrate seamless navigation.

- [ ] **Step 3: Review Analytics (Big Data Aggregations)**
  - Click the **"Review Analytics"** tab in the navbar.
  - Highlight the 5 verified KPI cards:
    - **25,000** Reviews Evaluated
    - **4.1655 ★** Corpus Star Rating
    - **19,065** Catalog Products
    - **16,409** Aspect-Discussing Reviews
    - **26,029** Total Aspect Mentions
  - Click **Aspect Volumes** (Hive Query 1) to show `build_durability` (10,846 reviews) and `battery_charging` (4,514 reviews).
  - Click **Customer Pain Points** (Hive Query 3) to show lowest-rated aspects ($\ge 5$ reviews).
  - Click **Aspect Penetration** (Hive Query 5) to show percentage coverage.
  - Click **Inspect Product** next to any ASIN to show that it jumps straight to that product's dashboard.

- [ ] **Step 4: Customer Reviews Explorer**
  - Click the **"Customer Reviews"** tab in the navbar.
  - Select `Rating: 1 Star` from the dropdown and click **Apply Filters**.
  - Show actual customer complaints regarding screen cracks and dead batteries.
  - Point out honest handling of rating-only reviews with no text.

- [ ] **Step 5: NLP Baseline CLI (Terminal Demo)**
  - Open your terminal and run:
    ```powershell
    .\.venv\Scripts\python.exe scripts/run_nlp_baseline_demo.py
    ```
  - Enter sample review sentences:
    - *"The battery life is terrible and drains in two hours, but the camera takes sharp photos."*
    - Show that it detects `battery_charging` (negative) and `camera_optics` (positive).

---

## 4. Manual Screenshot Capture Guide

For your college report, presentation slides, or lab record, capture the following **7 manual screenshots** from the live app (no fake or placeholder images):

1. **Screenshot 1 — Products Catalogue**:
   - URL: `http://127.0.0.1:5173`
   - Capture: Main catalogue view showing the total product counter (19,065), ASIN badges, star ratings, and the `"Product name unavailable"` honest disclosure banner.
2. **Screenshot 2 — Individual Product Dashboard (Header & KPIs)**:
   - URL: `http://127.0.0.1:5173` (click product `B01415QHYW`)
   - Capture: Top breadcrumb, `← Back to Products Catalogue` button, ASIN badge, 4.19 ★ rating card, and the 4 KPI stat boxes.
3. **Screenshot 3 — Individual Product Aspect Analytics**:
   - Scroll down to Section C of `B01415QHYW`.
   - Capture: Hadoop MapReduce aspect cards for Screen & Display, Build & Durability, Battery & Charging, and the color-coded stacked sentiment bars.
4. **Screenshot 4 — Review Analytics Overview**:
   - URL: `http://127.0.0.1:5173` (click `Review Analytics` tab)
   - Capture: Header chips (`Category Analytics`, `Cell_Phones_and_Accessories`), the 5 KPI summary cards (25k reviews, 4.1655★ rating, 19,065 products), and Aspect Volumes bar chart.
5. **Screenshot 5 — Customer Friction Points (Query 3)**:
   - Click `Customer Pain Points` sub-tab under Review Analytics.
   - Capture: Table showing lowest-rated product aspects (e.g. `B08KQ1L2W3` build durability at 2.60★).
6. **Screenshot 6 — Customer Reviews with Active Filters**:
   - URL: `http://127.0.0.1:5173` (click `Customer Reviews` tab)
   - Filter by `1 Star` rating.
   - Capture: Active filter chips, filtered results counter, and review cards.
7. **Screenshot 7 — Terminal Test Execution & Integrity Pass**:
   - Run `.\.venv\Scripts\python.exe scripts/verify_project_integrity.py` and `python -m unittest discover tests`.
   - Capture: Terminal window showing 137 tests passing and all 17 protected assets intact.

---

## 5. Key Numbers & Cheat-Sheet for Viva Defense

Keep these exact figures in mind if an evaluator asks:

| Question | Quick Exact Answer |
|---|---|
| **Total reviews processed?** | **25,000** customer reviews from Amazon 2023 `Cell_Phones_and_Accessories`. |
| **Total unique products?** | **19,065** parent products (identified by canonical parent ASIN). |
| **Corpus average star rating?** | **4.1655 ★** across all 25,000 reviews. |
| **How many reviews discuss aspects?** | **16,409** reviews (65.64%), with an average rating of 4.1299 ★. |
| **How many reviews have no aspects?** | **8,591** reviews (34.36%), with an average rating of 4.2336 ★. |
| **Total aspect mentions?** | **26,029** aspect-review pairs (average 1.59 aspects per discussing review). |
| **Most discussed aspect?** | **Build & Durability** (10,846 reviews, 4.15 ★ weighted average). |
| **Lowest-rated aspect?** | **Connectivity & Audio** (3.94 ★ weighted average, 16.96% low-rating share). |
| **Hadoop execution engine?** | **Apache Hadoop 3.3.6 Streaming MapReduce** (Single-Node HDFS in Docker). |
| **Hive execution engine?** | **Apache Hive 3.1.3** with isolated embedded Derby metastore. |
| **Total automated tests?** | **179 automated tests** (137 backend + 42 frontend), 100% passing. |
