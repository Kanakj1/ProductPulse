#!/usr/bin/env python3
"""
ProductPulse — High-Speed Multi-Threaded Apache Hive 3.1.3 Downloader
Downloads apache-hive-3.1.3-bin.tar.gz using parallel byte ranges and verifies SHA-256.
Expected SHA-256: 0c9b6a6359a7341b6029cc9347435ee7b379f93846f779d710b13f795b54bb16
"""
import os
import sys
import hashlib
import threading
import urllib.request
from concurrent.futures import ThreadPoolExecutor

EXPECTED_SHA256 = "0c9b6a6359a7341b6029cc9347435ee7b379f93846f779d710b13f795b54bb16"
DOWNLOAD_URL = "https://archive.apache.org/dist/hive/hive-3.1.3/apache-hive-3.1.3-bin.tar.gz"
TARGET_DIR = os.path.join(os.path.dirname(__file__), "downloads")
TARGET_FILE = os.path.join(TARGET_DIR, "apache-hive-3.1.3-bin.tar.gz")
NUM_THREADS = 12


def verify_existing():
    if os.path.exists(TARGET_FILE):
        hasher = hashlib.sha256()
        with open(TARGET_FILE, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        calc_sha = hasher.hexdigest().lower()
        if calc_sha == EXPECTED_SHA256:
            print(f"[PASS] File already exists and SHA-256 matches: {calc_sha}")
            return True
        else:
            print(f"[WARN] Existing file hash mismatch ({calc_sha}). Removing...")
            os.remove(TARGET_FILE)
    return False


def download_chunk(url, start_byte, end_byte, file_path, lock, progress_tracker):
    req = urllib.request.Request(url, headers={"Range": f"bytes={start_byte}-{end_byte}", "User-Agent": "ProductPulse/1.0"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = resp.read()
    with lock:
        with open(file_path, "r+b") as f:
            f.seek(start_byte)
            f.write(data)
        progress_tracker["downloaded"] += len(data)
        total = progress_tracker["total"]
        pct = (progress_tracker["downloaded"] / total) * 100
        mb = progress_tracker["downloaded"] / (1024 * 1024)
        sys.stdout.write(f"\rDownloaded {mb:.1f} MB / {total / (1024*1024):.1f} MB ({pct:.1f}%)")
        sys.stdout.flush()


def main():
    os.makedirs(TARGET_DIR, exist_ok=True)
    if verify_existing():
        return TARGET_FILE

    print(f"Connecting to {DOWNLOAD_URL}...")
    req = urllib.request.Request(DOWNLOAD_URL, method="HEAD", headers={"User-Agent": "ProductPulse/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        total_size = int(resp.getheader("Content-Length", 0))

    if total_size <= 0:
        raise ValueError("Failed to retrieve Content-Length from server")

    print(f"Total size: {total_size / (1024*1024):.1f} MB ({total_size:,} bytes). Allocating file...")
    with open(TARGET_FILE, "wb") as f:
        f.seek(total_size - 1)
        f.write(b"\0")

    chunk_size = (total_size + NUM_THREADS - 1) // NUM_THREADS
    ranges = []
    for i in range(NUM_THREADS):
        start = i * chunk_size
        end = min(start + chunk_size - 1, total_size - 1)
        if start <= end:
            ranges.append((start, end))

    print(f"Starting parallel download with {len(ranges)} threads...")
    lock = threading.Lock()
    progress = {"downloaded": 0, "total": total_size}

    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = [
            executor.submit(download_chunk, DOWNLOAD_URL, start, end, TARGET_FILE, lock, progress)
            for start, end in ranges
        ]
        for fut in futures:
            fut.result()

    print("\nVerifying SHA-256 hash...")
    hasher = hashlib.sha256()
    with open(TARGET_FILE, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)

    calc_sha = hasher.hexdigest().lower()
    print(f"Calculated SHA-256: {calc_sha}")
    print(f"Expected   SHA-256: {EXPECTED_SHA256}")
    if calc_sha == EXPECTED_SHA256:
        print("[SUCCESS] Checksum verified. Download is authentic.")
        return TARGET_FILE
    else:
        raise ValueError(f"Checksum mismatch: {calc_sha} != {EXPECTED_SHA256}")


if __name__ == "__main__":
    main()
