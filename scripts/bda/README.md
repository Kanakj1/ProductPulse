# ProductPulse — Big Data Analytics Pipeline (Hadoop & Hive)

This directory contains the authentic Hadoop Streaming MapReduce and Apache Hive pipeline implementations for ProductPulse, processing the 25,000 Amazon Cell Phones & Accessories review sample (`data/raw/sample_reviews_cell_phones_25k.jsonl`).

## 1. Architecture Overview

```
data/raw/sample_reviews_cell_phones_25k.jsonl (25,000 records, 14.2 MB)
                           │
                           ▼
             HDFS Ingestion: /productpulse/input/
                           │
                           ▼
          Hadoop MapReduce Streaming Job
      Image: apache/hadoop:3.3.6 (Official Apache)
      Mapper:  scripts/bda/aspect_mapper.py (Python 2.7 & 3 compatible)
      Reducer: scripts/bda/aspect_reducer.py (Python 2.7 & 3 compatible)
                           │
                           ▼
        HDFS Output: /productpulse/output/part-00000
             (48,708 unique product-aspect aggregates)
                           │
                           ▼
        Local Persistence: data/bda/hadoop_output/
                           │
                           ▼
               Apache Hive SQL Analytics
            Script: scripts/bda/hive_analytics.hql
        External Table: productpulse_bda.product_aspect_metrics
```

## 2. Hadoop MapReduce Job Details

- **Container Image**: `apache/hadoop:3.3.6` (Image ID `62a22627f35a`)
- **Job ID**: `job_local1374248698_0001`
- **Execution Mode**: Single-node HDFS (`hdfs://127.0.0.1:9000`)
- **Exit Code**: `0` (Success)
- **HDFS Input Path**: `/productpulse/input/sample_reviews_cell_phones_25k.jsonl` (14,241,285 bytes)
- **HDFS Output Path**: `/productpulse/output` (`_SUCCESS`, `part-00000`, 2,150,939 bytes)
- **Map Input Records**: `25,000`
- **Map Output Records**: `59,621` (25,000 product review records + 26,032 aspect mention records + 8,589 no-aspect records)
- **Reduce Input Groups**: `48,708`
- **Reduce Output Records**: `48,708`

### Schema of `part-00000` (Tab-Separated):
| Column | Type | Description |
|---|---|---|
| `parent_asin` | STRING | Product identifier (e.g. `B0BBGGC8F2`) |
| `aspect` | STRING | Aspect name or meta-key (`build_durability`, `battery_charging`, `screen_display`, `camera_optics`, `connectivity_audio`, `performance_software`, `__ALL_REVIEWS__`, `__NO_ASPECT__`) |
| `review_count` | INT | Number of distinct reviews discussing this aspect for this product (or total product reviews for `__ALL_REVIEWS__`) |
| `avg_rating` | FLOAT | Mean source star rating (1.0 to 5.0) |
| `total_helpful_votes` | INT | Sum of helpful votes for matching reviews |
| `low_rating_count` | INT | Reviews with 1.0–2.0 stars (rating band, NOT text sentiment) |
| `med_rating_count` | INT | Reviews with 3.0 stars (rating band, NOT text sentiment) |
| `high_rating_count` | INT | Reviews with 4.0–5.0 stars (rating band, NOT text sentiment) |

## 3. Hive Analytics Query Plan (`scripts/bda/hive_analytics.hql`)

1. **Query 1 (Aspect Volumes)**: Total distinct review counts, exact review-weighted average star rating, and cumulative helpful votes across all six aspects.
2. **Query 2 (Top Products by Aspect)**: Products ranked by aspect review volume (distinct reviews discussing the aspect).
3. **Query 3 (Aspect Defect / Pain-Point Ranking)**: Lowest-rated product aspects with a statistical threshold (minimum 5 distinct aspect reviews).
4. **Query 4 (Rating Band Distributions)**: Distribution of 1–2 star, 3 star, and 4–5 star reviews across each aspect.
5. **Query 5 (Aspect Review Penetration)**: Ratio of distinct reviews mentioning aspect to total product reviews (`reviews_mentioning_aspect / total_product_reviews * 100%`). Because both numerator and denominator count distinct reviews, this is a true review penetration rate bounded between 0.0% and 100.0%.

## 4. Apache Hive 3.1.3 Analytics Details

- **Docker Image**: `productpulse-hive:3.1.3` (Built from `apache/hadoop:3.3.6` base with official Apache Hive 3.1.3 binary tarball + Guava 27 compatibility fix)
- **Metastore Database**: Isolated Derby metastore schema initialized at `/opt/hadoop/metastore_db`
- **Execution Engine**: MapReduce (in-process LocalJobRunner with 2048 MB JVM heap)
- **External Table**: `productpulse_bda.product_aspect_metrics` over `data/bda/hadoop_output/`
- **Execution Status**: `Exit Code 0` (All 5 queries executed with 100% success)
- **Full Execution Log**: `data/bda/hive_job_execution.log`

## 5. Exported Analytical Outputs (`data/bda/`)

| Artifact | Query Description | Rows | Key Highlights |
|---|---|---|---|
| `hive_query1_aspect_volumes.csv` | Overall Aspect Volume & Helpful Votes | 6 | `build_durability`: 10,846 reviews (weighted avg 4.15★), `battery_charging`: 4,514 reviews (weighted avg 4.18★), `screen_display`: 4,350 reviews (weighted avg 4.02★), `performance_software`: 2,509 reviews (weighted avg 4.19★), `camera_optics`: 2,256 reviews (weighted avg 4.07★), `connectivity_audio`: 1,557 reviews (weighted avg 3.94★) |
| `hive_query2_top_products.csv` | Top Products Ranked by Aspect Reviews | 25 | Top discussed product: `B07P9S6R9Y` (battery_charging, 30 distinct reviews), `B01415QHYW` (screen_display, 21 distinct reviews) |
| `hive_query3_aspect_ratings.csv` | Lowest-Rated Product Aspects (min 5 reviews) | 25 | Potential pain points: `B08KQ1L2W3` (build_durability, avg 2.60★), `B07H36MNN1` (screen_display, avg 2.71★, 13 helpful votes) |
| `hive_query4_rating_bands.csv` | Star Rating-Band Distributions by Aspect | 6 | `connectivity_audio`: highest low-rating share (16.96% 1–2★); `battery_charging`: highest high-rating share (78.80% 4–5★) |
| `hive_query5_aspect_cooccurrence.csv` | Aspect Review Penetration vs. Total Product Reviews | 25 | Penetration rate: `B0BVLY92D8` (100% build_durability penetration), `B084VNCBNZ` (93.3% battery_charging penetration) |

## 6. Verification and End-to-End Orchestration

Run independent MapReduce verification:
```powershell
python scripts/bda/verify_hadoop_output.py
```

Run entire BDA pipeline (Hadoop Streaming + Output Validation + Hive Analytics):
```powershell
.\scripts\bda\run_bda_pipeline.ps1
```

