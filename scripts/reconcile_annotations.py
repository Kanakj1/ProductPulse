#!/usr/bin/env python3
"""
ProductPulse — Safe Annotation Reconciliation Tool (Phase 7B)
Reconciles completed human annotation CSVs with their canonical JSONL templates.

Safeguards:
1. Never overwrites the source CSV or the canonical template.
2. Output path must be distinct and will refuse to overwrite without --overwrite.
3. Strict identifier parity (no missing, extra, duplicate, or mismatched IDs).
4. Verifies exact sentence text equality; aborts on any mismatch without rewriting.
5. Controlled vocabulary validation:
   - Sample A: aspect decisions must be '1'/'present' or '0'/'absent'. Blanks remain unannotated.
   - Sample B: aspect_confirmed must be '1'/'present' or '0'/'absent'.
     If absent, sentiment must be null.
     If present, sentiment must be in {'positive', 'neutral', 'negative', 'uncertain/unclassified'}.
6. Validates every reconciled record using AnnotationUnit.model_validate().
7. Reports completed, incomplete, invalid, and rejected records separately.
"""
import argparse
import csv
import json
import os
import sqlite3
import sys
from typing import Dict, List, Optional, Set, Tuple

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.nlp.schemas import (
    AnnotationStatus,
    AnnotationUnit,
    AspectName,
    DetectionStatus,
    SentimentLabel
)


class ReconciliationError(ValueError):
    """Raised when reconciliation encounters a integrity violation, text alteration, or invalid schema state."""
    pass


def verify_sentence_provenance_against_db(
    db_path: str,
    units: List[Dict]
) -> None:
    """
    Verifies that for each canonical unit:
    1. The source review exists in the SQLite database.
    2. The char_start:char_end slice of raw_text (or raw_title fallback)
       exactly matches canon['sentence_text'].
    3. Offsets are non-negative, valid, and within text boundaries.

    Database is opened read-only (mode=ro) using parameterized SQL queries.
    """
    if not os.path.exists(db_path):
        raise ReconciliationError(f"Verification database not found: '{db_path}'.")

    uri = f"file:{os.path.abspath(db_path)}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    review_cache: Dict[str, Tuple[Optional[str], Optional[str]]] = {}

    try:
        for u in units:
            r_id = u.get("review_id")
            unit_id = u.get("annotation_id") or u.get("sentence_id") or "unknown_unit"
            if not r_id:
                raise ReconciliationError(f"Canonical unit '{unit_id}' missing 'review_id'.")

            if r_id not in review_cache:
                cursor.execute(
                    "SELECT raw_text, raw_title FROM reviews WHERE review_id = ?",
                    (r_id,)
                )
                row = cursor.fetchone()
                if not row:
                    raise ReconciliationError(
                        f"Database provenance check failed: review_id '{r_id}' not found in database '{db_path}'."
                    )
                review_cache[r_id] = (row["raw_text"], row["raw_title"])

            raw_text, raw_title = review_cache[r_id]

            # Primary source text is raw_text; fallback to raw_title if raw_text is empty/whitespace
            if raw_text is not None and raw_text.strip():
                source_text = raw_text
            elif raw_title is not None and raw_title.strip():
                source_text = raw_title
            else:
                source_text = ""

            char_start = u.get("char_start")
            char_end = u.get("char_end")

            if char_start is None or char_end is None:
                raise ReconciliationError(
                    f"Unit '{unit_id}' is missing character offsets char_start/char_end."
                )

            if not isinstance(char_start, int) or not isinstance(char_end, int):
                raise ReconciliationError(
                    f"Unit '{unit_id}' has non-integer character offsets: [{char_start}:{char_end}]."
                )

            if char_start < 0 or char_end < 0 or char_start > char_end or char_end > len(source_text):
                raise ReconciliationError(
                    f"Invalid character offsets [{char_start}:{char_end}] for review '{r_id}' "
                    f"of length {len(source_text)} (unit '{unit_id}')."
                )

            extracted = source_text[char_start:char_end]
            if extracted != u.get("sentence_text"):
                # Check title fallback in case body was non-empty but title was explicitly segmented
                if raw_title and 0 <= char_start < char_end <= len(raw_title) and raw_title[char_start:char_end] == u.get("sentence_text"):
                    continue

                raise ReconciliationError(
                    f"Database provenance check failed: sentence text mismatch for unit '{unit_id}'!\n"
                    f"  Canonical sentence: {repr(u.get('sentence_text'))}\n"
                    f"  Database slice:     {repr(extracted)}\n"
                    f"  Offsets:            [{char_start}:{char_end}] in review '{r_id}'"
                )
    finally:
        conn.close()


def normalize_presence(val: Optional[str]) -> Optional[bool]:
    """Normalizes human entry to True (present), False (absent), or None (unannotated/blank)."""
    if val is None:
        return None
    s = str(val).strip().lower()
    if not s:
        return None
    if s in {"1", "true", "present", "yes", "y"}:
        return True
    if s in {"0", "false", "absent", "no", "n"}:
        return False
    raise ReconciliationError(f"Invalid presence value: '{val}'. Must be 1/present or 0/absent.")


def normalize_sentiment(val: Optional[str]) -> Optional[SentimentLabel]:
    """Normalizes human sentiment entry to SentimentLabel or None."""
    if val is None:
        return None
    s = str(val).strip().lower()
    if not s:
        return None
    if s in {"pos", "positive"}:
        return SentimentLabel.POSITIVE
    if s in {"neu", "neutral"}:
        return SentimentLabel.NEUTRAL
    if s in {"neg", "negative"}:
        return SentimentLabel.NEGATIVE
    if s in {"uncertain", "unclassified", "uncertain/unclassified", "ambiguous", "?"}:
        return SentimentLabel.UNCERTAIN_UNCLASSIFIED
    raise ReconciliationError(
        f"Invalid sentiment label: '{val}'. Must be 'positive', 'neutral', 'negative', or 'uncertain/unclassified'."
    )


def reconcile_sample_a(
    csv_path: str,
    canonical_jsonl_path: str,
    output_jsonl_path: str,
    db_path: Optional[str] = "backend/db/productpulse.db",
    overwrite: bool = False
) -> Dict:
    """
    Reconciles Sample A wide CSV (6 aspect columns per sentence) with canonical template units.
    """
    if os.path.abspath(csv_path) == os.path.abspath(output_jsonl_path):
        raise ReconciliationError("Output path cannot be the same as input CSV.")
    if os.path.abspath(canonical_jsonl_path) == os.path.abspath(output_jsonl_path):
        raise ReconciliationError("Output path cannot be the same as canonical template JSONL.")
    if os.path.exists(output_jsonl_path) and not overwrite:
        raise FileExistsError(f"Output file '{output_jsonl_path}' exists. Use --overwrite to replace.")

    # 1. Load canonical template units
    canonical_units: Dict[str, Dict] = {}
    with open(canonical_jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            canonical_units[rec["annotation_id"]] = rec

    # 2. Read human CSV rows
    csv_sentences: Dict[str, Dict] = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            s_id = row.get("sentence_id")
            if not s_id:
                raise ReconciliationError("CSV row missing 'sentence_id'.")
            if s_id in csv_sentences:
                raise ReconciliationError(f"Duplicate sentence_id in CSV: '{s_id}'.")
            csv_sentences[s_id] = row

    # 3. Verify sentence ID set equality
    canonical_sentence_ids = {u["sentence_id"] for u in canonical_units.values()}
    csv_sentence_ids = set(csv_sentences.keys())

    missing_in_csv = canonical_sentence_ids - csv_sentence_ids
    extra_in_csv = csv_sentence_ids - canonical_sentence_ids
    if missing_in_csv:
        raise ReconciliationError(f"CSV is missing {len(missing_in_csv)} sentences from canonical template: {list(missing_in_csv)[:3]}")
    if extra_in_csv:
        raise ReconciliationError(f"CSV contains {len(extra_in_csv)} extra sentences not in canonical template: {list(extra_in_csv)[:3]}")

    # 4. Optional independent SQLite read-only provenance verification
    if db_path is not None:
        verify_sentence_provenance_against_db(db_path, list(canonical_units.values()))

    # 5. Reconcile each unit
    reconciled_units: List[AnnotationUnit] = []
    completed_decisions = 0
    unannotated_decisions = 0

    aspects = [a.value for a in AspectName]

    for ann_id, canon in sorted(canonical_units.items()):
        s_id = canon["sentence_id"]
        csv_row = csv_sentences[s_id]

        # Verify immutable metadata fields against canonical
        for field in ("sentence_id", "review_id", "parent_asin", "asin"):
            if csv_row.get(field) != canon.get(field):
                raise ReconciliationError(
                    f"Provenance tampering detected in sentence '{s_id}': "
                    f"field '{field}' mismatch (CSV='{csv_row.get(field)}', canonical='{canon.get(field)}')."
                )

        try:
            csv_rating = float(csv_row.get("source_rating"))
            canon_rating = float(canon.get("source_rating"))
        except (ValueError, TypeError):
            raise ReconciliationError(
                f"Invalid source_rating in CSV for sentence '{s_id}': '{csv_row.get('source_rating')}'."
            )
        if csv_rating != canon_rating:
            raise ReconciliationError(
                f"Provenance tampering detected in sentence '{s_id}': "
                f"field 'source_rating' mismatch (CSV={csv_rating}, canonical={canon_rating})."
            )

        # Optional metadata fields if present in CSV
        for opt_field in ("canonical_hash", "partition", "cluster_id"):
            if opt_field in csv_row and csv_row[opt_field] != canon.get(opt_field):
                raise ReconciliationError(
                    f"Provenance tampering detected in sentence '{s_id}': "
                    f"field '{opt_field}' mismatch (CSV='{csv_row[opt_field]}', canonical='{canon.get(opt_field)}')."
                )

        if "occurrence_index" in csv_row:
            try:
                csv_occ = int(csv_row["occurrence_index"])
                canon_occ = int(canon.get("occurrence_index", 0))
            except (ValueError, TypeError):
                raise ReconciliationError(
                    f"Invalid occurrence_index in CSV for sentence '{s_id}': '{csv_row.get('occurrence_index')}'."
                )
            if csv_occ != canon_occ:
                raise ReconciliationError(
                    f"Provenance tampering detected in sentence '{s_id}': "
                    f"field 'occurrence_index' mismatch (CSV={csv_occ}, canonical={canon_occ})."
                )

        # Verify text immutability
        if csv_row.get("sentence_text") != canon.get("sentence_text"):
            raise ReconciliationError(
                f"Sentence text alteration detected in row {s_id}!\n"
                f"  Canonical: {repr(canon['sentence_text'])}\n"
                f"  CSV:       {repr(csv_row.get('sentence_text'))}\n"
                "Reconciliation aborted. Sentence text must never be edited."
            )

        target_aspect = canon["aspect_name"]
        raw_val = csv_row.get(target_aspect)
        notes = csv_row.get("annotator_notes", "").strip() or canon.get("notes")

        presence = normalize_presence(raw_val)

        if presence is None:
            # Blank human cell -> remains unannotated
            unannotated_decisions += 1
            ann_status = AnnotationStatus.UNANNOTATED
            det_status = DetectionStatus.ABSENT
            sent_label = None
        else:
            completed_decisions += 1
            ann_status = AnnotationStatus.ANNOTATED
            det_status = DetectionStatus.PRESENT if presence else DetectionStatus.ABSENT
            sent_label = None  # Sample A has no sentiment evaluation

        unit_dict = dict(canon)
        unit_dict["annotation_status"] = ann_status
        unit_dict["detection_status"] = det_status
        unit_dict["sentiment_label"] = sent_label
        unit_dict["notes"] = notes

        # Strict Pydantic validation
        validated_unit = AnnotationUnit.model_validate(unit_dict)
        reconciled_units.append(validated_unit)

    # 6. Write reconciled output
    with open(output_jsonl_path, "w", encoding="utf-8") as f:
        for u in reconciled_units:
            f.write(u.model_dump_json() + "\n")

    return {
        "sample": "sample_a_detection",
        "total_units": len(reconciled_units),
        "total_sentences": len(csv_sentence_ids),
        "completed_decisions": completed_decisions,
        "unannotated_decisions": unannotated_decisions,
        "output_path": output_jsonl_path
    }


def reconcile_sample_b(
    csv_path: str,
    canonical_jsonl_path: str,
    output_jsonl_path: str,
    db_path: Optional[str] = "backend/db/productpulse.db",
    overwrite: bool = False
) -> Dict:
    """
    Reconciles Sample B long CSV (aspect_confirmed, human_sentiment) with canonical template units.
    """
    if os.path.abspath(csv_path) == os.path.abspath(output_jsonl_path):
        raise ReconciliationError("Output path cannot be the same as input CSV.")
    if os.path.abspath(canonical_jsonl_path) == os.path.abspath(output_jsonl_path):
        raise ReconciliationError("Output path cannot be the same as canonical template JSONL.")
    if os.path.exists(output_jsonl_path) and not overwrite:
        raise FileExistsError(f"Output file '{output_jsonl_path}' exists. Use --overwrite to replace.")

    # 1. Load canonical template units
    canonical_units: Dict[str, Dict] = {}
    with open(canonical_jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            canonical_units[rec["annotation_id"]] = rec

    # 2. Read human CSV rows
    csv_units: Dict[str, Dict] = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ann_id = row.get("annotation_id")
            if not ann_id:
                raise ReconciliationError("CSV row missing 'annotation_id'.")
            if ann_id in csv_units:
                raise ReconciliationError(f"Duplicate annotation_id in CSV: '{ann_id}'.")
            csv_units[ann_id] = row

    # 3. Check ID parity
    canon_ids = set(canonical_units.keys())
    csv_ids = set(csv_units.keys())
    missing_in_csv = canon_ids - csv_ids
    extra_in_csv = csv_ids - canon_ids
    if missing_in_csv:
        raise ReconciliationError(f"CSV is missing {len(missing_in_csv)} annotation units: {list(missing_in_csv)[:3]}")
    if extra_in_csv:
        raise ReconciliationError(f"CSV has {len(extra_in_csv)} extra annotation units: {list(extra_in_csv)[:3]}")

    # 4. Optional independent SQLite read-only provenance verification
    if db_path is not None:
        verify_sentence_provenance_against_db(db_path, list(canonical_units.values()))

    # 5. Reconcile units
    reconciled_units: List[AnnotationUnit] = []
    completed_records = 0
    unannotated_records = 0
    confirmed_absent_count = 0
    confirmed_present_count = 0

    for ann_id, canon in sorted(canonical_units.items()):
        csv_row = csv_units[ann_id]

        # Verify immutable metadata fields against canonical
        for field in ("annotation_id", "sentence_id", "review_id", "parent_asin", "asin"):
            if csv_row.get(field) != canon.get(field):
                raise ReconciliationError(
                    f"Provenance tampering detected in unit '{ann_id}': "
                    f"field '{field}' mismatch (CSV='{csv_row.get(field)}', canonical='{canon.get(field)}')."
                )

        # Target aspect in Sample B
        target_asp = canon.get("aspect_name")
        if isinstance(target_asp, AspectName):
            target_asp = target_asp.value
        if csv_row.get("target_aspect") != target_asp:
            raise ReconciliationError(
                f"Provenance tampering detected in unit '{ann_id}': "
                f"field 'target_aspect' mismatch (CSV='{csv_row.get('target_aspect')}', canonical='{target_asp}')."
            )

        try:
            csv_rating = float(csv_row.get("source_rating"))
            canon_rating = float(canon.get("source_rating"))
        except (ValueError, TypeError):
            raise ReconciliationError(
                f"Invalid source_rating in CSV for unit '{ann_id}': '{csv_row.get('source_rating')}'."
            )
        if csv_rating != canon_rating:
            raise ReconciliationError(
                f"Provenance tampering detected in unit '{ann_id}': "
                f"field 'source_rating' mismatch (CSV={csv_rating}, canonical={canon_rating})."
            )

        # Optional metadata fields if present in CSV
        for opt_field in ("canonical_hash", "partition", "cluster_id"):
            if opt_field in csv_row and csv_row[opt_field] != canon.get(opt_field):
                raise ReconciliationError(
                    f"Provenance tampering detected in unit '{ann_id}': "
                    f"field '{opt_field}' mismatch (CSV='{csv_row[opt_field]}', canonical='{canon.get(opt_field)}')."
                )

        if "occurrence_index" in csv_row:
            try:
                csv_occ = int(csv_row["occurrence_index"])
                canon_occ = int(canon.get("occurrence_index", 0))
            except (ValueError, TypeError):
                raise ReconciliationError(
                    f"Invalid occurrence_index in CSV for unit '{ann_id}': '{csv_row.get('occurrence_index')}'."
                )
            if csv_occ != canon_occ:
                raise ReconciliationError(
                    f"Provenance tampering detected in unit '{ann_id}': "
                    f"field 'occurrence_index' mismatch (CSV={csv_occ}, canonical={canon_occ})."
                )

        # Verify text immutability
        if csv_row.get("sentence_text") != canon.get("sentence_text"):
            raise ReconciliationError(
                f"Sentence text alteration detected in unit {ann_id}!\n"
                f"  Canonical: {repr(canon['sentence_text'])}\n"
                f"  CSV:       {repr(csv_row.get('sentence_text'))}\n"
                "Reconciliation aborted. Sentence text must never be edited."
            )

        raw_conf = csv_row.get("aspect_confirmed")
        raw_sent = csv_row.get("human_sentiment")
        notes = csv_row.get("annotator_notes", "").strip() or canon.get("notes")

        presence = normalize_presence(raw_conf)
        sentiment = normalize_sentiment(raw_sent)

        if presence is None and sentiment is None:
            # Completely blank row -> remains unannotated
            ann_status = AnnotationStatus.UNANNOTATED
            det_status = DetectionStatus.PRESENT  # Keyword-matched candidate
            sent_label = None
            unannotated_records += 1
        elif presence is False:
            # Human confirmed aspect is ABSENT
            # In accordance with schema rule 1: absent aspect MUST have null sentiment
            if sentiment is not None:
                raise ReconciliationError(
                    f"Invalid record {ann_id}: aspect confirmed absent (0), but human_sentiment '{sentiment.value}' was entered. "
                    "An absent aspect must have null sentiment."
                )
            ann_status = AnnotationStatus.ANNOTATED
            det_status = DetectionStatus.ABSENT
            sent_label = None
            completed_records += 1
            confirmed_absent_count += 1
        elif presence is True:
            # Human confirmed aspect is PRESENT
            # Requires valid explicit sentiment
            if sentiment is None:
                raise ReconciliationError(
                    f"Incomplete record {ann_id}: aspect confirmed present (1), but human_sentiment is blank. "
                    "Present aspects require an explicit sentiment label."
                )
            ann_status = AnnotationStatus.ANNOTATED
            det_status = DetectionStatus.PRESENT
            sent_label = sentiment
            completed_records += 1
            confirmed_present_count += 1
        else:
            # presence is None, but sentiment was entered -> Incomplete presence confirmation
            raise ReconciliationError(
                f"Incomplete record {ann_id}: sentiment '{sentiment.value}' was entered, but aspect_confirmed is blank. "
                "Human must explicitly confirm aspect presence (1) or absence (0)."
            )

        unit_dict = dict(canon)
        unit_dict["annotation_status"] = ann_status
        unit_dict["detection_status"] = det_status
        unit_dict["sentiment_label"] = sent_label
        unit_dict["notes"] = notes

        validated_unit = AnnotationUnit.model_validate(unit_dict)
        reconciled_units.append(validated_unit)

    # 6. Write reconciled output
    with open(output_jsonl_path, "w", encoding="utf-8") as f:
        for u in reconciled_units:
            f.write(u.model_dump_json() + "\n")

    return {
        "sample": "sample_b_sentiment",
        "total_units": len(reconciled_units),
        "completed_records": completed_records,
        "unannotated_records": unannotated_records,
        "confirmed_present": confirmed_present_count,
        "confirmed_absent": confirmed_absent_count,
        "output_path": output_jsonl_path
    }


def main():
    parser = argparse.ArgumentParser(description="Reconcile human annotation CSVs with canonical JSONL templates.")
    parser.add_argument("--sample", required=True, choices=["A", "B"], help="Sample type to reconcile: 'A' or 'B'")
    parser.add_argument("--csv", required=True, help="Path to completed human-edited CSV")
    parser.add_argument("--canonical", required=True, help="Path to canonical template JSONL")
    parser.add_argument("--output", required=True, help="Output path for reconciled JSONL")
    parser.add_argument("--db", default="backend/db/productpulse.db", help="Path to SQLite database for source text verification (default: backend/db/productpulse.db)")
    parser.add_argument("--skip-db-verify", action="store_true", help="Skip SQLite database source text verification")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output file")

    args = parser.parse_args()
    db_to_use = None if args.skip_db_verify else args.db
    try:
        if args.sample == "A":
            summary = reconcile_sample_a(
                csv_path=args.csv,
                canonical_jsonl_path=args.canonical,
                output_jsonl_path=args.output,
                db_path=db_to_use,
                overwrite=args.overwrite
            )
        else:
            summary = reconcile_sample_b(
                csv_path=args.csv,
                canonical_jsonl_path=args.canonical,
                output_jsonl_path=args.output,
                db_path=db_to_use,
                overwrite=args.overwrite
            )
        print(f"[SUCCESS] Reconciled {args.sample} annotations successfully:")
        for k, v in summary.items():
            print(f"  {k}: {v}")
    except Exception as e:
        print(f"[ERROR] Reconciliation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
