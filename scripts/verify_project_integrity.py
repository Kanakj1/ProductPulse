"""
ProductPulse — Project Integrity Verification Tool
Computes SHA-256 cryptographic hashes and byte counts for all protected project assets
and verifies them against established, immutable baselines. Also checks SQLite integrity.
"""
import hashlib
import os
import sqlite3
import sys
from typing import Dict, Tuple

BASELINE_INVENTORY: Dict[str, Dict[str, any]] = {
    "data/raw/sample_reviews_cell_phones_25k.jsonl": {
        "expected_bytes": 14241285,
        "expected_sha256": "86eca6adea79bb125fb373bde6a1d5b0e8027211754ba229b171e6d42f5e495a"
    },
    "backend/db/productpulse.db": {
        "expected_bytes": 27574272,
        "expected_sha256": "f64b742e29c5c82c8231a740cf56477cc5d35ed45142ef4d6f86ca60a4f22b4c"
    },
    "data/annotation/sample_a_aspect_detection_template.csv": {
        "expected_bytes": 49310,
        "expected_sha256": "e44196496dc7c8832e3dd9b5bbfd92e414d66295dc452c895316010d828799bf"
    },
    "data/annotation/sample_b_aspect_sentiment_template.csv": {
        "expected_bytes": 79631,
        "expected_sha256": "4488811196d689b7ce684e8cdfecb23acc3d8b7a34ecf47bbdf6f5e70c4b04f4"
    },
    "data/annotation/sample_a_aspect_detection_template.jsonl": {
        "expected_bytes": 1160776,
        "expected_sha256": "31f9f20feeae9d746a1a933a2ade9e3c38c97612524b1eb2c848e3351758094c"
    },
    "data/annotation/sample_b_aspect_sentiment_template.jsonl": {
        "expected_bytes": 207551,
        "expected_sha256": "a362db3b1ac4e57a88d75bfe0532eee5b786e498419bec90c6ba3ba31eebb573"
    },
    "data/annotation/sampling_manifest.json": {
        "expected_bytes": 2133,
        "expected_sha256": "1698f0c542c34c383a4eec8d576d0fb476de4798f55eb9eb7c973ca03a63ad36"
    },
    "data/annotation/sample_a_aspect_detection_auto_draft.csv": {
        "expected_bytes": 59046,
        "expected_sha256": "3890be6abd1464dfe4f7a39f47f1ae19ff8da2168220bb482fbf545945d43df5"
    },
    "data/annotation/sample_b_aspect_sentiment_auto_draft.csv": {
        "expected_bytes": 103345,
        "expected_sha256": "9ff490e8042801dc1cb54bb35d72f90e94c28cfe1b82f1f164e5b391ddccd360"
    },
    "data/annotation/sample_a_auto_reconciled.jsonl": {
        "expected_bytes": 860205,
        "expected_sha256": "9d801491e232910f138c3466c9873d3638fc2ff0a84c084f4634783e5fbc5c48"
    },
    "data/annotation/sample_b_auto_reconciled.jsonl": {
        "expected_bytes": 168679,
        "expected_sha256": "cde6c4b5b89a22d6d42f36efd56a4058bb4c73239770c40df992734e61f0edbf"
    },
    "data/annotation/auto_draft_generation_report.json": {
        "expected_bytes": 2015,
        "expected_sha256": "c6faf5fab5f571ce498ba6462e2ef1e69853b5a1b17ccdb6d7cd85f751c64108"
    },
    "data/annotation/sample_a_aspect_detection_auto_draft_v2.csv": {
        "expected_bytes": 58892,
        "expected_sha256": "a224ed54b2aaa0bbd586ccb33f41847ff42087a15d91a1ce87bd8d4bfe33e3bd"
    },
    "data/annotation/sample_b_aspect_sentiment_auto_draft_v2.csv": {
        "expected_bytes": 103093,
        "expected_sha256": "fc232cd79223c9c1e57c5d5610b2f0cd5ad033d5e9f0ba523a01c3e3763c2a75"
    },
    "data/annotation/sample_a_auto_reconciled_v2.jsonl": {
        "expected_bytes": 859297,
        "expected_sha256": "3d5db4af5b2143d987fc81369f36da1b6058c686fec023288b7ec4a6103935bc"
    },
    "data/annotation/sample_b_auto_reconciled_v2.jsonl": {
        "expected_bytes": 168429,
        "expected_sha256": "13bfada65ffd3ee694d072eed2d8088a2b2318c12121b4afd04c42070459e04d"
    },
    "data/annotation/auto_draft_generation_report_v2.json": {
        "expected_bytes": 2539,
        "expected_sha256": "799161559e58b5016d211114755e98d234dc50e962d42a7bdbd6af5b2fa0936b"
    }
}


def verify_file_hashes() -> Tuple[bool, Dict[str, Dict]]:
    """Calculates SHA-256 for all protected files and compares with baseline."""
    results = {}
    all_passed = True

    for rel_path, expected in BASELINE_INVENTORY.items():
        if not os.path.exists(rel_path):
            results[rel_path] = {
                "status": "FAIL",
                "reason": "FILE_NOT_FOUND",
                "actual_sha256": None,
                "expected_sha256": expected["expected_sha256"]
            }
            all_passed = False
            continue

        actual_size = os.path.getsize(rel_path)
        with open(rel_path, "rb") as f:
            actual_sha256 = hashlib.sha256(f.read()).hexdigest()

        hash_matches = (actual_sha256 == expected["expected_sha256"])
        size_matches = (actual_size == expected["expected_bytes"])

        if hash_matches and size_matches:
            results[rel_path] = {
                "status": "PASS",
                "bytes": actual_size,
                "sha256": actual_sha256
            }
        else:
            results[rel_path] = {
                "status": "FAIL",
                "reason": "CHECKSUM_OR_SIZE_MISMATCH",
                "actual_bytes": actual_size,
                "expected_bytes": expected["expected_bytes"],
                "actual_sha256": actual_sha256,
                "expected_sha256": expected["expected_sha256"]
            }
            all_passed = False

    return all_passed, results


def verify_sqlite_db(db_path: str = "backend/db/productpulse.db") -> Tuple[bool, Dict]:
    """Runs SQLite PRAGMA integrity and foreign key checks."""
    if not os.path.exists(db_path):
        return False, {"error": "Database file not found"}

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    c = conn.cursor()

    c.execute("PRAGMA integrity_check")
    integ = c.fetchall()

    c.execute("PRAGMA foreign_key_check")
    fk = c.fetchall()

    c.execute("SELECT COUNT(*) FROM reviews")
    rev_cnt = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM products")
    prod_cnt = c.fetchone()[0]

    conn.close()

    is_clean = (integ == [("ok",)] and fk == [] and rev_cnt == 25000 and prod_cnt == 19065)
    return is_clean, {
        "integrity_check": integ,
        "foreign_key_violations": fk,
        "reviews_count": rev_cnt,
        "products_count": prod_cnt
    }


def main():
    print("================================================================================")
    print(" ProductPulse — Project Integrity Verification")
    print("================================================================================")

    files_ok, file_results = verify_file_hashes()
    for path, res in file_results.items():
        status = res["status"]
        if status == "PASS":
            print(f"[{status}] {path} ({res['bytes']:,} bytes)")
        else:
            print(f"[{status}] {path} -> {res.get('reason')}")
            print(f"       Expected SHA-256: {res.get('expected_sha256')}")
            print(f"       Actual SHA-256:   {res.get('actual_sha256')}")

    db_ok, db_results = verify_sqlite_db()
    print("\n--------------------------------------------------------------------------------")
    print(f"SQLite DB Check: {'PASS' if db_ok else 'FAIL'}")
    print(f"  Reviews:  {db_results.get('reviews_count')} (expected 25,000)")
    print(f"  Products: {db_results.get('products_count')} (expected 19,065)")
    print(f"  PRAGMA integrity_check: {db_results.get('integrity_check')}")
    print(f"  PRAGMA foreign_key_check: {db_results.get('foreign_key_violations')}")
    print("================================================================================")

    if files_ok and db_ok:
        print("[SUCCESS] All 17 protected assets and SQLite database verified 100% intact.")
        sys.exit(0)
    else:
        print("[ERROR] Integrity verification failed! Stop and report discrepancies.")
        sys.exit(1)


if __name__ == "__main__":
    main()
