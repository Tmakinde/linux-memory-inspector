from pathlib import Path

from registry import register
from helpers import section, concept, fmt_kv


@register("pressure", "Memory pressure via PSI (/proc/pressure/memory) + meminfo heuristics")
def feature_pressure(pid: int) -> None:
    section("Memory Pressure Detection",
            "/proc/pressure/memory + /proc/meminfo")

    # --- PSI (Pressure Stall Information) ---
    print()
    print("  -- Pressure Stall Information (PSI) --")

    psi_path = Path("/proc/pressure/memory")
    if psi_path.exists():
        try:
            for line in psi_path.read_text().strip().splitlines():
                parts = line.split()
                kind = parts[0]  # "some" or "full"
                kvs = dict(p.split("=") for p in parts[1:])
                label = ("at least one task stalled"
                         if kind == "some" else "ALL tasks stalled")
                print(f"\n  [{kind.upper()}] {label}")
                fmt_kv("avg10",  kvs.get("avg10", "n/a"),
                       "% of time stalled over last 10 s")
                fmt_kv("avg60",  kvs.get("avg60", "n/a"),
                       "% of time stalled over last 60 s")
                fmt_kv("avg300", kvs.get("avg300", "n/a"),
                       "% of time stalled over last 300 s")
                fmt_kv("total",  kvs.get("total", "n/a"),
                       "cumulative microseconds stalled since boot")
        except PermissionError:
            print("  [error] permission denied reading /proc/pressure/memory")
    else:
        print("  [unavailable] /proc/pressure/memory not found")
        print("  (PSI requires Linux 4.20+ with CONFIG_PSI=y)")

    # --- Heuristic pressure indicators from /proc/meminfo ---
    print()
    print("  -- Heuristic pressure indicators (/proc/meminfo) --")

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
    swap_total    = kb("SwapTotal")
    swap_free     = kb("SwapFree")
    swap_used     = swap_total - swap_free
    cached        = kb("Cached")
    s_reclaimable = kb("SReclaimable")

    avail_pct = (mem_available / mem_total * 100) if mem_total else 0
    swap_pct  = (swap_used / swap_total * 100) if swap_total else 0

    def pressure_level(pct):
        if pct > 20:
            return "OK",       "plenty of reclaimable memory"
        elif pct > 10:
            return "MODERATE", "kswapd may wake for background reclaim"
        elif pct > 5:
            return "HIGH",     "direct reclaim likely — allocations will stall"
        else:
            return "CRITICAL", "OOM killer may fire soon"

    level, note = pressure_level(avail_pct)

    print()
    fmt_kv("MemAvailable",   f"{mem_available} kB",
           f"{avail_pct:.1f}% of total RAM")
    fmt_kv("Pressure level", level, note)
    fmt_kv("Reclaimable",    f"{cached + s_reclaimable} kB",
           "Cached + SReclaimable — kernel can free this under pressure")

    print()
    if swap_total > 0:
        fmt_kv("SwapUsed",    f"{swap_used} kB",
               f"{swap_pct:.1f}% of swap consumed")
        if swap_pct > 80:
            fmt_kv("Swap status", "WARNING",
                   "heavy swap use — system is memory-constrained")
        elif swap_pct > 20:
            fmt_kv("Swap status", "IN USE", "some pages swapped out")
        else:
            fmt_kv("Swap status", "OK", "minimal swap use")
    else:
        fmt_kv("SwapTotal",   "0 kB",
               "no swap configured — OOM kill is the only pressure relief valve")

    concept(
        "Memory pressure escalates through three stages in the Linux kernel. "
        "(1) Background reclaim: when MemAvailable drops below ~20%, kswapd "
        "wakes and quietly reclaims cold page-cache pages — no process is "
        "stalled. (2) Direct reclaim: when a memory allocation cannot find a "
        "free page, the allocating process itself walks the LRU and reclaims "
        "pages synchronously — this adds latency directly to your code. "
        "(3) OOM kill: when reclaim fails repeatedly, the kernel picks and "
        "kills a process using the OOM scoring algorithm. "
        "PSI (Pressure Stall Information, added in Linux 4.20) measures the "
        "fraction of time tasks spent waiting for memory. 'some' > 0 means at "
        "least one task stalled; 'full' > 0 means ALL runnable tasks stalled "
        "— the system was completely head-of-line blocked on memory."
    )
