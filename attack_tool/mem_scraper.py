#!/usr/bin/python3
"""VaultLLM Security Demo — Memory Scraper Tool

Purpose:
  Demonstrates data-in-use memory exposure in local LLM processes by inspecting
  process memory via Linux /proc/[pid]/mem and /proc/[pid]/maps.

Scope & Safety Constraints (RULES.md Section 2):
  - This tool may ONLY be run against processes started by this project for
    authorized demonstration and testing purposes.
  - It must never be pointed at any third-party, production, or shared system.
  - Synthetic / fictional placeholders (e.g. 'Project-Titan-Alpha') must be used.

Theoretical Context:
  Demonstrates the CPU/RAM equivalent of the data-in-use memory exposure category
  highlighted in CVE-2023-4969 (LeftoverLocals), where data residing in RAM can
  be inspected by any user or malware possessing administrative (root) rights.
"""

import os
import sys
import errno
import re
from pathlib import Path


def get_process_cmdline(pid: int) -> str:
    """Read cmdline for safety check to ensure target is a VaultLLM process."""
    cmdline_path = f"/proc/{pid}/cmdline"
    try:
        with open(cmdline_path, "rb") as f:
            raw = f.read()
            return raw.replace(b"\x00", b" ").decode(errors="replace").strip()
    except Exception:
        return ""


def validate_target_process(pid: int):
    """Safety check: Verify PID exists and belongs to the project."""
    proc_dir = Path(f"/proc/{pid}")
    if not proc_dir.exists():
        print(f"Error: No such process with PID {pid}", file=sys.stderr)
        sys.exit(1)

    cmdline = get_process_cmdline(pid)
    # Validate that the process is related to python / uvicorn / vaultllm
    if not any(token in cmdline.lower() for token in ["python", "uvicorn", "vaultllm", "server"]):
        print(
            f"[SAFETY WARNING] PID {pid} cmdline ('{cmdline}') does not appear to be a VaultLLM process.\n"
            f"Per RULES.md, mem_scraper.py may only be run against VaultLLM project processes.",
            file=sys.stderr
        )
        sys.exit(1)


def parse_memory_maps(pid: int):
    """Parse /proc/[pid]/maps for readable memory regions."""
    maps_path = f"/proc/{pid}/maps"
    try:
        with open(maps_path, "r") as f:
            lines = f.readlines()
    except PermissionError:
        print("Permission denied: Reading /proc/[pid]/maps requires root/sudo privileges.", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: No such process with PID {pid}", file=sys.stderr)
        sys.exit(1)

    regions = []
    # Pattern: 55e2a3c00000-55e2a3c21000 rw-p 00000000 00:00 0 [heap]
    for line in lines:
        parts = line.strip().split()
        if len(parts) < 2:
            continue
        addr_range = parts[0]
        perms = parts[1]
        pathname = parts[5] if len(parts) >= 6 else ""

        # Only search readable mappings
        if not perms.startswith("r"):
            continue

        # Skip special virtual mappings that cannot be read from /proc/pid/mem
        if pathname in ["[vsyscall]", "[vdso]", "[vvar]"] or pathname.startswith("/dev/"):
            continue

        start_str, end_str = addr_range.split("-")
        start_addr = int(start_str, 16)
        end_addr = int(end_str, 16)
        regions.append((start_addr, end_addr, perms, pathname))

    return regions


def scrape_memory(pid: int, search_str: str, max_matches: int = 10):
    """Scrape /proc/[pid]/mem for occurrences of search_str."""
    validate_target_process(pid)
    regions = parse_memory_maps(pid)
    mem_path = f"/proc/{pid}/mem"

    search_bytes = search_str.encode("utf-8")
    search_len = len(search_bytes)
    matches = []

    print(f"[*] Target PID: {pid} ({get_process_cmdline(pid)})")
    print(f"[*] Target pattern: \"{search_str}\" ({search_len} bytes)")
    print(f"[*] Searching across {len(regions)} readable memory mappings...")

    try:
        with open(mem_path, "rb", buffering=0) as mem_file:
            for start_addr, end_addr, perms, pathname in regions:
                region_len = end_addr - start_addr
                if region_len <= 0 or region_len > 1024 * 1024 * 1024:  # Safety cap at 1GB per region
                    continue

                chunk_size = 1024 * 1024  # 1MB chunks
                overlap = search_len - 1
                offset = 0

                while offset < region_len:
                    read_size = min(chunk_size, region_len - offset)
                    curr_addr = start_addr + offset

                    try:
                        mem_file.seek(curr_addr)
                        chunk = mem_file.read(read_size)
                    except (OSError, IOError) as err:
                        # Unmapped or guard page; skip to next mapping
                        break

                    if not chunk:
                        break

                    # Search for pattern in chunk
                    idx = 0
                    while True:
                        found_idx = chunk.find(search_bytes, idx)
                        if found_idx == -1:
                            break

                        match_addr = curr_addr + found_idx
                        # Extract surrounding context (up to 40 bytes before and 80 bytes after)
                        ctx_start = max(0, found_idx - 40)
                        ctx_end = min(len(chunk), found_idx + search_len + 80)
                        raw_context = chunk[ctx_start:ctx_end]
                        clean_context = "".join(
                            chr(b) if 32 <= b <= 126 else "." for b in raw_context
                        )

                        match_info = {
                            "address": hex(match_addr),
                            "region": f"0x{start_addr:x}-0x{end_addr:x}",
                            "perms": perms,
                            "pathname": pathname or "[anon]",
                            "context": clean_context
                        }
                        matches.append(match_info)

                        if len(matches) >= max_matches:
                            return matches

                        idx = found_idx + 1

                    if len(chunk) < read_size or read_size < chunk_size:
                        break

                    offset += (chunk_size - overlap)

    except PermissionError:
        print("Permission denied: Reading /proc/[pid]/mem requires root/sudo privileges.", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: No such process with PID {pid}", file=sys.stderr)
        sys.exit(1)

    return matches


def main():
    if len(sys.argv) < 3:
        print(f"Usage: sudo python3 {sys.argv[0]} <PID> <SEARCH_STRING> [MAX_MATCHES]")
        print("Example: sudo python3 mem_scraper.py 12345 'Project-Titan-Alpha'")
        sys.exit(1)

    try:
        target_pid = int(sys.argv[1])
    except ValueError:
        print(f"Error: Invalid PID '{sys.argv[1]}'. Must be an integer.", file=sys.stderr)
        sys.exit(1)

    search_pattern = sys.argv[2]
    max_matches = int(sys.argv[3]) if len(sys.argv) > 3 else 10

    matches = scrape_memory(target_pid, search_pattern, max_matches=max_matches)

    print("\n" + "=" * 70)
    if matches:
        print(f"[!] ATTACK SUCCESSFUL: Found {len(matches)} occurrence(s) of \"{search_pattern}\" in live RAM!")
        print("=" * 70)
        for i, m in enumerate(matches, 1):
            print(f"Match #{i}:")
            print(f"  Memory Address : {m['address']}")
            print(f"  Mapping Region : {m['region']} ({m['perms']}) {m['pathname']}")
            print(f"  Live Memory Snippet:")
            print(f"    {m['context']}")
            print("-" * 70)
        sys.exit(0)
    else:
        print(f"[-] ATTACK NEGATIVE: Pattern \"{search_pattern}\" not found in scanned memory regions.")
        print("=" * 70)
        sys.exit(2)


if __name__ == "__main__":
    main()
