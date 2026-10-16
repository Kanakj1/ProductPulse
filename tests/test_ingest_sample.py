"""
ProductPulse — Unit Tests for Bounded Ingestion Script (tests/test_ingest_sample.py)

Comprehensive offline tests for:
- Strict HTTP Range and Content-Range parsing and bounds validation.
- Rejection of HTTP 200 and unexpected statuses.
- Streaming byte-cap enforcement and cumulative timeout bounds.
- Schema validation, missing field detection, and timestamp anomaly classification.
- Duplicate record provenance and deterministic canonical hash IDs.
- Incomplete trailing line detection.
- Failure-safe staging, rollback on publication errors, and overwrite protection.
- CLI safety lock subprocess execution.

All tests execute in-memory or in isolated temporary directories. Zero live network calls.
"""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.ingest_sample import (
    BoundedRangeStreamer,
    DOCUMENTED_TOTAL_SIZE,
    IngestionByteStreamParser,
    TimestampAnomalyError,
    classify_timestamp,
    compute_canonical_review_id,
    run_bounded_ingestion,
    validate_review_record,
)


class TestTimestampClassifier(unittest.TestCase):
    def test_valid_milliseconds(self):
        # 1612044451196 -> 2021-01-30 in ms (13 digits)
        is_valid, unit, norm_secs, err = classify_timestamp(1612044451196)
        self.assertTrue(is_valid)
        self.assertEqual(unit, "MILLISECONDS")
        self.assertAlmostEqual(norm_secs, 1612044451.196)
        self.assertIsNone(err)

    def test_valid_seconds(self):
        # 1612044451 -> 2021-01-30 in seconds (10 digits)
        is_valid, unit, norm_secs, err = classify_timestamp(1612044451)
        self.assertTrue(is_valid)
        self.assertEqual(unit, "SECONDS")
        self.assertEqual(norm_secs, 1612044451.0)
        self.assertIsNone(err)

    def test_anomaly_future_or_past(self):
        # Year 1970 (too early) or absurdly large value
        is_valid, unit, norm_secs, err = classify_timestamp(100)
        self.assertFalse(is_valid)
        self.assertEqual(unit, "ANOMALY")
        self.assertIsNotNone(err)

    def test_anomaly_null_or_invalid_type(self):
        is_valid, unit, _, err = classify_timestamp(None)
        self.assertFalse(is_valid)
        self.assertEqual(unit, "ANOMALY")

        is_valid2, unit2, _, err2 = classify_timestamp("not-a-number")
        self.assertFalse(is_valid2)
        self.assertEqual(unit2, "ANOMALY")


class TestRecordValidator(unittest.TestCase):
    def test_valid_record(self):
        rec = {
            "parent_asin": "B08L6L3X1S",
            "asin": "B08L6L3X1S",
            "user_id": "U12345",
            "rating": 5.0,
            "timestamp": 1612044451196,
            "title": "Good Phone",
            "text": "Great battery life.",
        }
        is_valid, errors = validate_review_record(rec)
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])

    def test_missing_or_blank_required_fields(self):
        # Missing parent_asin
        rec1 = {"asin": "A1", "user_id": "U1", "rating": 4.0, "timestamp": 1612044451196}
        is_valid1, errors1 = validate_review_record(rec1)
        self.assertFalse(is_valid1)
        self.assertTrue(any("parent_asin" in e for e in errors1))

        # Blank parent_asin
        rec2 = {"parent_asin": "   ", "asin": "A1", "user_id": "U1", "rating": 4.0, "timestamp": 1612044451196}
        is_valid2, errors2 = validate_review_record(rec2)
        self.assertFalse(is_valid2)

    def test_rating_out_of_bounds_or_non_numeric(self):
        rec1 = {"parent_asin": "P1", "asin": "A1", "user_id": "U1", "rating": 6.5, "timestamp": 1612044451196}
        is_valid1, errors1 = validate_review_record(rec1)
        self.assertFalse(is_valid1)
        self.assertTrue(any("Rating 6.5" in e for e in errors1))

        rec2 = {"parent_asin": "P1", "asin": "A1", "user_id": "U1", "rating": "five-stars", "timestamp": 1612044451196}
        is_valid2, errors2 = validate_review_record(rec2)
        self.assertFalse(is_valid2)


class TestStreamParser(unittest.TestCase):
    def test_valid_jsonl_parsing_and_provenance(self):
        records = [
            {"parent_asin": "P1", "asin": "A1", "user_id": "U1", "rating": 5.0, "timestamp": 1612044451000, "text": "Review 1"},
            {"parent_asin": "P2", "asin": "A2", "user_id": "U2", "rating": 4.0, "timestamp": 1612044452000, "text": "Review 2"},
        ]
        stream_bytes = "\n".join(json.dumps(r) for r in records).encode("utf-8") + b"\n"

        parser = IngestionByteStreamParser(target_records=10)
        parser.feed(stream_bytes)
        summary = parser.finalize()

        self.assertEqual(summary["admitted_records_count"], 2)
        self.assertEqual(summary["parse_errors_count"], 0)
        self.assertEqual(summary["trailing_incomplete_bytes"], 0)

        # Check provenance
        r0 = parser.admitted_records[0]
        self.assertEqual(r0["_provenance"]["source_line_number"], 0)
        self.assertEqual(r0["_provenance"]["byte_offset"], 0)
        self.assertEqual(r0["_provenance"]["occurrence_index"], 0)

        r1 = parser.admitted_records[1]
        self.assertEqual(r1["_provenance"]["source_line_number"], 1)
        self.assertGreater(r1["_provenance"]["byte_offset"], 0)

    def test_malformed_json_handling(self):
        stream_bytes = b'{"parent_asin": "P1", "asin": "A1", "user_id": "U1", "rating": 5.0, "timestamp": 1612044451000}\n' \
                       b'MALFORMED_JSON_LINE_HERE\n' \
                       b'{"parent_asin": "P2", "asin": "A2", "user_id": "U2", "rating": 4.0, "timestamp": 1612044452000}\n'

        parser = IngestionByteStreamParser(target_records=10)
        parser.feed(stream_bytes)
        summary = parser.finalize()

        self.assertEqual(summary["admitted_records_count"], 2)
        self.assertEqual(summary["parse_errors_count"], 1)
        self.assertEqual(parser.parse_errors[0]["line_number"], 1)

    def test_trailing_incomplete_line(self):
        stream_bytes = b'{"parent_asin": "P1", "asin": "A1", "user_id": "U1", "rating": 5.0, "timestamp": 1612044451000}\n' \
                       b'{"parent_asin": "P2", "asin": "A2", "user_id": "U2", "rat'

        parser = IngestionByteStreamParser(target_records=10)
        parser.feed(stream_bytes)
        summary = parser.finalize()

        self.assertEqual(summary["admitted_records_count"], 1)
        self.assertGreater(summary["trailing_incomplete_bytes"], 0)
        self.assertEqual(summary["parse_errors_count"], 0)

    def test_duplicate_records_provenance_preservation(self):
        rec = {"parent_asin": "P1", "asin": "A1", "user_id": "U1", "rating": 5.0, "timestamp": 1612044451000, "text": "Same"}
        stream_bytes = (json.dumps(rec) + "\n" + json.dumps(rec) + "\n").encode("utf-8")

        parser = IngestionByteStreamParser(target_records=10)
        parser.feed(stream_bytes)
        summary = parser.finalize()

        self.assertEqual(summary["admitted_records_count"], 2)
        self.assertEqual(summary["duplicates_count"], 1)

        id0 = parser.admitted_records[0]["_provenance"]["review_id"]
        id1 = parser.admitted_records[1]["_provenance"]["review_id"]

        self.assertNotEqual(id0, id1)
        self.assertTrue(id1.endswith("_#1"))
        self.assertEqual(parser.admitted_records[1]["_provenance"]["occurrence_index"], 1)
        self.assertEqual(parser.admitted_records[0]["_provenance"]["occurrence_index"], 0)


class TestStrictContentRangeValidation(unittest.TestCase):
    def _create_streamer_with_headers(self, headers, max_body_bytes=1024, expected_total=DOCUMENTED_TOTAL_SIZE):
        mock_response = MagicMock()
        mock_response.status = 206
        mock_response.headers = headers
        mock_response.read.return_value = b""

        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response

        return BoundedRangeStreamer(
            opener=mock_opener,
            max_body_bytes=max_body_bytes,
            expected_total_size=expected_total,
        ), mock_response

    def test_valid_content_range_and_length(self):
        headers = {
            "Content-Range": f"bytes 0-1023/{DOCUMENTED_TOTAL_SIZE}",
            "Content-Length": "1024",
        }
        streamer, _ = self._create_streamer_with_headers(headers, max_body_bytes=1024)
        chunks = list(streamer.stream_bytes())
        self.assertEqual(chunks, [])

    def test_rejection_of_nonzero_content_range_start(self):
        # Starts at 100 instead of 0
        headers = {
            "Content-Range": f"bytes 100-1023/{DOCUMENTED_TOTAL_SIZE}",
            "Content-Length": "924",
        }
        streamer, mock_resp = self._create_streamer_with_headers(headers, max_body_bytes=1024)
        with self.assertRaises(ValueError) as ctx:
            list(streamer.stream_bytes())
        self.assertIn("start offset must be 0", str(ctx.exception))
        mock_resp.close.assert_called_once()

    def test_rejection_of_wrong_content_range_end(self):
        # End is 500 when 1023 was requested
        headers = {
            "Content-Range": f"bytes 0-500/{DOCUMENTED_TOTAL_SIZE}",
            "Content-Length": "501",
        }
        streamer, mock_resp = self._create_streamer_with_headers(headers, max_body_bytes=1024)
        with self.assertRaises(ValueError) as ctx:
            list(streamer.stream_bytes())
        self.assertIn("end offset 500 does not match expected 1023", str(ctx.exception))
        mock_resp.close.assert_called_once()

    def test_rejection_of_reversed_content_range_bounds(self):
        # Bounds reversed: 500-100
        headers = {
            "Content-Range": f"bytes 500-100/{DOCUMENTED_TOTAL_SIZE}",
        }
        streamer, mock_resp = self._create_streamer_with_headers(headers, max_body_bytes=1024)
        with self.assertRaises(ValueError) as ctx:
            list(streamer.stream_bytes())
        # Either start != 0 or reversed bounds triggers failure
        self.assertTrue(
            "start offset must be 0" in str(ctx.exception) or "reversed bounds" in str(ctx.exception)
        )
        mock_resp.close.assert_called_once()

    def test_rejection_of_malformed_content_range_syntax(self):
        malformed_examples = [
            f"0-1023/{DOCUMENTED_TOTAL_SIZE}",
            f"bytes 0:1023/{DOCUMENTED_TOTAL_SIZE}",
            f"bytes 0-1023/*",
            "bytes zero-1023/9342568048",
            "invalid-header-value",
        ]
        for bad_header in malformed_examples:
            streamer, mock_resp = self._create_streamer_with_headers({"Content-Range": bad_header})
            with self.assertRaises(ValueError) as ctx:
                list(streamer.stream_bytes())
            self.assertIn("Malformed Content-Range", str(ctx.exception))
            mock_resp.close.assert_called_once()

    def test_rejection_of_incorrect_total_size(self):
        headers = {
            "Content-Range": "bytes 0-1023/12345678",
            "Content-Length": "1024",
        }
        streamer, mock_resp = self._create_streamer_with_headers(headers, max_body_bytes=1024)
        with self.assertRaises(ValueError) as ctx:
            list(streamer.stream_bytes())
        self.assertIn("does not match documented", str(ctx.exception))
        mock_resp.close.assert_called_once()

    def test_rejection_of_mismatched_content_length(self):
        # Content-Range says 1024 bytes, but Content-Length says 500
        headers = {
            "Content-Range": f"bytes 0-1023/{DOCUMENTED_TOTAL_SIZE}",
            "Content-Length": "500",
        }
        streamer, mock_resp = self._create_streamer_with_headers(headers, max_body_bytes=1024)
        with self.assertRaises(ValueError) as ctx:
            list(streamer.stream_bytes())
        self.assertIn("does not match declared range length", str(ctx.exception))
        mock_resp.close.assert_called_once()


class TestBoundedRangeStreamerProtocol(unittest.TestCase):
    def test_rejection_of_status_200(self):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Length": "9342568048"}

        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response

        streamer = BoundedRangeStreamer(opener=mock_opener, max_body_bytes=1024)
        with self.assertRaises(RuntimeError) as ctx:
            list(streamer.stream_bytes())
        self.assertIn("Server returned status 200", str(ctx.exception))
        mock_response.close.assert_called_once()

    def test_byte_cap_enforcement(self):
        data = b"X" * 2000
        mock_response = MagicMock()
        mock_response.status = 206
        mock_response.headers = {
            "Content-Range": f"bytes 0-499/{DOCUMENTED_TOTAL_SIZE}",
            "Content-Length": "500",
        }
        stream_io = io.BytesIO(data)
        mock_response.read = stream_io.read

        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response

        streamer = BoundedRangeStreamer(
            opener=mock_opener,
            max_body_bytes=500,
            expected_total_size=DOCUMENTED_TOTAL_SIZE,
            chunk_size=100,
        )
        chunks = [c for c, meta in streamer.stream_bytes()]
        total_streamed = sum(len(c) for c in chunks)
        self.assertEqual(total_streamed, 500)

    def test_cumulative_timeout_enforcement(self):
        mock_response = MagicMock()
        mock_response.status = 206
        mock_response.headers = {
            "Content-Range": f"bytes 0-1023/{DOCUMENTED_TOTAL_SIZE}",
            "Content-Length": "1024",
        }
        def slow_read(n):
            time.sleep(0.05)
            return b"Y" * n

        mock_response.read = slow_read
        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response

        streamer = BoundedRangeStreamer(
            opener=mock_opener,
            max_body_bytes=1024,
            cumulative_timeout=0.03,
            expected_total_size=DOCUMENTED_TOTAL_SIZE,
            chunk_size=100,
        )
        with self.assertRaises(TimeoutError):
            list(streamer.stream_bytes())


class TestFailureSafeOutputCreation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.raw_path = os.path.join(self.temp_dir, "raw.jsonl")
        self.manifest_path = os.path.join(self.temp_dir, "manifest.json")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_dummy_streamer(self, records):
        stream_bytes = "\n".join(json.dumps(r) for r in records).encode("utf-8") + b"\n"
        mock_streamer = MagicMock()
        mock_streamer.url = "https://example.com/test.jsonl"
        mock_streamer.stream_bytes.return_value = [
            (stream_bytes, {
                "final_status": 206,
                "content_range": f"bytes 0-{len(stream_bytes)-1}/{DOCUMENTED_TOTAL_SIZE}",
            })
        ]
        return mock_streamer

    def test_protection_against_silent_overwrite(self):
        with open(self.raw_path, "w") as f:
            f.write("EXISTING RAW DATA\n")

        with self.assertRaises(FileExistsError):
            run_bounded_ingestion(
                output_raw_path=self.raw_path,
                output_manifest_path=self.manifest_path,
                allow_overwrite=False,
            )

    def test_successful_staging_publication_and_cleanup(self):
        records = [
            {"parent_asin": "P1", "asin": "A1", "user_id": "U1", "rating": 5.0, "timestamp": 1612044451000, "text": "Test"}
        ]
        mock_streamer = self._create_dummy_streamer(records)

        manifest = run_bounded_ingestion(
            output_raw_path=self.raw_path,
            output_manifest_path=self.manifest_path,
            streamer=mock_streamer,
            allow_overwrite=False,
        )

        # Both destination files must exist
        self.assertTrue(os.path.exists(self.raw_path))
        self.assertTrue(os.path.exists(self.manifest_path))

        # Check manifest contents
        self.assertEqual(manifest["ingestion_outcomes"]["admitted_records_count"], 1)

        # Confirm zero temporary files left behind
        temp_files = [f for f in os.listdir(self.temp_dir) if ".tmp." in f]
        self.assertEqual(temp_files, [])

    def test_failure_while_writing_raw_data_cleans_up(self):
        records = [
            {"parent_asin": "P1", "asin": "A1", "user_id": "U1", "rating": 5.0, "timestamp": 1612044451000}
        ]
        mock_streamer = self._create_dummy_streamer(records)

        # Simulate write failure by mocking open
        original_open = open
        def mock_open_fail(path, *args, **kwargs):
            if ".tmp." in str(path) and "raw" in str(path):
                raise IOError("Simulated disk error during raw file write")
            return original_open(path, *args, **kwargs)

        with patch("builtins.open", side_effect=mock_open_fail):
            with self.assertRaises(IOError):
                run_bounded_ingestion(
                    output_raw_path=self.raw_path,
                    output_manifest_path=self.manifest_path,
                    streamer=mock_streamer,
                )

        # Neither destination file should exist
        self.assertFalse(os.path.exists(self.raw_path))
        self.assertFalse(os.path.exists(self.manifest_path))

        # No leftover .tmp files
        temp_files = [f for f in os.listdir(self.temp_dir) if ".tmp." in f]
        self.assertEqual(temp_files, [])

    def test_failure_while_writing_manifest_cleans_up(self):
        records = [
            {"parent_asin": "P1", "asin": "A1", "user_id": "U1", "rating": 5.0, "timestamp": 1612044451000}
        ]
        mock_streamer = self._create_dummy_streamer(records)

        with patch("json.dump", side_effect=TypeError("Simulated serialization error in manifest")):
            with self.assertRaises(TypeError):
                run_bounded_ingestion(
                    output_raw_path=self.raw_path,
                    output_manifest_path=self.manifest_path,
                    streamer=mock_streamer,
                )

        self.assertFalse(os.path.exists(self.raw_path))
        self.assertFalse(os.path.exists(self.manifest_path))

        temp_files = [f for f in os.listdir(self.temp_dir) if ".tmp." in f]
        self.assertEqual(temp_files, [])

    def test_failure_during_publication_rolls_back_raw_dataset(self):
        records = [
            {"parent_asin": "P1", "asin": "A1", "user_id": "U1", "rating": 5.0, "timestamp": 1612044451000}
        ]
        mock_streamer = self._create_dummy_streamer(records)

        original_replace = os.replace
        replace_call_count = 0

        # Replace raw succeeds, replace manifest fails
        def mock_replace(src, dst):
            nonlocal replace_call_count
            replace_call_count += 1
            if "manifest" in str(dst):
                raise OSError("Simulated permission error publishing manifest")
            return original_replace(src, dst)

        with patch("os.replace", side_effect=mock_replace):
            with self.assertRaises(RuntimeError) as ctx:
                run_bounded_ingestion(
                    output_raw_path=self.raw_path,
                    output_manifest_path=self.manifest_path,
                    streamer=mock_streamer,
                )
            self.assertIn("Rolled back published raw dataset", str(ctx.exception))

        # Both files must NOT exist on disk (raw was rolled back!)
        self.assertFalse(os.path.exists(self.raw_path))
        self.assertFalse(os.path.exists(self.manifest_path))

        # Temporary files must be cleaned up
        temp_files = [f for f in os.listdir(self.temp_dir) if ".tmp." in f]
        self.assertEqual(temp_files, [])

    def test_no_misleading_manifest_on_stream_failure(self):
        mock_streamer = MagicMock()
        mock_streamer.url = "https://example.com/test.jsonl"
        def failing_stream():
            yield b'{"parent_asin": "P1", "asin": "A1", "user_id": "U1", "rating": 5.0, "timestamp": 1612044451000}\n', {}
            raise ConnectionResetError("Simulated network drop mid-stream")
        mock_streamer.stream_bytes = failing_stream

        with self.assertRaises(ConnectionResetError):
            run_bounded_ingestion(
                output_raw_path=self.raw_path,
                output_manifest_path=self.manifest_path,
                streamer=mock_streamer,
            )

        self.assertFalse(os.path.exists(self.raw_path))
        self.assertFalse(os.path.exists(self.manifest_path))

    def test_overwrite_manifest_failure_restores_existing_files(self):
        existing_raw = b'{"parent_asin": "EXISTING_P1", "asin": "EXISTING_A1"}\n'
        existing_manifest = b'{"manifest_version": "0.9", "note": "pre-existing"}\n'
        with open(self.raw_path, "wb") as f:
            f.write(existing_raw)
        with open(self.manifest_path, "wb") as f:
            f.write(existing_manifest)

        records = [
            {"parent_asin": "NEW_P1", "asin": "NEW_A1", "user_id": "U1", "rating": 5.0, "timestamp": 1612044451000}
        ]
        mock_streamer = self._create_dummy_streamer(records)

        original_replace = os.replace
        def mock_replace(src, dst):
            if "manifest" in str(dst) and ".tmp." in str(src):
                raise OSError("Simulated permission error publishing manifest")
            return original_replace(src, dst)

        with patch("os.replace", side_effect=mock_replace):
            with self.assertRaises(RuntimeError) as ctx:
                run_bounded_ingestion(
                    output_raw_path=self.raw_path,
                    output_manifest_path=self.manifest_path,
                    streamer=mock_streamer,
                    allow_overwrite=True,
                )
            self.assertIn("Publication failed", str(ctx.exception))

        # Both original files must remain byte-for-byte identical
        with open(self.raw_path, "rb") as f:
            self.assertEqual(f.read(), existing_raw)
        with open(self.manifest_path, "rb") as f:
            self.assertEqual(f.read(), existing_manifest)

        # Confirm zero temporary or backup files left behind
        extra_files = [f for f in os.listdir(self.temp_dir) if ".tmp." in f or ".bak." in f]
        self.assertEqual(extra_files, [])

    def test_overwrite_raw_failure_preserves_existing_files(self):
        existing_raw = b'{"parent_asin": "EXISTING_P1", "asin": "EXISTING_A1"}\n'
        existing_manifest = b'{"manifest_version": "0.9", "note": "pre-existing"}\n'
        with open(self.raw_path, "wb") as f:
            f.write(existing_raw)
        with open(self.manifest_path, "wb") as f:
            f.write(existing_manifest)

        records = [
            {"parent_asin": "NEW_P1", "asin": "NEW_A1", "user_id": "U1", "rating": 5.0, "timestamp": 1612044451000}
        ]
        mock_streamer = self._create_dummy_streamer(records)

        original_replace = os.replace
        def mock_replace(src, dst):
            if "raw" in str(dst) and ".tmp." in str(src):
                raise OSError("Simulated disk error replacing raw file")
            return original_replace(src, dst)

        with patch("os.replace", side_effect=mock_replace):
            with self.assertRaises(RuntimeError) as ctx:
                run_bounded_ingestion(
                    output_raw_path=self.raw_path,
                    output_manifest_path=self.manifest_path,
                    streamer=mock_streamer,
                    allow_overwrite=True,
                )
            self.assertIn("Publication failed", str(ctx.exception))

        # Both original files must remain byte-for-byte identical
        with open(self.raw_path, "rb") as f:
            self.assertEqual(f.read(), existing_raw)
        with open(self.manifest_path, "rb") as f:
            self.assertEqual(f.read(), existing_manifest)

        # Confirm zero temporary or backup files left behind
        extra_files = [f for f in os.listdir(self.temp_dir) if ".tmp." in f or ".bak." in f]
        self.assertEqual(extra_files, [])

    def test_successful_overwrite_replaces_both_files_cleanly(self):
        with open(self.raw_path, "w") as f:
            f.write("OLD RAW DATA\n")
        with open(self.manifest_path, "w") as f:
            f.write('{"old": "manifest"}\n')

        records = [
            {"parent_asin": "NEW_P1", "asin": "NEW_A1", "user_id": "U1", "rating": 5.0, "timestamp": 1612044451000}
        ]
        mock_streamer = self._create_dummy_streamer(records)

        manifest = run_bounded_ingestion(
            output_raw_path=self.raw_path,
            output_manifest_path=self.manifest_path,
            streamer=mock_streamer,
            allow_overwrite=True,
        )

        with open(self.raw_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("NEW_P1", content)
            self.assertNotIn("OLD RAW DATA", content)

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["manifest_version"], "1.0")

        # Confirm zero temporary or backup files left behind
        extra_files = [f for f in os.listdir(self.temp_dir) if ".tmp." in f or ".bak." in f]
        self.assertEqual(extra_files, [])

    def test_default_overwrite_false_refuses_existing_destinations(self):
        # 1. Existing raw file refuses
        with open(self.raw_path, "w") as f:
            f.write("PRIOR RAW\n")
        with self.assertRaises(FileExistsError):
            run_bounded_ingestion(
                output_raw_path=self.raw_path,
                output_manifest_path=self.manifest_path,
                allow_overwrite=False,
            )
        with open(self.raw_path, "r") as f:
            self.assertEqual(f.read(), "PRIOR RAW\n")
        self.assertFalse(os.path.exists(self.manifest_path))

        # 2. Existing manifest file refuses
        os.remove(self.raw_path)
        with open(self.manifest_path, "w") as f:
            f.write("PRIOR MANIFEST\n")
        with self.assertRaises(FileExistsError):
            run_bounded_ingestion(
                output_raw_path=self.raw_path,
                output_manifest_path=self.manifest_path,
                allow_overwrite=False,
            )
        with open(self.manifest_path, "r") as f:
            self.assertEqual(f.read(), "PRIOR MANIFEST\n")
        self.assertFalse(os.path.exists(self.raw_path))

    def test_recovery_failure_preserves_backups_and_reports_paths(self):
        existing_raw = b'{"parent_asin": "CRITICAL_OLD_P1"}\n'
        existing_manifest = b'{"old_manifest": true}\n'
        with open(self.raw_path, "wb") as f:
            f.write(existing_raw)
        with open(self.manifest_path, "wb") as f:
            f.write(existing_manifest)

        records = [
            {"parent_asin": "NEW_P1", "asin": "NEW_A1", "user_id": "U1", "rating": 5.0, "timestamp": 1612044451000}
        ]
        mock_streamer = self._create_dummy_streamer(records)

        original_replace = os.replace
        def mock_replace(src, dst):
            # Step 4a: raw replacement succeeds
            if "raw" in str(dst) and ".tmp." in str(src):
                return original_replace(src, dst)
            # Step 4b: manifest replacement fails
            if "manifest" in str(dst) and ".tmp." in str(src):
                raise OSError("Simulated disk error publishing manifest")
            # Recovery: restoring raw from .bak fails
            if "raw" in str(dst) and ".bak." in str(src):
                raise PermissionError("Simulated locked file: cannot restore raw file")
            return original_replace(src, dst)

        with patch("os.replace", side_effect=mock_replace):
            with self.assertRaises(RuntimeError) as ctx:
                run_bounded_ingestion(
                    output_raw_path=self.raw_path,
                    output_manifest_path=self.manifest_path,
                    streamer=mock_streamer,
                    allow_overwrite=True,
                )
            err_msg = str(ctx.exception)
            self.assertIn("Publication failed", err_msg)
            self.assertIn("automatic restoration failed", err_msg)
            self.assertIn("raw_backup=", err_msg)

        # Confirm the recoverable raw backup file STILL EXISTS on disk and has original data
        bak_files = [f for f in os.listdir(self.temp_dir) if ".bak." in f and "raw" in f]
        self.assertEqual(len(bak_files), 1)
        bak_full_path = os.path.join(self.temp_dir, bak_files[0])
        with open(bak_full_path, "rb") as f:
            self.assertEqual(f.read(), existing_raw)

    def test_no_misleading_manifest_after_stream_failure_with_overwrite(self):
        existing_manifest = b'{"old_manifest": "valid_prior_run"}\n'
        with open(self.manifest_path, "wb") as f:
            f.write(existing_manifest)

        mock_streamer = MagicMock()
        mock_streamer.url = "https://example.com/test.jsonl"
        def failing_stream():
            yield b'{"parent_asin": "P1", "asin": "A1", "user_id": "U1", "rating": 5.0, "timestamp": 1612044451000}\n', {}
            raise ConnectionResetError("Simulated network drop mid-stream")
        mock_streamer.stream_bytes = failing_stream

        with self.assertRaises(ConnectionResetError):
            run_bounded_ingestion(
                output_raw_path=self.raw_path,
                output_manifest_path=self.manifest_path,
                streamer=mock_streamer,
                allow_overwrite=True,
            )

        # Prior manifest must remain intact and unchanged
        with open(self.manifest_path, "rb") as f:
            self.assertEqual(f.read(), existing_manifest)
        self.assertFalse(os.path.exists(self.raw_path))


class TestCliSafetyLockSubprocess(unittest.TestCase):
    def test_cli_safety_lock_exits_zero_without_network(self):
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scripts",
            "ingest_sample.py",
        )
        proc = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=5.0,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("[SAFETY LOCK] Execution halted", proc.stdout)
        self.assertIn("--execute-live", proc.stdout)


if __name__ == "__main__":
    unittest.main()
