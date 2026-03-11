#!/usr/bin/env python3
"""
Search files on mounted SMB share with filters and local index caching.
First scan builds a JSON index (~74s for 4000+ files); subsequent searches are instant.

Usage:
  python3 smb_search.py /tmp/smb_mounts/DMFile/双师智学2026 --name "*.pptx"
  python3 smb_search.py /tmp/smb_mounts/DMFile --ext pptx,xlsx --max-depth 3
  python3 smb_search.py /tmp/smb_mounts/DMFile --size-gt 100M --top 20
  python3 smb_search.py /tmp/smb_mounts/DMFile --tree --max-depth 2
  python3 smb_search.py /tmp/smb_mounts/DMFile --rebuild
"""

import argparse
import fnmatch
import hashlib
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from preflight import ensure_cache_dir, ensure_existing_path


CACHE_DIR = Path.home() / ".cache" / "smb-file-index"


def parse_size(s):
    s = s.strip().upper()
    units = {"B": 1, "K": 1024, "M": 1024**2, "G": 1024**3}
    for unit, multiplier in units.items():
        if s.endswith(unit):
            return float(s[:-1]) * multiplier
    return float(s)


def fmt_size(n):
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def fmt_time(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def cache_path_for(root):
    key = hashlib.md5(root.encode()).hexdigest()[:12]
    name = os.path.basename(root.rstrip("/")) or "root"
    return CACHE_DIR / f"{name}_{key}.json"


def ensure_runtime_ready(root=None):
    """Validate local runtime and optional SMB mount path."""
    if not ensure_cache_dir(CACHE_DIR):
        return False
    return ensure_existing_path(root, label="Search root", should_be_dir=True, mount_hint=True)


def build_index(root, max_depth=4, max_files=10000):
    """Walk SMB share and build file index with progress reporting."""
    files = []
    count = 0
    dirs_scanned = 0
    root_depth = root.rstrip(os.sep).count(os.sep)
    start_ts = time.time()

    for dirpath, dirnames, filenames in os.walk(root):
        depth = dirpath.rstrip(os.sep).count(os.sep) - root_depth
        if max_depth is not None and depth >= max_depth:
            dirnames.clear()
        dirs_scanned += 1
        if dirs_scanned % 10 == 0:
            rel = os.path.relpath(dirpath, root)
            elapsed = time.time() - start_ts
            print(
                f"\r[index] {count} files, {dirs_scanned} dirs, {elapsed:.0f}s ... {rel[:50]}",
                end="",
                flush=True,
                file=sys.stderr,
            )
        for filename in filenames:
            if filename.startswith("."):
                continue
            count += 1
            if count > max_files:
                print(f"\n[warn] Index capped at {max_files} files.", file=sys.stderr)
                return files
            filepath = os.path.join(dirpath, filename)
            try:
                stat = os.stat(filepath)
                files.append(
                    {
                        "path": os.path.relpath(filepath, root),
                        "size": stat.st_size,
                        "mtime": stat.st_mtime,
                    }
                )
            except OSError:
                pass

    elapsed = time.time() - start_ts
    print(
        f"\r[index] Done: {count} files, {dirs_scanned} dirs in {elapsed:.1f}s{' ' * 30}",
        file=sys.stderr,
    )
    return files


def load_or_build_index(root, max_depth, max_files, force_rebuild=False):
    """Load cached index or build a new one."""
    cache_path = cache_path_for(root)
    if not force_rebuild and cache_path.exists():
        age_hours = (time.time() - cache_path.stat().st_mtime) / 3600
        try:
            data = json.loads(cache_path.read_text())
            meta = data.get("meta", {})
            print(
                f"[cache] Loaded {len(data['files'])} files from index "
                f"(built {age_hours:.1f}h ago, depth={meta.get('max_depth', '?')})",
                file=sys.stderr,
            )
            if age_hours > 24:
                print("[cache] Index older than 24h. Use --rebuild to refresh.", file=sys.stderr)
            return data["files"]
        except (json.JSONDecodeError, KeyError):
            pass

    print(f"[index] Building index for {root} (depth={max_depth})...", file=sys.stderr)
    files = build_index(root, max_depth, max_files)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "meta": {
            "root": root,
            "max_depth": max_depth,
            "file_count": len(files),
            "built_at": datetime.now().isoformat(),
        },
        "files": files,
    }
    cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=None))
    print(f"[index] Saved to {cache_path}", file=sys.stderr)
    return files


def search(all_files, args):
    results = []
    for entry in all_files:
        filename = os.path.basename(entry["path"])

        if args.name and not fnmatch.fnmatch(filename.lower(), args.name.lower()):
            continue

        if args.ext:
            exts = [ext.strip().lower().lstrip(".") for ext in args.ext.split(",")]
            file_ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            if file_ext not in exts:
                continue

        if args.size_gt and entry["size"] < parse_size(args.size_gt):
            continue
        if args.size_lt and entry["size"] > parse_size(args.size_lt):
            continue

        if args.path_contains and args.path_contains.lower() not in entry["path"].lower():
            continue

        results.append(entry)

    if args.sort == "size":
        results.sort(key=lambda item: item["size"], reverse=True)
    elif args.sort == "date":
        results.sort(key=lambda item: item["mtime"], reverse=True)
    elif args.sort == "name":
        results.sort(key=lambda item: item["path"].lower())

    if args.top:
        results = results[:args.top]

    return results


def print_tree(root, max_depth=2, prefix=""):
    try:
        entries = sorted(os.listdir(root))
    except OSError:
        return
    dirs = [entry for entry in entries if os.path.isdir(os.path.join(root, entry)) and not entry.startswith(".")]
    files = [entry for entry in entries if os.path.isfile(os.path.join(root, entry)) and not entry.startswith(".")]

    for idx, filename in enumerate(files):
        connector = "└── " if (idx == len(files) - 1 and not dirs) else "├── "
        try:
            size = fmt_size(os.path.getsize(os.path.join(root, filename)))
        except OSError:
            size = "?"
        print(f"{prefix}{connector}{filename}  ({size})")

    for idx, dirname in enumerate(dirs):
        connector = "└── " if idx == len(dirs) - 1 else "├── "
        print(f"{prefix}{connector}{dirname}/")
        if max_depth > 1:
            ext = "    " if idx == len(dirs) - 1 else "│   "
            print_tree(os.path.join(root, dirname), max_depth - 1, prefix + ext)


def main():
    parser = argparse.ArgumentParser(description="SMB File Search (with index cache)")
    parser.add_argument("root", nargs="?", help="Mount path to search")
    parser.add_argument("--name", help="Filename glob pattern (e.g. '*.pptx')")
    parser.add_argument("--ext", help="Comma-separated extensions (e.g. 'pptx,xlsx')")
    parser.add_argument("--path-contains", help="Filter by path substring (e.g. 'level 1')")
    parser.add_argument("--size-gt", help="Min file size (e.g. '10M', '1G')")
    parser.add_argument("--size-lt", help="Max file size (e.g. '100M')")
    parser.add_argument("--max-depth", type=int, default=3, help="Max scan depth (default: 3)")
    parser.add_argument("--max-files", type=int, default=10000, help="Max files to index (default: 10000)")
    parser.add_argument("--sort", choices=["size", "date", "name"], default="name")
    parser.add_argument("--top", type=int, help="Show top N results")
    parser.add_argument("--tree", action="store_true", help="Show directory tree (no cache, direct SMB)")
    parser.add_argument("--rebuild", action="store_true", help="Force rebuild index")
    parser.add_argument("--stats", action="store_true", help="Show index statistics")
    parser.add_argument("--check-tools", action="store_true", help="Check runtime readiness and optional mount path")
    args = parser.parse_args()

    if args.check_tools:
        if ensure_runtime_ready(args.root):
            print("[ok] SMB search runtime is ready.")
            return
        sys.exit(1)

    if not args.root:
        parser.error("root is required unless --check-tools is used")

    if not ensure_runtime_ready(args.root):
        sys.exit(1)

    if args.tree:
        print(f"{os.path.basename(args.root)}/")
        print_tree(args.root, args.max_depth)
        return

    root = os.path.abspath(args.root)
    all_files = load_or_build_index(root, args.max_depth, args.max_files, args.rebuild)

    if args.stats:
        total_size = sum(item["size"] for item in all_files)
        exts = {}
        for item in all_files:
            ext = os.path.basename(item["path"]).rsplit(".", 1)[-1].lower() if "." in item["path"] else "(none)"
            exts[ext] = exts.get(ext, 0) + 1
        print(f"Total files: {len(all_files)}")
        print(f"Total size:  {fmt_size(total_size)}")
        print("\nTop extensions:")
        for ext, count in sorted(exts.items(), key=lambda pair: -pair[1])[:15]:
            print(f"  .{ext:10s} {count:>5} files")
        return

    results = search(all_files, args)
    if not results:
        print("[info] No files found matching criteria.")
        return

    print(f"{'Size':>10}  {'Modified':>16}  Path")
    print("-" * 80)
    for result in results:
        print(f"{fmt_size(result['size']):>10}  {fmt_time(result['mtime']):>16}  {result['path']}")
    print(f"\n[info] {len(results)} file(s) found.")


if __name__ == "__main__":
    main()
