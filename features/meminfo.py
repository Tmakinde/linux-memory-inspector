from registry import register
from helpers import section, concept, fmt_kv


@register("meminfo", "System-wide memory from /proc/meminfo")
def feature_meminfo(pid: int) -> None:
    section("/proc/meminfo Inspector", "/proc/meminfo")

    try:
        raw = {}
        with open("/proc/meminfo") as f:
            for line in f:
                if ":" in line:
                    k, v = line.split(":", 1)
                    raw[k.strip()] = v.strip()
    except FileNotFoundError:
        print("  [error] /proc/meminfo not found")
        return

    def kb(key):
        val = raw.get(key, "0 kB")
        return int(val.split()[0]) if val and val != "n/a" else 0

    mem_total     = kb("MemTotal")
    mem_available = kb("MemAvailable") or kb("MemFree")
    used          = mem_total - mem_available

    print()
    print("  -- Physical RAM --")
    fmt_kv("MemTotal",        raw.get("MemTotal", "n/a"),
           "total installed RAM")
    fmt_kv("MemFree",         raw.get("MemFree", "n/a"),
           "completely unused pages (misleading — see CONCEPT)")
    if "MemAvailable" in raw:
        fmt_kv("MemAvailable", raw["MemAvailable"],
               "estimated reclaimable memory for new allocations")
    else:
        fmt_kv("MemAvailable", "n/a", "kernel < 3.14 — field absent, using MemFree")
    fmt_kv("UsedRAM",         f"{used} kB",
           "derived: MemTotal - MemAvailable")

    print()
    print("  -- Kernel-managed pages --")
    fmt_kv("Buffers",         raw.get("Buffers", "n/a"),
           "block device I/O buffer cache")
    fmt_kv("Cached",          raw.get("Cached", "n/a"),
           "page cache — cached file contents")
    fmt_kv("SwapCached",      raw.get("SwapCached", "n/a"),
           "swapped-out pages still present in RAM (counted in both)")
    fmt_kv("Slab",            raw.get("Slab", "n/a"),
           "kernel slab allocator — kernel data structures")
    fmt_kv("SReclaimable",    raw.get("SReclaimable", "n/a"),
           "slab pages the kernel can reclaim under pressure")
    fmt_kv("SUnreclaim",      raw.get("SUnreclaim", "n/a"),
           "slab pages that cannot be reclaimed")

    print()
    print("  -- Swap --")
    fmt_kv("SwapTotal",       raw.get("SwapTotal", "n/a"),
           "total swap space")
    fmt_kv("SwapFree",        raw.get("SwapFree", "n/a"),
           "unused swap space")

    print()
    print("  -- Kernel internals --")
    fmt_kv("PageTables",      raw.get("PageTables", "n/a"),
           "total memory used by page tables across all processes")
    fmt_kv("VmallocTotal",    raw.get("VmallocTotal", "n/a"),
           "virtual address space reserved for vmalloc()")
    fmt_kv("VmallocUsed",     raw.get("VmallocUsed", "n/a"),
           "vmalloc space currently allocated")
    fmt_kv("HugePages_Total", raw.get("HugePages_Total", "n/a"),
           "pre-allocated huge pages (2 MB each)")
    fmt_kv("AnonHugePages",   raw.get("AnonHugePages", "n/a"),
           "THP: transparent huge pages in use by processes")

    print()
    print("  -- Conclusion: Is memory actually full? --")

    cache_and_buf = kb("Cached") + kb("Buffers") + kb("SReclaimable")
    cache_pct     = (cache_and_buf / mem_total * 100) if mem_total else 0
    avail_pct     = (mem_available / mem_total * 100) if mem_total else 0

    if avail_pct > 20:
        verdict = "HEALTHY"
        note    = "MemAvailable is comfortable; no pressure"
    elif cache_pct > 30 and avail_pct > 5:
        verdict = "HEALTHY (cache-heavy)"
        note    = "Low MemFree is page cache, NOT a shortage — kernel can reclaim it"
    elif avail_pct > 10:
        verdict = "MODERATE PRESSURE"
        note    = "Limited reclaimable memory; monitor kswapd activity"
    elif avail_pct > 5:
        verdict = "HIGH PRESSURE"
        note    = "Direct reclaim likely; allocations will stall"
    else:
        verdict = "CRITICAL"
        note    = "OOM killer risk; add RAM or reduce workload"

    fmt_kv("MemAvailable %",    f"{avail_pct:.1f}%",
           f"{mem_available} kB of {mem_total} kB")
    fmt_kv("Reclaimable cache", f"{cache_pct:.1f}%",
           "Cached + Buffers + SReclaimable")
    fmt_kv("Verdict",           verdict, note)

    concept(
        "MemFree is nearly useless as a 'free memory' indicator. Linux "
        "aggressively uses spare RAM as a page cache (Cached) — it is much "
        "faster to serve a file read from RAM than from disk. When a process "
        "needs memory, the kernel evicts cold cache pages. MemAvailable "
        "accounts for this reclaim potential: it is the kernel's estimate of "
        "how much RAM could be made available without swapping. A system with "
        "MemFree=100 MB but Cached=4 GB is healthy; a system with "
        "MemAvailable=50 MB and SwapFree=0 is about to invoke the OOM killer."
    )
