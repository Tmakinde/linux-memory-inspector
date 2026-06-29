def fetch():
    try:
        raw = {}
        with open("/proc/meminfo") as f:
            for line in f:
                if ":" in line:
                    k, v = line.split(":", 1)
                    raw[k.strip()] = v.strip()
    except FileNotFoundError:
        return {"error": "[error] /proc/meminfo not found"}

    def kb(key):
        val = raw.get(key, "0 kB")
        return int(val.split()[0]) if val and val != "n/a" else 0

    mem_total     = kb("MemTotal")
    mem_available = kb("MemAvailable") or kb("MemFree")
    used          = mem_total - mem_available

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

    return {
        "error":            None,
        "raw":              raw,
        "mem_total_kb":     mem_total,
        "mem_available_kb": mem_available,
        "used_kb":          used,
        "cache_pct":        cache_pct,
        "avail_pct":        avail_pct,
        "verdict":          verdict,
        "verdict_note":     note,
    }
