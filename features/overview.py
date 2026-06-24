from registry import register
from helpers import section, concept, fmt_kv


@register("overview", "Process memory overview from /proc/<pid>/status")
def feature_overview(pid: int) -> None:
    section("Process Memory Overview", f"/proc/{pid}/status")

    try:
        raw = {}
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if ":" in line:
                    k, v = line.split(":", 1)
                    raw[k.strip()] = v.strip()
    except FileNotFoundError:
        print(f"  [error] /proc/{pid}/status not found — process may have exited")
        return
    except PermissionError:
        print(f"  [error] permission denied reading /proc/{pid}/status")
        return

    FIELDS = [
        ("VmPeak",  "peak virtual memory — highest watermark since process start"),
        ("VmSize",  "current virtual address space size — includes unmapped regions"),
        ("VmRSS",   "resident set size — pages actually in physical RAM"),
        ("VmSwap",  "pages currently swapped out to disk"),
        ("VmStk",   "stack segment size"),
        ("VmData",  "data + BSS segment size (heap lives here)"),
        ("VmLib",   "shared library code size"),
        ("VmPTE",   "page table entries — overhead of mapping virtual→physical"),
    ]
    for key, annotation in FIELDS:
        fmt_kv(key, raw.get(key, "n/a"), annotation)

    concept(
        "VmSize >> VmRSS because Linux uses demand paging — virtual address "
        "ranges are reserved with mmap() but pages are only faulted into "
        "physical RAM on first access. A 500 MB mmap() costs zero physical "
        "pages until you touch the data. The gap between VmSize and VmRSS "
        "is the 'lazy' portion: allocated but never yet touched. "
        "VmPTE shows the cost of maintaining the virtual-to-physical mapping "
        "itself — each 4 KB page needs an entry in the page table hierarchy."
    )
