#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ProductPulse — Hadoop Streaming Reducer for Aspect Aggregation
Aggregates mapper outputs grouped by product and aspect.
Maintains per-product aspect dictionary to ensure exactly one aggregated row
per (parent_asin, aspect) pair.
Compatible with Python 2.7 and Python 3.x.

Input format (from Hadoop Streaming sort/shuffle):
  parent_asin \t aspect \t count \t rating \t helpful_votes \t is_low \t is_med \t is_high

Output format (tab-separated):
  parent_asin \t aspect \t review_count \t avg_rating \t total_helpful_votes \t low_rating_count \t med_rating_count \t high_rating_count
  (where review_count is the distinct review count for that product and aspect)
"""
import sys


def emit_product(product, aspects):
    if not product or not aspects:
        return
    for aspect in sorted(aspects.keys()):
        c = aspects[aspect]
        if c["count"] <= 0:
            continue
        avg_r = c["rating_sum"] / float(c["count"])
        sys.stdout.write(
            "{0}\t{1}\t{2}\t{3:.4f}\t{4}\t{5}\t{6}\t{7}\n".format(
                product,
                aspect,
                c["count"],
                avg_r,
                c["helpful_sum"],
                c["low_count"],
                c["med_count"],
                c["high_count"]
            )
        )


def main():
    current_product = None
    product_aspects = {}

    for line in sys.stdin:
        line_str = line.strip()
        if not line_str:
            continue

        parts = line_str.split("\t")
        if len(parts) < 8:
            continue

        parent_asin, aspect = parts[0], parts[1]
        try:
            cnt = int(parts[2])
            rating = float(parts[3])
            helpful = int(parts[4])
            is_low = int(parts[5])
            is_med = int(parts[6])
            is_high = int(parts[7])
        except (ValueError, IndexError):
            continue

        if current_product != parent_asin:
            if current_product is not None:
                emit_product(current_product, product_aspects)
            current_product = parent_asin
            product_aspects = {}

        if aspect not in product_aspects:
            product_aspects[aspect] = {
                "count": 0,
                "rating_sum": 0.0,
                "helpful_sum": 0,
                "low_count": 0,
                "med_count": 0,
                "high_count": 0,
            }

        product_aspects[aspect]["count"] += cnt
        product_aspects[aspect]["rating_sum"] += rating
        product_aspects[aspect]["helpful_sum"] += helpful
        product_aspects[aspect]["low_count"] += is_low
        product_aspects[aspect]["med_count"] += is_med
        product_aspects[aspect]["high_count"] += is_high

    if current_product is not None:
        emit_product(current_product, product_aspects)


if __name__ == "__main__":
    main()
