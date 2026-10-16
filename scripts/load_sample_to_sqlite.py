"""
ProductPulse — Phase 4A: SQLite Data Loader Script
Transfers verified JSONL sample reviews into the SQLite analytical database
following strict checksum, provenance, deterministic identity, idempotency,
and atomic transaction safety protocols.
"""
import argparse
import datetime
import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Permanent project locks
CATEGORY_LOCK = "Cell_Phones_and_Accessories"
EXPECTED_DATASET_NAME = "McAuley-Lab/Amazon-Reviews-2023"

# Default relative paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RAW_PATH = PROJECT_ROOT / "data" / "raw" / "sample_reviews_cell_phones_25k.jsonl"
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "data" / "manifests" / "ingestion_manifest_phase2.json"
DEFAULT_DB_PATH = PROJECT_ROOT / "backend" / "db" / "productpulse.db"
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "backend" / "db" / "schema.sql"


def compute_file_sha256_and_bytes(file_path: Path) -> Tuple[str, int]:
    """
    Computes the SHA-256 digest and byte size of a file on disk.
    """
    hasher = hashlib.sha256()
    total_bytes = 0
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            hasher.update(chunk)
            total_bytes += len(chunk)
    return hasher.hexdigest(), total_bytes


def compute_canonical_review_hash(record: Dict[str, Any]) -> str:
    """
    Computes canonical SHA-256 hash across sorted JSON keys.
    """
    canonical_json_str = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical_json_str.encode("utf-8")).hexdigest()


def compute_deterministic_run_id(
    category: str,
    raw_sha256: str,
    dataset_name: str,
    manifest_version: str,
) -> str:
    """
    Constructs a deterministic run ID derived from immutable provenance attributes:
    sha256(category:raw_jsonl_sha256:dataset_name:manifest_version)[:16]
    """
    token = f"{category}:{raw_sha256}:{dataset_name}:{manifest_version}"
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]


def format_iso8601_utc_ms(timestamp_raw_ms: int) -> Tuple[str, float]:
    """
    Converts millisecond integer epoch into full-precision ISO-8601 UTC string (YYYY-MM-DDTHH:MM:SS.sssZ)
    and epoch seconds float.
    """
    epoch_seconds = timestamp_raw_ms / 1000.0
    dt = datetime.datetime.fromtimestamp(epoch_seconds, tz=datetime.timezone.utc)
    iso_str = dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    return iso_str, epoch_seconds


def verify_sqlite_foreign_keys(conn: sqlite3.Connection) -> None:
    """
    Asserts that foreign key enforcement is active.
    """
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys;")
    row = cur.fetchone()
    if not row or row[0] != 1:
        raise RuntimeError("PRAGMA foreign_keys is not active on SQLite connection.")


def ensure_schema_initialized(conn: sqlite3.Connection, schema_path: Path) -> None:
    """
    Applies schema.sql if core tables do not exist.
    """
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ingestion_runs';")
    if not cur.fetchone():
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found at: {schema_path}")
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)


def check_idempotent_noop(
    conn: sqlite3.Connection,
    run_id: str,
    raw_sha256: str,
    category: str,
    dataset_name: str,
    expected_admitted_count: int,
) -> bool:
    """
    Verifies ALL five no-op conditions specified in Section 9 of the data contract:
    1. Candidate run_id exists in ingestion_runs.
    2. Stored raw_jsonl_sha256 matches the raw file's newly computed checksum.
    3. Stored category matches expected category.
    4. Stored dataset_name matches manifest dataset identity.
    5. Stored admitted_records_count equals expected count, AND count in reviews table matches.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT run_id, raw_jsonl_sha256, category, dataset_name, admitted_records_count
        FROM ingestion_runs
        WHERE run_id = ?;
        """,
        (run_id,),
    )
    row = cur.fetchone()
    if not row:
        return False

    stored_run_id, stored_sha, stored_cat, stored_ds, stored_admitted = row

    if (
        stored_run_id == run_id
        and stored_sha == raw_sha256
        and stored_cat == category
        and stored_ds == dataset_name
        and stored_admitted == expected_admitted_count
    ):
        # Check actual row count in reviews table
        cur.execute("SELECT COUNT(*) FROM reviews WHERE ingestion_run_id = ?;", (run_id,))
        review_count = cur.fetchone()[0]
        if review_count == expected_admitted_count:
            return True

    return False


def load_dataset(
    raw_path: Path,
    manifest_path: Path,
    db_path: Path,
    schema_path: Path = DEFAULT_SCHEMA_PATH,
    replace_run: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Executes the validated JSONL-to-SQLite loading pipeline.
    """
    # -------------------------------------------------------------------------
    # 1. Pre-Import Verification
    # -------------------------------------------------------------------------
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw dataset file not found: {raw_path}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    manifest_category = manifest.get("category")
    if manifest_category != CATEGORY_LOCK:
        raise ValueError(
            f"Manifest category mismatch: expected '{CATEGORY_LOCK}', got '{manifest_category}'"
        )

    expected_sha256 = manifest["output_files"]["raw_jsonl_sha256"]
    expected_bytes = manifest["output_files"]["raw_jsonl_bytes"]
    expected_admitted_count = manifest["ingestion_outcomes"]["admitted_records_count"]
    dataset_name = manifest.get("dataset_name", EXPECTED_DATASET_NAME)
    manifest_version = manifest.get("manifest_version", "1.0")

    # Compute actual checksum and byte size of raw file
    computed_sha256, computed_bytes = compute_file_sha256_and_bytes(raw_path)

    if computed_sha256 != expected_sha256:
        raise ValueError(
            f"Raw dataset SHA-256 mismatch!\n"
            f"  Computed: {computed_sha256}\n"
            f"  Manifest: {expected_sha256}"
        )
    if computed_bytes != expected_bytes:
        raise ValueError(
            f"Raw dataset byte size mismatch!\n"
            f"  Computed: {computed_bytes} bytes\n"
            f"  Manifest: {expected_bytes} bytes"
        )

    # -------------------------------------------------------------------------
    # 2. Deterministic Dataset and Run Identity
    # -------------------------------------------------------------------------
    run_id = compute_deterministic_run_id(
        category=manifest_category,
        raw_sha256=computed_sha256,
        dataset_name=dataset_name,
        manifest_version=manifest_version,
    )

    # -------------------------------------------------------------------------
    # 3. Database Connection & Schema Verification
    # -------------------------------------------------------------------------
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.isolation_level = None  # Explicit SQL transaction control

    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        verify_sqlite_foreign_keys(conn)
        ensure_schema_initialized(conn, schema_path)

        # -------------------------------------------------------------------------
        # 4. Strict Idempotency / Already-Imported Check
        # -------------------------------------------------------------------------
        is_noop = check_idempotent_noop(
            conn=conn,
            run_id=run_id,
            raw_sha256=computed_sha256,
            category=manifest_category,
            dataset_name=dataset_name,
            expected_admitted_count=expected_admitted_count,
        )

        if is_noop and not replace_run:
            msg = (
                f"[IDEMPOTENT] Dataset identity '{run_id}', checksum, category, "
                f"and record count ({expected_admitted_count}) verified in database. "
                "Zero modifications made."
            )
            print(msg)
            return {
                "status": "idempotent_noop",
                "run_id": run_id,
                "admitted_records": expected_admitted_count,
                "message": msg,
            }

        # If run exists but no-op failed and replace_run is False -> refuse silent overwrite
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM ingestion_runs WHERE run_id = ?;", (run_id,))
        if cur.fetchone()[0] > 0 and not replace_run:
            raise RuntimeError(
                f"Dataset with run_id '{run_id}' already exists in ingestion_runs, "
                "but verification checks did not match. Refusing silent overwrite. "
                "Use --replace-run to execute a controlled replacement."
            )

        # -------------------------------------------------------------------------
        # 5. Record Streaming & In-Memory Staging
        # -------------------------------------------------------------------------
        products_to_insert: Set[str] = set()
        variants_to_insert: Set[Tuple[str, str]] = set()
        review_rows: List[Tuple[Any, ...]] = []
        hash_counts: Dict[str, int] = {}

        current_line = 0
        current_offset = 0

        with open(raw_path, "rb") as rf:
            for line_bytes in rf:
                current_line += 1
                line_len = len(line_bytes)
                line_offset = current_offset
                current_offset += line_len

                line_str = line_bytes.decode("utf-8", errors="replace").strip()
                if not line_str:
                    continue

                record = json.loads(line_str)

                parent_asin = record.get("parent_asin")
                asin = record.get("asin")
                user_id = record.get("user_id")
                rating = float(record["rating"])
                timestamp_raw = int(record["timestamp"])

                if not (1.0 <= rating <= 5.0):
                    raise ValueError(f"Rating out of bounds at line {current_line}: {rating}")

                # Primary Key & Duplicate Provenance
                canonical_hash = compute_canonical_review_hash(record)
                occurrence_idx = hash_counts.get(canonical_hash, 0)
                hash_counts[canonical_hash] = occurrence_idx + 1

                if occurrence_idx == 0:
                    review_id = canonical_hash
                else:
                    review_id = f"{canonical_hash}_#{occurrence_idx}"

                # Timestamp conversion
                review_ts_utc, review_epoch_sec = format_iso8601_utc_ms(timestamp_raw)

                # Optional / Derived fields
                raw_title = record.get("title")
                raw_text = record.get("text")
                is_blank_text = 1 if not (raw_text and raw_text.strip()) else 0

                helpful_vote = int(record.get("helpful_vote", 0) or 0)
                if helpful_vote < 0:
                    helpful_vote = 0

                verified_purchase = 1 if bool(record.get("verified_purchase")) else 0

                images_list = record.get("images", []) or []
                has_images = 1 if len(images_list) > 0 else 0
                raw_images_json = json.dumps(images_list, ensure_ascii=False)

                # Collect entities for staging
                products_to_insert.add(parent_asin)
                variants_to_insert.add((asin, parent_asin))

                review_rows.append((
                    review_id,
                    canonical_hash,
                    occurrence_idx,
                    parent_asin,
                    asin,
                    user_id,
                    rating,
                    raw_title,
                    raw_text,
                    timestamp_raw,
                    review_ts_utc,
                    review_epoch_sec,
                    helpful_vote,
                    verified_purchase,
                    raw_images_json,
                    has_images,
                    is_blank_text,
                    current_line,
                    line_offset,
                    line_len,
                    run_id,
                ))

        if len(review_rows) != expected_admitted_count:
            raise ValueError(
                f"Parsed review count ({len(review_rows)}) does not match expected "
                f"count ({expected_admitted_count})"
            )

        if dry_run:
            print(f"[DRY-RUN] Verified {len(review_rows)} reviews, {len(products_to_insert)} products. Zero DB writes.")
            return {
                "status": "dry_run_success",
                "run_id": run_id,
                "admitted_records": len(review_rows),
                "distinct_products": len(products_to_insert),
                "distinct_variants": len(variants_to_insert),
            }

        # -------------------------------------------------------------------------
        # 6. Atomic Transaction & Dependency-Order Staging
        # -------------------------------------------------------------------------
        try:
            conn.execute("BEGIN IMMEDIATE TRANSACTION;")

            # If replacing, clear prior reviews for this run_id
            if replace_run:
                conn.execute("DELETE FROM reviews WHERE ingestion_run_id = ?;", (run_id,))

            # Step A: INGESTION RUNS (Update existing on replace, or Insert)
            cur.execute("SELECT COUNT(*) FROM ingestion_runs WHERE run_id = ?;", (run_id,))
            run_already_exists = cur.fetchone()[0] > 0

            if run_already_exists and replace_run:
                conn.execute(
                    """
                    UPDATE ingestion_runs SET
                        manifest_version = ?, dataset_name = ?, category = ?, source_url = ?,
                        target_records = ?, max_body_bytes_cap = ?, cumulative_timeout_seconds = ?,
                        final_status = ?, content_range = ?, total_bytes_streamed = ?, admitted_records_count = ?,
                        total_lines_processed = ?, trailing_incomplete_bytes = ?, parse_errors_count = ?,
                        validation_errors_count = ?, duplicates_count = ?, unique_parent_asins_count = ?,
                        unique_asins_count = ?, unique_users_count = ?, raw_jsonl_path = ?, raw_jsonl_bytes = ?,
                        raw_jsonl_sha256 = ?, manifest_path = ?, start_utc = ?, end_utc = ?, elapsed_seconds = ?,
                        sampling_nature = ?, population_claims_allowed = ?
                    WHERE run_id = ?;
                    """,
                    (
                        manifest_version,
                        dataset_name,
                        manifest_category,
                        manifest.get("source_url", ""),
                        manifest["limits_enforced"]["target_records"],
                        manifest["limits_enforced"]["max_body_bytes_cap"],
                        manifest["limits_enforced"]["cumulative_timeout_seconds"],
                        manifest["transport_evidence"].get("final_status", 206),
                        manifest["transport_evidence"].get("content_range", ""),
                        manifest["transport_evidence"].get("total_bytes_streamed", 0),
                        expected_admitted_count,
                        manifest["ingestion_outcomes"].get("total_lines_processed", expected_admitted_count),
                        manifest["ingestion_outcomes"].get("trailing_incomplete_bytes", 0),
                        manifest["ingestion_outcomes"].get("parse_errors_count", 0),
                        manifest["ingestion_outcomes"].get("validation_errors_count", 0),
                        manifest["ingestion_outcomes"].get("duplicates_count", 0),
                        manifest["ingestion_outcomes"].get("unique_parent_asins_count", len(products_to_insert)),
                        manifest["ingestion_outcomes"].get("unique_asins_count", len(variants_to_insert)),
                        manifest["ingestion_outcomes"].get("unique_users_count", 0),
                        str(raw_path),
                        computed_bytes,
                        computed_sha256,
                        str(manifest_path),
                        manifest["ingestion_timestamps"].get("start_utc", ""),
                        manifest["ingestion_timestamps"].get("end_utc", ""),
                        manifest["ingestion_timestamps"].get("elapsed_seconds", 0.0),
                        manifest.get("academic_disclosures", {}).get("sampling_nature", "Bounded prefix sample"),
                        1 if manifest.get("academic_disclosures", {}).get("population_claims_allowed") else 0,
                        run_id,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO ingestion_runs (
                        run_id, manifest_version, dataset_name, category, source_url,
                        target_records, max_body_bytes_cap, cumulative_timeout_seconds,
                        final_status, content_range, total_bytes_streamed, admitted_records_count,
                        total_lines_processed, trailing_incomplete_bytes, parse_errors_count,
                        validation_errors_count, duplicates_count, unique_parent_asins_count,
                        unique_asins_count, unique_users_count, raw_jsonl_path, raw_jsonl_bytes,
                        raw_jsonl_sha256, manifest_path, start_utc, end_utc, elapsed_seconds,
                        sampling_nature, population_claims_allowed
                    ) VALUES (
                        ?, ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, ?
                    );
                    """,
                    (
                        run_id,
                        manifest_version,
                        dataset_name,
                        manifest_category,
                        manifest.get("source_url", ""),
                        manifest["limits_enforced"]["target_records"],
                        manifest["limits_enforced"]["max_body_bytes_cap"],
                        manifest["limits_enforced"]["cumulative_timeout_seconds"],
                        manifest["transport_evidence"].get("final_status", 206),
                        manifest["transport_evidence"].get("content_range", ""),
                        manifest["transport_evidence"].get("total_bytes_streamed", 0),
                        expected_admitted_count,
                        manifest["ingestion_outcomes"].get("total_lines_processed", expected_admitted_count),
                        manifest["ingestion_outcomes"].get("trailing_incomplete_bytes", 0),
                        manifest["ingestion_outcomes"].get("parse_errors_count", 0),
                        manifest["ingestion_outcomes"].get("validation_errors_count", 0),
                        manifest["ingestion_outcomes"].get("duplicates_count", 0),
                        manifest["ingestion_outcomes"].get("unique_parent_asins_count", len(products_to_insert)),
                        manifest["ingestion_outcomes"].get("unique_asins_count", len(variants_to_insert)),
                        manifest["ingestion_outcomes"].get("unique_users_count", 0),
                        str(raw_path),
                        computed_bytes,
                        computed_sha256,
                        str(manifest_path),
                        manifest["ingestion_timestamps"].get("start_utc", ""),
                        manifest["ingestion_timestamps"].get("end_utc", ""),
                        manifest["ingestion_timestamps"].get("elapsed_seconds", 0.0),
                        manifest.get("academic_disclosures", {}).get("sampling_nature", "Bounded prefix sample"),
                        1 if manifest.get("academic_disclosures", {}).get("population_claims_allowed") else 0,
                    ),
                )

            # Step B: PRODUCTS (INSERT OR IGNORE)
            product_params = [(p_asin, run_id) for p_asin in sorted(products_to_insert)]
            conn.executemany(
                """
                INSERT OR IGNORE INTO products (parent_asin, first_seen_run_id)
                VALUES (?, ?);
                """,
                product_params,
            )

            # Step C: PRODUCT VARIANTS (INSERT OR IGNORE)
            variant_params = [(v_asin, p_asin, run_id) for v_asin, p_asin in sorted(variants_to_insert)]
            conn.executemany(
                """
                INSERT OR IGNORE INTO product_variants (asin, parent_asin, first_seen_run_id)
                VALUES (?, ?, ?);
                """,
                variant_params,
            )

            # Step D: REVIEWS (INSERT)
            conn.executemany(
                """
                INSERT INTO reviews (
                    review_id, canonical_hash, occurrence_index, parent_asin, asin,
                    user_id, rating, raw_title, raw_text, timestamp_raw,
                    review_timestamp_utc, review_epoch_seconds, helpful_vote,
                    verified_purchase, raw_images_json, has_images, is_blank_text,
                    source_line_number, source_byte_offset, source_byte_length,
                    ingestion_run_id
                ) VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?
                );
                """,
                review_rows,
            )

            # Step E: Reconciliation Assertion
            cur.execute("SELECT COUNT(*) FROM reviews WHERE ingestion_run_id = ?;", (run_id,))
            inserted_count = cur.fetchone()[0]
            if inserted_count != expected_admitted_count:
                raise RuntimeError(
                    f"Reconciliation failure: expected {expected_admitted_count} reviews, "
                    f"but found {inserted_count} in database transaction."
                )

            # Step F: Commit
            conn.execute("COMMIT TRANSACTION;")

        except Exception as e:
            conn.execute("ROLLBACK TRANSACTION;")
            raise RuntimeError(f"Database insertion failed and was rolled back cleanly: {e}") from e

    finally:
        conn.close()

    print(f"[SUCCESS] Ingested {len(review_rows)} reviews into {db_path} (Run ID: {run_id}).")
    return {
        "status": "success",
        "run_id": run_id,
        "admitted_records": len(review_rows),
        "distinct_products": len(products_to_insert),
        "distinct_variants": len(variants_to_insert),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ProductPulse — Bounded JSONL to SQLite Analytical Loader"
    )
    parser.add_argument("--raw-path", type=Path, default=DEFAULT_RAW_PATH, help="Path to raw JSONL dataset")
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST_PATH, help="Path to ingestion manifest")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="Target SQLite database file path")
    parser.add_argument("--schema-path", type=Path, default=DEFAULT_SCHEMA_PATH, help="SQLite schema DDL file path")
    parser.add_argument("--replace-run", action="store_true", help="Perform safe, atomic replacement of existing run")
    parser.add_argument("--dry-run", action="store_true", help="Validate input dataset without writing to database")

    args = parser.parse_args()

    try:
        load_dataset(
            raw_path=args.raw_path,
            manifest_path=args.manifest_path,
            db_path=args.db_path,
            schema_path=args.schema_path,
            replace_run=args.replace_run,
            dry_run=args.dry_run,
        )
    except Exception as err:
        print(f"[ERROR] Loader execution failed: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
