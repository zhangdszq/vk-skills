#!/usr/bin/env python3
"""
Download files from mounted SMB share with bandwidth control and resume support.
Designed for large files over low-bandwidth networks.

Usage:
  python3 smb_download.py "/tmp/smb_mounts/DMFile/双师智学2026/level 1/U1" ./downloads/
  python3 smb_download.py /tmp/smb_mounts/DMFile/file.pptx ./local/ --bw-limit 5M
  python3 smb_download.py /tmp/smb_mounts/DMFile/big/ ./local/ --ext pptx --dry-run
"""

import argparse
import os
import sys
import time

from preflight import ensure_existing_path, ensure_writable_dir


def parse_bw(s):
    """Parse bandwidth limit like '5M' to bytes/sec."""
    if not s:
        return None
    s = s.strip().upper()
    units = {"K": 1024, "M": 1024**2, "G": 1024**3}
    for unit, multiplier in units.items():
        if s.endswith(unit):
            return int(float(s[:-1]) * multiplier)
    return int(s)


def fmt_size(n):
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def copy_with_progress(src, dst, bw_limit=None):
    """Copy file with progress display and optional bandwidth limiting."""
    total = os.path.getsize(src)
    copied = 0

    if os.path.exists(dst) and os.path.getsize(dst) == total:
        print(f"  [skip] Already exists: {os.path.basename(dst)}")
        return True

    partial = dst + ".partial"
    if os.path.exists(partial):
        copied = os.path.getsize(partial)
        print(f"  [resume] From {fmt_size(copied)}/{fmt_size(total)}")

    chunk_size = min(bw_limit or 8 * 1024 * 1024, 8 * 1024 * 1024)
    start_ts = time.time()

    try:
        with open(src, "rb") as fin:
            mode = "ab" if copied > 0 else "wb"
            fin.seek(copied)
            with open(partial, mode) as fout:
                while True:
                    chunk = fin.read(chunk_size)
                    if not chunk:
                        break
                    fout.write(chunk)
                    copied += len(chunk)

                    elapsed = time.time() - start_ts
                    speed = copied / elapsed if elapsed > 0 else 0
                    pct = (copied / total * 100) if total > 0 else 100
                    print(
                        f"\r  [{pct:5.1f}%] {fmt_size(copied)}/{fmt_size(total)} "
                        f"@ {fmt_size(speed)}/s",
                        end="",
                        flush=True,
                    )

                    if bw_limit and speed > bw_limit:
                        time.sleep(len(chunk) / bw_limit - len(chunk) / speed)

        os.rename(partial, dst)
        elapsed = time.time() - start_ts
        print(f"\r  [done] {fmt_size(total)} in {elapsed:.1f}s")
        return True
    except KeyboardInterrupt:
        print(f"\n  [paused] Partial saved: {partial}")
        return False
    except OSError as exc:
        print(f"\n  [error] {exc}")
        return False


def collect_files(src, ext_filter=None):
    """Collect files to download, optionally filtering by extension."""
    if os.path.isfile(src):
        return [(src, os.path.basename(src))]

    files = []
    for dirpath, _, filenames in os.walk(src):
        for filename in filenames:
            if filename.startswith("."):
                continue
            if ext_filter:
                exts = [ext.strip().lower().lstrip(".") for ext in ext_filter.split(",")]
                file_ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
                if file_ext not in exts:
                    continue
            full = os.path.join(dirpath, filename)
            rel = os.path.relpath(full, src)
            files.append((full, rel))
    return files


def ensure_runtime_ready(source=None, dest=None):
    """Validate source mount path and optional local destination."""
    if not ensure_existing_path(source, label="Source", mount_hint=True):
        return False
    return ensure_writable_dir(dest, label="Destination")


def main():
    parser = argparse.ArgumentParser(description="SMB File Downloader")
    parser.add_argument("source", nargs="?", help="Source path on mounted share")
    parser.add_argument("dest", nargs="?", help="Local destination directory")
    parser.add_argument("--ext", help="Filter by extensions (e.g. 'pptx,xlsx')")
    parser.add_argument("--bw-limit", help="Bandwidth limit (e.g. '5M', '500K')")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be downloaded")
    parser.add_argument("--check-tools", action="store_true", help="Check runtime readiness, source mount, and optional destination")
    args = parser.parse_args()

    if args.check_tools:
        if ensure_runtime_ready(args.source, args.dest):
            print("[ok] SMB download runtime is ready.")
            return
        sys.exit(1)

    if not args.source or not args.dest:
        parser.error("source and dest are required unless --check-tools is used")

    if not ensure_runtime_ready(args.source, args.dest if not args.dry_run else None):
        sys.exit(1)

    files = collect_files(args.source, args.ext)
    if not files:
        print("[info] No files match criteria.")
        return

    total_size = sum(os.path.getsize(item[0]) for item in files)
    print(f"[info] {len(files)} file(s), total {fmt_size(total_size)}")

    if args.dry_run:
        for src, rel in files:
            print(f"  {fmt_size(os.path.getsize(src)):>10}  {rel}")
        return

    os.makedirs(args.dest, exist_ok=True)
    bw = parse_bw(args.bw_limit)
    ok = 0

    for idx, (src, rel) in enumerate(files, 1):
        dst = os.path.join(args.dest, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        print(f"[{idx}/{len(files)}] {rel}")
        if copy_with_progress(src, dst, bw):
            ok += 1

    print(f"\n[done] {ok}/{len(files)} files downloaded to {args.dest}")


if __name__ == "__main__":
    main()
