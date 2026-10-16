#!/usr/bin/env python3
"""
ProductPulse — Annotation Template Generator (Phase 7B)
Generates deterministic, unannotated Sample A (detection) and Sample B (sentiment)
templates from the verified local SQLite review database.

Outputs:
  data/annotation/sample_a_aspect_detection_template.csv
  data/annotation/sample_a_aspect_detection_template.jsonl
  data/annotation/sample_b_aspect_sentiment_template.csv
  data/annotation/sample_b_aspect_sentiment_template.jsonl
  data/annotation/sampling_manifest.json

Safety rules:
- Strictly read-only against the database.
- Refuses to overwrite existing files without explicit --overwrite flag.
- Generated templates are 100% unannotated (all human label fields blank in CSV and null in JSONL).
- Sentence IDs in Sample A and Sample B have strictly zero intersection.
- Connected component clusters and partitions are assigned and preserved.
"""
import argparse
import csv
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from typing import Dict, List, Set

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.nlp.partitioner import ConnectedComponentPartitioner
from backend.app.nlp.sampler import EvaluationSampler
from backend.app.nlp.schemas import AnnotationStatus, AspectName, DetectionStatus, SentimentLabel


def fetch_all_reviews(db_path: str) -> List[Dict]:
    """Reads all reviews from the local SQLite database in read-only mode."""
    uri = f"file:{os.path.abspath(db_path)}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT review_id, canonical_hash, occurrence_index, parent_asin, asin,
               user_id, rating, raw_title, raw_text, timestamp_raw,
               review_timestamp_utc, review_epoch_seconds, helpful_vote,
               verified_purchase, has_images, is_blank_text
        FROM reviews
        ORDER BY review_id ASC;
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def generate_templates(
    db_path: str = "backend/db/productpulse.db",
    output_dir: str = "data/annotation",
    sample_a_target: int = 200,
    sample_b_target: int = 200,
    seed: int = 42,
    overwrite: bool = False
) -> Dict:
    os.makedirs(output_dir, exist_ok=True)

    expected_files = [
        os.path.join(output_dir, "sample_a_aspect_detection_template.csv"),
        os.path.join(output_dir, "sample_a_aspect_detection_template.jsonl"),
        os.path.join(output_dir, "sample_b_aspect_sentiment_template.csv"),
        os.path.join(output_dir, "sample_b_aspect_sentiment_template.jsonl"),
        os.path.join(output_dir, "sampling_manifest.json"),
    ]

    for f in expected_files:
        if os.path.exists(f) and not overwrite:
            raise FileExistsError(
                f"Target file '{f}' already exists. Use --overwrite to replace existing templates."
            )

    reviews = fetch_all_reviews(db_path)
    if not reviews:
        raise RuntimeError("No reviews found in database.")

    # 1. Connected-component partitioning
    partitioner = ConnectedComponentPartitioner(seed=seed)
    assignments, part_manifest = partitioner.build_partitions(reviews)
    partition_map = {a.review_id: a.partition for a in assignments}
    cluster_map = {a.review_id: a.cluster_id for a in assignments}
    canonical_hash_map = {r['review_id']: r['canonical_hash'] for r in reviews}
    occurrence_index_map = {r['review_id']: r['occurrence_index'] for r in reviews}

    # 2. Sampler execution
    sampler = EvaluationSampler(seed=seed)

    # Sample A: 200 random sentences
    units_a, meta_a = sampler.sample_a_detection(reviews, target_size=sample_a_target)
    sample_a_sentence_ids = sorted(list({u.sentence_id for u in units_a}))

    # Sample B: 200 aspect-enriched sentences, strictly excluding Sample A sentence IDs
    units_b, meta_b = sampler.sample_b_sentiment(
        reviews,
        target_size=sample_b_target,
        exclude_sentence_ids=set(sample_a_sentence_ids)
    )
    sample_b_sentence_ids = sorted(list({u.sentence_id for u in units_b}))

    # Strict overlap assertion
    overlap = set(sample_a_sentence_ids).intersection(set(sample_b_sentence_ids))
    if overlap:
        raise RuntimeError(f"CRITICAL ERROR: Sentence overlap detected between Sample A and Sample B: {overlap}")

    # Build unique sentence map for Sample A wide CSV
    # Each sentence has 6 units in units_a
    sample_a_sentences: Dict[str, Dict] = {}
    for u in units_a:
        s_id = u.sentence_id
        if s_id not in sample_a_sentences:
            sample_a_sentences[s_id] = {
                "sentence_id": s_id,
                "review_id": u.review_id,
                "parent_asin": u.parent_asin,
                "asin": u.asin,
                "source_rating": u.source_rating,
                "sentence_text": u.sentence_text,
                "partition": partition_map.get(u.review_id, "unknown"),
                "cluster_id": cluster_map.get(u.review_id, "unknown"),
                "canonical_hash": canonical_hash_map.get(u.review_id, "unknown"),
                "occurrence_index": occurrence_index_map.get(u.review_id, 0),
            }

    # 3. Write Sample A Wide CSV (blank aspect columns)
    sample_a_csv_path = os.path.join(output_dir, "sample_a_aspect_detection_template.csv")
    with open(sample_a_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "sentence_id", "review_id", "parent_asin", "asin", "source_rating", "sentence_text",
            "build_durability", "battery_charging", "screen_display",
            "camera_optics", "connectivity_audio", "performance_software", "annotator_notes"
        ])
        for s_id in sample_a_sentence_ids:
            s_data = sample_a_sentences[s_id]
            writer.writerow([
                s_data["sentence_id"],
                s_data["review_id"],
                s_data["parent_asin"],
                s_data["asin"],
                s_data["source_rating"],
                s_data["sentence_text"],
                "", "", "", "", "", "", ""  # 6 blank aspect decision columns + blank notes
            ])

    # 4. Write Sample A Canonical JSONL (unannotated units)
    sample_a_jsonl_path = os.path.join(output_dir, "sample_a_aspect_detection_template.jsonl")
    with open(sample_a_jsonl_path, "w", encoding="utf-8") as f:
        for u in units_a:
            record = u.model_dump()
            record["partition"] = partition_map.get(u.review_id, "unknown")
            record["cluster_id"] = cluster_map.get(u.review_id, "unknown")
            record["canonical_hash"] = canonical_hash_map.get(u.review_id, "unknown")
            record["occurrence_index"] = occurrence_index_map.get(u.review_id, 0)
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # 5. Write Sample B Long CSV (blank confirmation and sentiment columns)
    sample_b_csv_path = os.path.join(output_dir, "sample_b_aspect_sentiment_template.csv")
    with open(sample_b_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "annotation_id", "sentence_id", "review_id", "parent_asin", "asin",
            "source_rating", "sentence_text", "target_aspect",
            "aspect_confirmed", "human_sentiment", "annotator_notes"
        ])
        for u in units_b:
            writer.writerow([
                u.annotation_id,
                u.sentence_id,
                u.review_id,
                u.parent_asin,
                u.asin,
                u.source_rating,
                u.sentence_text,
                u.aspect_name.value,
                "", "", ""  # blank aspect_confirmed, blank human_sentiment, blank notes
            ])

    # 6. Write Sample B Canonical JSONL (unannotated units)
    sample_b_jsonl_path = os.path.join(output_dir, "sample_b_aspect_sentiment_template.jsonl")
    with open(sample_b_jsonl_path, "w", encoding="utf-8") as f:
        for u in units_b:
            record = u.model_dump()
            record["partition"] = partition_map.get(u.review_id, "unknown")
            record["cluster_id"] = cluster_map.get(u.review_id, "unknown")
            record["canonical_hash"] = canonical_hash_map.get(u.review_id, "unknown")
            record["occurrence_index"] = occurrence_index_map.get(u.review_id, 0)
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # 7. Write Sampling Manifest
    manifest_path = os.path.join(output_dir, "sampling_manifest.json")
    manifest_data = {
        "manifest_version": "1.0",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "random_seed": seed,
        "database_path": db_path,
        "total_source_reviews": len(reviews),
        "total_source_parent_asins": len({r['parent_asin'] for r in reviews}),
        "sample_a": {
            "sample_type": "sample_a_detection",
            "target_sentence_count": sample_a_target,
            "actual_sentence_count": len(sample_a_sentence_ids),
            "total_annotation_units": len(units_a),
            "csv_path": sample_a_csv_path,
            "jsonl_path": sample_a_jsonl_path,
            "blank_human_decision_cells": len(sample_a_sentence_ids) * 6,
            "selection_rationale": meta_a.selection_rationale,
            "rating_tier_distribution": {
                "1-2_star": sum(1 for s in sample_a_sentences.values() if s["source_rating"] <= 2.5),
                "3_star": sum(1 for s in sample_a_sentences.values() if 2.5 < s["source_rating"] <= 3.5),
                "4-5_star": sum(1 for s in sample_a_sentences.values() if s["source_rating"] > 3.5),
            }
        },
        "sample_b": {
            "sample_type": "sample_b_sentiment",
            "target_sentence_count": sample_b_target,
            "actual_sentence_count": len(sample_b_sentence_ids),
            "total_annotation_units": len(units_b),
            "csv_path": sample_b_csv_path,
            "jsonl_path": sample_b_jsonl_path,
            "blank_human_decision_cells": len(units_b) * 2,
            "selection_rationale": meta_b.selection_rationale,
            "per_aspect_counts": {
                asp.value: sum(1 for u in units_b if u.aspect_name == asp) for asp in AspectName
            },
            "rating_tier_distribution": {
                "1-2_star": sum(1 for u in units_b if u.source_rating <= 2.5),
                "3_star": sum(1 for u in units_b if 2.5 < u.source_rating <= 3.5),
                "4-5_star": sum(1 for u in units_b if u.source_rating > 3.5),
            },
            "shortfalls": [s.model_dump() for s in meta_b.shortfalls]
        },
        "overlap_audit": {
            "sample_a_sentence_count": len(sample_a_sentence_ids),
            "sample_b_sentence_count": len(sample_b_sentence_ids),
            "overlapping_sentence_count": len(overlap),
            "disjoint_guarantee_met": len(overlap) == 0
        },
        "academic_disclosure": {
            "status": "Student pilot benchmark",
            "population_prevalence_claim": False,
            "limitations": "Sample B is keyword-enriched and stratifies rating tiers intentionally; aspect frequencies do not reflect market-wide prevalence."
        }
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    return manifest_data


def main():
    parser = argparse.ArgumentParser(description="Generate unannotated Phase 7B evaluation templates.")
    parser.add_argument("--db", default="backend/db/productpulse.db", help="Path to SQLite database")
    parser.add_argument("--output-dir", default="data/annotation", help="Output directory for templates")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    parser.add_argument("--sample-a", type=int, default=200, help="Target sentence count for Sample A")
    parser.add_argument("--sample-b", type=int, default=200, help="Target sentence count for Sample B")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing template files")

    args = parser.parse_args()
    try:
        manifest = generate_templates(
            db_path=args.db,
            output_dir=args.output_dir,
            sample_a_target=args.sample_a,
            sample_b_target=args.sample_b,
            seed=args.seed,
            overwrite=args.overwrite
        )
        print("[SUCCESS] Phase 7B templates generated successfully:")
        print(f"  Sample A: {manifest['sample_a']['actual_sentence_count']} sentences, {manifest['sample_a']['total_annotation_units']} units")
        print(f"  Sample B: {manifest['sample_b']['actual_sentence_count']} sentences, {manifest['sample_b']['total_annotation_units']} units")
        print(f"  Sentence overlap: {manifest['overlap_audit']['overlapping_sentence_count']} (Disjoint: {manifest['overlap_audit']['disjoint_guarantee_met']})")
        print(f"  Manifest written to: {os.path.join(args.output_dir, 'sampling_manifest.json')}")
    except Exception as e:
        print(f"[ERROR] Failed to generate templates: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
