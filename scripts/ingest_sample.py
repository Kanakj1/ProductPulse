"""
ProductPulse — Bounded Review Ingestion Script (scripts/ingest_sample.py)

Controlled, bounded retrieval and validation of customer review records from
the official McAuley-Lab/Amazon-Reviews-2023 dataset, category Cell_Phones_and_Accessories.

Guarantees:
- Bounded HTTP Range requests (capped response-body transfer, default 15 MiB).
- Cumulative wall-clock deadline tracking across redirects and chunk reads.
- Rejection of non-206 responses; immediate abort on HTTP 200 to prevent unbounded downloads.
- Validation of Content-Range headers and expected total remote file size.
- Exact line-offset and line-number provenance tracking.
- Preservation of raw JSON records and original source fields without pruning.
- Deterministic primary key generation: SHA-256 over canonical JSON serialization.
- Preservation of duplicate records via occurrence ordinals and manifest auditing.
- Timestamp unit anomaly detection (milliseconds vs. seconds vs. invalid).
- Protection against silent overwriting of existing output files.
- Fully testable offline via dependency injection; zero network activity on import.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, BinaryIO, Callable, Dict, Iterator, List, Optional, Set, Tuple

# Official Dataset Constants (Category Lock & Provenance)
OFFICIAL_SOURCE_URL = (
    "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/main/"
    "raw/review_categories/Cell_Phones_and_Accessories.jsonl"
)
CATEGORY_LOCK = "Cell_Phones_and_Accessories"
DOCUMENTED_TOTAL_SIZE = 9342568048  # Exact byte size observed in official tree & HEAD

# Default Guardrails
DEFAULT_TARGET_RECORDS = 25000
DEFAULT_MAX_BODY_BYTES = 15728640  # 15.0 MiB
DEFAULT_CUMULATIVE_TIMEOUT = 30.0  # seconds
DEFAULT_CHUNK_SIZE = 65536  # 64 KiB buffer

DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DEFAULT_OUTPUT_RAW = os.path.join(DEFAULT_DATA_DIR, "raw", "sample_reviews_cell_phones_25k.jsonl")
DEFAULT_OUTPUT_MANIFEST = os.path.join(DEFAULT_DATA_DIR, "manifests", "ingestion_manifest_phase2.json")


class TimestampAnomalyError(ValueError):
    """Raised when a timestamp value cannot be classified as valid seconds or milliseconds."""
    pass


def classify_timestamp(raw_val: Any) -> Tuple[bool, str, Optional[float], Optional[str]]:
    """
    Validates and classifies a Unix timestamp without silent corruption.

    Returns:
        (is_valid, unit_label, normalized_seconds, anomaly_message)
        where unit_label is in {'MILLISECONDS', 'SECONDS', 'ANOMALY'}.
    """
    if raw_val is None:
        return False, "ANOMALY", None, "Timestamp is null/missing"

    try:
        val = int(raw_val)
    except (TypeError, ValueError):
        return False, "ANOMALY", None, f"Timestamp is non-integer: {raw_val!r}"

    # Plausible epoch ranges for Amazon review history (approx. 1995 to 2035)
    # Seconds range: 788918400 (1995-01-01) to 2051222400 (2035-01-01) -> 9-10 digits
    # Milliseconds range: 788918400000 to 2051222400000 -> 12-13 digits

    if 788918400000 <= val <= 2051222400000:
        return True, "MILLISECONDS", val / 1000.0, None
    elif 788918400 <= val <= 2051222400:
        return True, "SECONDS", float(val), None
    else:
        return False, "ANOMALY", None, f"Timestamp value out of plausible epoch bounds: {val}"


def compute_canonical_review_id(record: Dict[str, Any]) -> str:
    """
    Computes a deterministic primary key by hashing the entire parsed record
    using canonical JSON serialization (sorted keys, compact separators).
    """
    canonical_json_str = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical_json_str.encode("utf-8")).hexdigest()


def validate_review_record(record: Any) -> Tuple[bool, List[str]]:
    """
    Validates the structure and data types of a parsed review JSON record.
    """
    errors: List[str] = []
    if not isinstance(record, dict):
        return False, ["Record is not a JSON object/dict"]

    # Mandatory identity & join keys
    parent_asin = record.get("parent_asin")
    if not parent_asin or not isinstance(parent_asin, str) or not parent_asin.strip():
        errors.append("Missing or invalid 'parent_asin'")

    asin = record.get("asin")
    if not asin or not isinstance(asin, str) or not asin.strip():
        errors.append("Missing or invalid 'asin'")

    user_id = record.get("user_id")
    if not user_id or not isinstance(user_id, str) or not user_id.strip():
        errors.append("Missing or invalid 'user_id'")

    # Rating validation
    rating = record.get("rating")
    if rating is None:
        errors.append("Missing 'rating'")
    else:
        try:
            r_val = float(rating)
            if not (1.0 <= r_val <= 5.0):
                errors.append(f"Rating {r_val} outside [1.0, 5.0] range")
        except (TypeError, ValueError):
            errors.append(f"Rating is non-numeric: {rating!r}")

    # Text validation (can be empty string for rating-only entries, but must be string if present)
    text = record.get("text")
    if text is not None and not isinstance(text, str):
        errors.append("Field 'text' must be a string or null")

    # Timestamp validation
    ts_val = record.get("timestamp")
    is_valid_ts, unit_label, _, ts_err = classify_timestamp(ts_val)
    if not is_valid_ts:
        errors.append(f"Timestamp anomaly: {ts_err}")

    return len(errors) == 0, errors


class IngestionByteStreamParser:
    """
    Incrementally parses complete newline-delimited JSONL records from an incoming
    byte stream, preserving exact line numbers, byte offsets, and raw source records.
    """

    def __init__(self, target_records: int):
        self.target_records = target_records
        self.buffer = bytearray()
        self.global_byte_offset = 0
        self.line_number = 0

        self.admitted_records: List[Dict[str, Any]] = []
        self.parse_errors: List[Dict[str, Any]] = []
        self.validation_errors: List[Dict[str, Any]] = []
        self.timestamp_anomalies: List[Dict[str, Any]] = []
        self.duplicates_detected: List[Dict[str, Any]] = []

        # Duplicate tracking: canonical_hash -> count
        self._hash_counts: Dict[str, int] = {}
        self.unique_parent_asins: Set[str] = set()
        self.unique_asins: Set[str] = set()
        self.unique_users: Set[str] = set()

    def feed(self, chunk: bytes) -> bool:
        """
        Feeds a chunk of bytes into the parser.
        Returns True if more data is needed, or False if target_records reached.
        """
        self.buffer.extend(chunk)

        while True:
            nl_pos = self.buffer.find(b"\n")
            if nl_pos == -1:
                break

            line_bytes = bytes(self.buffer[:nl_pos])
            del self.buffer[: nl_pos + 1]

            line_start_offset = self.global_byte_offset
            line_len = len(line_bytes)
            self.global_byte_offset += line_len + 1  # count the newline byte
            current_line_num = self.line_number
            self.line_number += 1

            line_str = line_bytes.decode("utf-8", errors="replace").strip()
            if not line_str:
                continue

            # JSON Parsing
            try:
                record = json.loads(line_str)
            except Exception as e:
                self.parse_errors.append({
                    "line_number": current_line_num,
                    "byte_offset": line_start_offset,
                    "error": str(e),
                    "snippet": line_str[:100],
                })
                continue

            # Schema Validation
            is_valid, err_list = validate_review_record(record)
            if not is_valid:
                self.validation_errors.append({
                    "line_number": current_line_num,
                    "byte_offset": line_start_offset,
                    "errors": err_list,
                })
                continue

            # Timestamp unit audit
            _, unit_label, norm_secs, _ = classify_timestamp(record.get("timestamp"))

            # Primary Key & Duplicate Provenance
            canonical_hash = compute_canonical_review_id(record)
            occurrence_idx = self._hash_counts.get(canonical_hash, 0)
            self._hash_counts[canonical_hash] = occurrence_idx + 1

            if occurrence_idx == 0:
                review_id = canonical_hash
            else:
                review_id = f"{canonical_hash}_#{occurrence_idx}"
                self.duplicates_detected.append({
                    "review_id": review_id,
                    "canonical_hash": canonical_hash,
                    "occurrence_index": occurrence_idx,
                    "line_number": current_line_num,
                    "byte_offset": line_start_offset,
                })

            # Provenance metadata envelope
            record_entry = {
                "_provenance": {
                    "review_id": review_id,
                    "canonical_hash": canonical_hash,
                    "occurrence_index": occurrence_idx,
                    "source_line_number": current_line_num,
                    "byte_offset": line_start_offset,
                    "byte_length": line_len,
                    "timestamp_unit": unit_label,
                    "normalized_epoch_seconds": norm_secs,
                },
                "raw_record": record,
            }

            self.admitted_records.append(record_entry)
            self.unique_parent_asins.add(record["parent_asin"])
            self.unique_asins.add(record["asin"])
            self.unique_users.add(record["user_id"])

            if len(self.admitted_records) >= self.target_records:
                return False

        return True

    def finalize(self) -> Dict[str, Any]:
        """
        Reports unparsed trailing bytes and returns summary statistics.
        """
        trailing_incomplete_bytes = len(self.buffer)
        return {
            "admitted_records_count": len(self.admitted_records),
            "target_records": self.target_records,
            "target_reached": len(self.admitted_records) >= self.target_records,
            "total_lines_processed": self.line_number,
            "trailing_incomplete_bytes": trailing_incomplete_bytes,
            "parse_errors_count": len(self.parse_errors),
            "validation_errors_count": len(self.validation_errors),
            "duplicates_count": len(self.duplicates_detected),
            "unique_parent_asins_count": len(self.unique_parent_asins),
            "unique_asins_count": len(self.unique_asins),
            "unique_users_count": len(self.unique_users),
        }


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Prevents automatic redirect following so deadlines and range headers can be enforced per hop."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class BoundedRangeStreamer:
    """
    Executes a bounded HTTP Range request enforcing:
    1. Status strictly 206 Partial Content.
    2. Content-Range validation against requested bytes and documented total size.
    3. Cumulative wall-clock deadline across redirects and chunk streaming.
    4. Streaming byte cap enforcement (closes socket immediately upon cap).
    """

    def __init__(
        self,
        url: str = OFFICIAL_SOURCE_URL,
        max_body_bytes: int = DEFAULT_MAX_BODY_BYTES,
        cumulative_timeout: float = DEFAULT_CUMULATIVE_TIMEOUT,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        expected_total_size: int = DOCUMENTED_TOTAL_SIZE,
        opener: Optional[urllib.request.OpenerDirector] = None,
    ):
        self.url = url
        self.max_body_bytes = max_body_bytes
        self.cumulative_timeout = cumulative_timeout
        self.chunk_size = chunk_size
        self.expected_total_size = expected_total_size
        self.opener = opener or urllib.request.build_opener(NoRedirectHandler)

    def stream_bytes(self) -> Iterator[Tuple[bytes, Dict[str, Any]]]:
        """
        Yields chunks of bytes along with transport metadata.
        Raises RuntimeError, ValueError, or TimeoutError on contract violations.
        """
        start_time = time.monotonic()
        hard_deadline = start_time + self.cumulative_timeout

        current_url = self.url
        redirect_hops: List[Dict[str, Any]] = []
        final_response = None

        # Redirect resolution loop
        while True:
            now = time.monotonic()
            if now >= hard_deadline:
                raise TimeoutError(f"Cumulative timeout ({self.cumulative_timeout}s) exceeded before connection.")
            remaining_timeout = hard_deadline - now

            req = urllib.request.Request(current_url)
            req.add_header("Range", f"bytes=0-{self.max_body_bytes - 1}")
            req.add_header("User-Agent", "ProductPulse-BoundedIngest/1.0 (Academic Verification)")

            try:
                resp = self.opener.open(req, timeout=remaining_timeout)
                final_response = resp
                redirect_hops.append({
                    "hop": len(redirect_hops) + 1,
                    "domain": urllib.parse.urlparse(current_url).netloc,
                    "status": resp.status,
                })
                break
            except urllib.error.HTTPError as err:
                if err.code in (301, 302, 303, 307, 308):
                    redirect_hops.append({
                        "hop": len(redirect_hops) + 1,
                        "domain": urllib.parse.urlparse(current_url).netloc,
                        "status": err.code,
                    })
                    location = err.headers.get("Location")
                    if not location:
                        raise RuntimeError(f"HTTP {err.code} redirect missing Location header")
                    current_url = urllib.parse.urljoin(current_url, location)
                    continue
                else:
                    final_response = err
                    redirect_hops.append({
                        "hop": len(redirect_hops) + 1,
                        "domain": urllib.parse.urlparse(current_url).netloc,
                        "status": err.code,
                    })
                    break

        final_status = getattr(final_response, "status", None)
        headers = getattr(final_response, "headers", None)

        # Safeguard 1: Status must be strictly 206 Partial Content
        if final_status != 206:
            if hasattr(final_response, "close"):
                final_response.close()
            raise RuntimeError(
                f"Server returned status {final_status} instead of expected 206 Partial Content. "
                "Aborting immediately to prevent unbounded payload transfer."
            )

        # Safeguard 2: Strict Content-Range validation
        content_range = headers.get("Content-Range") if headers else None
        if not content_range:
            final_response.close()
            raise ValueError("Missing Content-Range header in HTTP 206 response.")

        # Exact regex matching: bytes <start>-<end>/<total>
        match = re.match(r"^bytes\s+(\d+)-(\d+)/(\d+)$", content_range.strip())
        if not match:
            final_response.close()
            raise ValueError(
                f"Malformed Content-Range header syntax: {content_range!r}. Expected exact 'bytes <start>-<end>/<total>'."
            )

        start_byte = int(match.group(1))
        end_byte = int(match.group(2))
        total_reported = int(match.group(3))

        # 1. start offset must be strictly 0
        if start_byte != 0:
            final_response.close()
            raise ValueError(f"Content-Range start offset must be 0, got {start_byte} in '{content_range}'")

        # 2. bounds order: end must be >= start
        if end_byte < start_byte:
            final_response.close()
            raise ValueError(f"Content-Range reversed bounds: end {end_byte} < start {start_byte} in '{content_range}'")

        # 3. total must match documented total size
        if total_reported != self.expected_total_size:
            final_response.close()
            raise ValueError(
                f"Reported total file size {total_reported} in Content-Range does not match documented {self.expected_total_size}"
            )

        # 4. end offset must match expected range end: min(max_body_bytes - 1, total_reported - 1)
        expected_range_end = min(self.max_body_bytes - 1, total_reported - 1)
        if end_byte != expected_range_end:
            final_response.close()
            raise ValueError(
                f"Content-Range end offset {end_byte} does not match expected {expected_range_end} in '{content_range}'"
            )

        # 5. returned range length agrees with Content-Length (if present)
        declared_range_len = end_byte - start_byte + 1
        content_length_header = headers.get("Content-Length") if headers else None
        if content_length_header is not None:
            try:
                cl_val = int(content_length_header)
            except (TypeError, ValueError) as ex:
                final_response.close()
                raise ValueError(f"Invalid Content-Length header {content_length_header!r}: {ex}")
            if cl_val != declared_range_len:
                final_response.close()
                raise ValueError(
                    f"Content-Length ({cl_val}) does not match declared range length ({declared_range_len}) in '{content_range}'"
                )

        # Streaming loop with byte cap and deadline
        total_body_bytes = 0
        transport_meta = {
            "final_status": final_status,
            "content_range": content_range,
            "content_length": headers.get("Content-Length") if headers else None,
            "redirect_hops": redirect_hops,
            "start_time": start_time,
        }

        try:
            while total_body_bytes < self.max_body_bytes:
                now = time.monotonic()
                if now >= hard_deadline:
                    raise TimeoutError(f"Cumulative timeout ({self.cumulative_timeout}s) exceeded during body stream.")

                chunk_to_read = min(self.chunk_size, self.max_body_bytes - total_body_bytes)
                chunk = final_response.read(chunk_to_read)
                if not chunk:
                    break

                total_body_bytes += len(chunk)
                transport_meta["total_body_bytes_read"] = total_body_bytes
                transport_meta["elapsed_seconds"] = round(time.monotonic() - start_time, 4)
                yield chunk, transport_meta
        finally:
            if hasattr(final_response, "close"):
                final_response.close()


def run_bounded_ingestion(
    target_records: int = DEFAULT_TARGET_RECORDS,
    max_body_bytes: int = DEFAULT_MAX_BODY_BYTES,
    cumulative_timeout: float = DEFAULT_CUMULATIVE_TIMEOUT,
    output_raw_path: str = DEFAULT_OUTPUT_RAW,
    output_manifest_path: str = DEFAULT_OUTPUT_MANIFEST,
    streamer: Optional[BoundedRangeStreamer] = None,
    allow_overwrite: bool = False,
) -> Dict[str, Any]:
    """
    Executes bounded ingestion end-to-end, writing raw lines to output_raw_path
    and the execution manifest to output_manifest_path.
    Protects against silent file overwrites unless allow_overwrite is True.

    Crash-Atomicity Disclosure:
    While individual file replacements (os.replace) are atomic per-file on POSIX
    and Windows NTFS, replacing two separate files (raw dataset and manifest)
    sequentially cannot form an OS-level atomic transaction across sudden process
    termination (e.g. SIGKILL, power outage, or hardware crash) occurring in the
    microsecond window between Step 4a (raw replacement) and Step 4b (manifest replacement).
    Under standard Python runtime execution, safety and rollback are guaranteed:
    if allow_overwrite is True, existing files are preserved in recoverable backups
    prior to replacement; if publication of either file fails, the previous valid pair
    is automatically restored. If restoration itself fails, recoverable backups are
    preserved on disk and their exact paths reported.
    """
    if not allow_overwrite:
        if os.path.exists(output_raw_path):
            raise FileExistsError(f"Destination raw output file already exists: {output_raw_path}")
        if os.path.exists(output_manifest_path):
            raise FileExistsError(f"Destination manifest file already exists: {output_manifest_path}")

    # Ensure output directories exist
    os.makedirs(os.path.dirname(output_raw_path), exist_ok=True)
    os.makedirs(os.path.dirname(output_manifest_path), exist_ok=True)

    streamer_inst = streamer or BoundedRangeStreamer(
        max_body_bytes=max_body_bytes,
        cumulative_timeout=cumulative_timeout,
    )
    parser = IngestionByteStreamParser(target_records=target_records)

    start_wall_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    start_mono = time.monotonic()
    total_bytes_streamed = 0
    transport_details: Dict[str, Any] = {}

    for chunk, meta in streamer_inst.stream_bytes():
        total_bytes_streamed += len(chunk)
        transport_details = meta
        more_needed = parser.feed(chunk)
        if not more_needed:
            break

    elapsed_mono = time.monotonic() - start_mono
    end_wall_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    summary = parser.finalize()

    pid = os.getpid()
    nano_ts = time.time_ns()
    tmp_raw_path = f"{output_raw_path}.tmp.{pid}.{nano_ts}"
    tmp_manifest_path = f"{output_manifest_path}.tmp.{pid}.{nano_ts}"
    bak_raw_path: Optional[str] = None
    bak_manifest_path: Optional[str] = None

    try:
        # 1. Stage raw records to temporary file
        with open(tmp_raw_path, "w", encoding="utf-8") as raw_f:
            for entry in parser.admitted_records:
                raw_f.write(json.dumps(entry["raw_record"], ensure_ascii=False) + "\n")
            raw_f.flush()
            os.fsync(raw_f.fileno())

        # 2. Compute SHA-256 of the staged raw file
        hasher = hashlib.sha256()
        with open(tmp_raw_path, "rb") as f:
            while True:
                b = f.read(65536)
                if not b:
                    break
                hasher.update(b)
        output_raw_sha256 = hasher.hexdigest()
        output_raw_bytes = os.path.getsize(tmp_raw_path)

        manifest = {
            "manifest_version": "1.0",
            "dataset_name": "McAuley-Lab/Amazon-Reviews-2023",
            "category": CATEGORY_LOCK,
            "source_url": streamer_inst.url,
            "ingestion_timestamps": {
                "start_utc": start_wall_time,
                "end_utc": end_wall_time,
                "elapsed_seconds": round(elapsed_mono, 4),
            },
            "limits_enforced": {
                "target_records": target_records,
                "max_body_bytes_cap": max_body_bytes,
                "cumulative_timeout_seconds": cumulative_timeout,
            },
            "transport_evidence": {
                "final_status": transport_details.get("final_status"),
                "content_range": transport_details.get("content_range"),
                "total_bytes_streamed": total_bytes_streamed,
                "redirect_hops": transport_details.get("redirect_hops", []),
            },
            "ingestion_outcomes": {
                "admitted_records_count": summary["admitted_records_count"],
                "target_reached": summary["target_reached"],
                "total_lines_processed": summary["total_lines_processed"],
                "trailing_incomplete_bytes": summary["trailing_incomplete_bytes"],
                "parse_errors_count": summary["parse_errors_count"],
                "validation_errors_count": summary["validation_errors_count"],
                "duplicates_count": summary["duplicates_count"],
                "unique_parent_asins_count": summary["unique_parent_asins_count"],
                "unique_asins_count": summary["unique_asins_count"],
                "unique_users_count": summary["unique_users_count"],
            },
            "output_files": {
                "raw_jsonl_path": output_raw_path,
                "raw_jsonl_bytes": output_raw_bytes,
                "raw_jsonl_sha256": output_raw_sha256,
                "manifest_path": output_manifest_path,
            },
            "academic_disclosures": {
                "sampling_nature": "Convenience prefix sample derived from byte range of remote JSONL",
                "population_claims_allowed": False,
                "intended_use": "Pipeline verification, aspect mining, NLP sentiment demonstration, and local MapReduce benchmarking",
            },
        }

        # 3. Stage manifest to temporary file
        with open(tmp_manifest_path, "w", encoding="utf-8") as mf:
            json.dump(manifest, mf, indent=2)
            mf.flush()
            os.fsync(mf.fileno())

        # 4. Safe Publication Strategy with Automatic Rollback and Prior Dataset Preservation
        # When allow_overwrite is True and destination files exist, preserve them as safe
        # recoverable backups before touching either destination file.
        if allow_overwrite:
            if os.path.exists(output_raw_path):
                candidate_bak_raw = f"{output_raw_path}.bak.{pid}.{nano_ts}"
                shutil.copy2(output_raw_path, candidate_bak_raw)
                bak_raw_path = candidate_bak_raw

            if os.path.exists(output_manifest_path):
                candidate_bak_manifest = f"{output_manifest_path}.bak.{pid}.{nano_ts}"
                shutil.copy2(output_manifest_path, candidate_bak_manifest)
                bak_manifest_path = candidate_bak_manifest

        published_raw = False
        published_manifest = False
        restoration_failures: List[str] = []

        try:
            # Step 4a: Publish raw file
            try:
                os.replace(tmp_raw_path, output_raw_path)
                published_raw = True
            except Exception as raw_pub_err:
                raise RuntimeError(
                    f"Publication failed while replacing raw file ({raw_pub_err})"
                ) from raw_pub_err

            # Step 4b: Publish manifest file
            try:
                os.replace(tmp_manifest_path, output_manifest_path)
                published_manifest = True
            except Exception as manifest_pub_err:
                raise RuntimeError(
                    f"Publication failed while replacing manifest ({manifest_pub_err})"
                ) from manifest_pub_err

            # Step 4c: Both files successfully replaced! Clean up temporary backups safely.
            if bak_raw_path and os.path.exists(bak_raw_path):
                try:
                    os.remove(bak_raw_path)
                    bak_raw_path = None
                except Exception:
                    pass

            if bak_manifest_path and os.path.exists(bak_manifest_path):
                try:
                    os.remove(bak_manifest_path)
                    bak_manifest_path = None
                except Exception:
                    pass

            return manifest

        except Exception as pub_err:
            # Step 4d: Publication failed. Execute safe restoration/rollback.
            # Rollback raw file
            if bak_raw_path:
                if published_raw:
                    try:
                        os.replace(bak_raw_path, output_raw_path)
                        bak_raw_path = None
                    except Exception as restore_err:
                        restoration_failures.append(
                            f"Failed to restore original raw file from {bak_raw_path}: {restore_err}"
                        )
                else:
                    if not os.path.exists(output_raw_path):
                        try:
                            os.replace(bak_raw_path, output_raw_path)
                            bak_raw_path = None
                        except Exception as restore_err:
                            restoration_failures.append(
                                f"Failed to restore missing raw file from {bak_raw_path}: {restore_err}"
                            )
                    else:
                        try:
                            os.remove(bak_raw_path)
                            bak_raw_path = None
                        except Exception:
                            pass
            elif published_raw and os.path.exists(output_raw_path):
                try:
                    os.remove(output_raw_path)
                except Exception as rm_err:
                    restoration_failures.append(
                        f"Failed to remove newly created raw file {output_raw_path}: {rm_err}"
                    )

            # Rollback manifest file
            if bak_manifest_path:
                if published_manifest:
                    try:
                        os.replace(bak_manifest_path, output_manifest_path)
                        bak_manifest_path = None
                    except Exception as restore_err:
                        restoration_failures.append(
                            f"Failed to restore original manifest from {bak_manifest_path}: {restore_err}"
                        )
                else:
                    if not os.path.exists(output_manifest_path):
                        try:
                            os.replace(bak_manifest_path, output_manifest_path)
                            bak_manifest_path = None
                        except Exception as restore_err:
                            restoration_failures.append(
                                f"Failed to restore missing manifest from {bak_manifest_path}: {restore_err}"
                            )
                    else:
                        try:
                            os.remove(bak_manifest_path)
                            bak_manifest_path = None
                        except Exception:
                            pass
            elif published_manifest and os.path.exists(output_manifest_path):
                try:
                    os.remove(output_manifest_path)
                except Exception as rm_err:
                    restoration_failures.append(
                        f"Failed to remove newly created manifest {output_manifest_path}: {rm_err}"
                    )

            if restoration_failures:
                failures_msg = "; ".join(restoration_failures)
                preserved_baks = []
                if bak_raw_path and os.path.exists(bak_raw_path):
                    preserved_baks.append(f"raw_backup={bak_raw_path}")
                if bak_manifest_path and os.path.exists(bak_manifest_path):
                    preserved_baks.append(f"manifest_backup={bak_manifest_path}")
                baks_str = ", ".join(preserved_baks) if preserved_baks else "none"
                raise RuntimeError(
                    f"Publication failed ({pub_err}) AND automatic restoration failed: {failures_msg}. "
                    f"Recoverable backups safely preserved: {baks_str}."
                ) from pub_err
            else:
                raise RuntimeError(
                    f"Publication failed ({pub_err}). "
                    "Rolled back published raw dataset to prevent incomplete/unmanifested outputs."
                ) from pub_err

    finally:
        # 5. Clean up any leftover temporary staging files
        for p in (tmp_raw_path, tmp_manifest_path):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ProductPulse Bounded Review Ingestion Script for Cell_Phones_and_Accessories"
    )
    parser.add_argument(
        "--target-records",
        type=int,
        default=DEFAULT_TARGET_RECORDS,
        help=f"Target review count (default: {DEFAULT_TARGET_RECORDS})",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=DEFAULT_MAX_BODY_BYTES,
        help=f"Response body byte ceiling (default: {DEFAULT_MAX_BODY_BYTES})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_CUMULATIVE_TIMEOUT,
        help=f"Cumulative timeout in seconds (default: {DEFAULT_CUMULATIVE_TIMEOUT})",
    )
    parser.add_argument(
        "--allow-overwrite",
        action="store_true",
        help="Allow overwriting existing output raw files and manifests (default: False)",
    )
    parser.add_argument(
        "--execute-live",
        action="store_true",
        help="Explicit confirmation to execute live network ingestion (must be authorized by user)",
    )

    args = parser.parse_args()

    if not args.execute_live:
        print("[SAFETY LOCK] Execution halted. Live network requests require the explicit '--execute-live' flag.")
        print("To run local offline tests, use: python -m unittest discover tests/")
        sys.exit(0)

    try:
        manifest = run_bounded_ingestion(
            target_records=args.target_records,
            max_body_bytes=args.max_bytes,
            cumulative_timeout=args.timeout,
            allow_overwrite=args.allow_overwrite,
        )
        print("Ingestion completed successfully.")
        print(json.dumps(manifest, indent=2))
    except Exception as e:
        print(f"[INGESTION ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
