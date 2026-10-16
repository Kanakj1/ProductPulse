#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ProductPulse — Extract Hive Analytics Query Outputs to Structured CSVs
Parses the authentic stdout log from `hive -f scripts/bda/hive_analytics.hql`
and formats each analytical query result as a clean CSV with standard headers.
"""

import io
import os
import re

HEADERS = [
    ("hive_query1_aspect_volumes.csv", [
        "aspect", "total_aspect_reviews", "weighted_avg_rating", "total_helpful_votes"
    ]),
    ("hive_query2_top_products.csv", [
        "parent_asin", "aspect", "aspect_review_count", "product_aspect_avg_rating", "total_helpful_votes"
    ]),
    ("hive_query3_aspect_ratings.csv", [
        "parent_asin", "aspect", "aspect_review_count", "avg_rating", "total_helpful_votes"
    ]),
    ("hive_query4_rating_bands.csv", [
        "aspect", "low_rating_reviews_1_to_2_stars", "med_rating_reviews_3_stars",
        "high_rating_reviews_4_to_5_stars", "total_aspect_reviews", "high_rating_pct", "low_rating_pct"
    ]),
    ("hive_query5_aspect_cooccurrence.csv", [
        "parent_asin", "total_product_reviews", "aspect", "reviews_mentioning_aspect",
        "aspect_review_penetration_pct", "aspect_avg_rating", "overall_product_avg_rating"
    ])
]

def parse_hive_log(log_path, output_dir):
    with io.open(log_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Pattern for Hive result blocks:
    # After MapReduce completion or OK, data rows follow until "Time taken: ... Fetched: N row(s)"
    blocks = re.findall(r"OK\n((?:[^\n]+\t[^\n]+\n)+)Time taken:[^\n]+Fetched: (\d+) row\(s\)", content)
    
    if len(blocks) != 5:
        print("[ERROR] Expected 5 query result blocks in Hive log, found: {}".format(len(blocks)))
        return False

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for i, (filename, cols) in enumerate(HEADERS):
        raw_rows, count = blocks[i]
        expected_count = int(count)
        lines = [line.strip().split("\t") for line in raw_rows.strip().split("\n") if line.strip()]
        
        if len(lines) != expected_count:
            print("[WARN] Row count mismatch in {}: got {} vs expected {}".format(filename, len(lines), expected_count))

        out_path = os.path.join(output_dir, filename)
        with io.open(out_path, "w", encoding="utf-8") as out_f:
            out_f.write(u",".join(cols) + u"\n")
            for line in lines:
                out_f.write(u",".join(line) + u"\n")

        print("[OK] Exported {}: {} rows -> {}".format(filename, len(lines), out_path))

    return True

if __name__ == "__main__":
    workspace = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_file = os.path.join(workspace, "data", "bda", "hive_job_execution.log")
    if not os.path.exists(log_file):
        log_file = os.path.join(workspace, "data", "bda", "hive_all_queries_raw.txt")
    out_dir = os.path.join(workspace, "data", "bda")
    parse_hive_log(log_file, out_dir)
