from helpers import section, concept, fmt_kv


def render(data):
    if data.get("error"):
        print(f"  {data['error']}")
        return

    section("Memory Pressure Detection",
            "/proc/pressure/memory + /proc/meminfo")

    print()
    print("  -- Pressure Stall Information (PSI) --")

    if not data["psi_available"]:
        print("  [unavailable] /proc/pressure/memory not found")
        print("  (PSI requires Linux 4.20+ with CONFIG_PSI=y)")
    elif data["psi_permission_error"]:
        print("  [error] permission denied reading /proc/pressure/memory")
    else:
        for psi in data["psi_lines"]:
            kind  = psi["kind"]
            label = ("at least one task stalled"
                     if kind == "some" else "ALL tasks stalled")
            print(f"\n  [{kind.upper()}] {label}")
            fmt_kv("avg10",  psi["avg10"],  "% of time stalled over last 10 s")
            fmt_kv("avg60",  psi["avg60"],  "% of time stalled over last 60 s")
            fmt_kv("avg300", psi["avg300"], "% of time stalled over last 300 s")
            fmt_kv("total",  psi["total"],  "cumulative microseconds stalled since boot")

    print()
    print("  -- Heuristic pressure indicators (/proc/meminfo) --")
    print()
    fmt_kv("MemAvailable",   f"{data['mem_available_kb']} kB",
           f"{data['avail_pct']:.1f}% of total RAM")
    fmt_kv("Pressure level", data["pressure_level"], data["pressure_note"])
    fmt_kv("Reclaimable",    f"{data['reclaimable_kb']} kB",
           "Cached + SReclaimable — kernel can free this under pressure")

    print()
    if data["swap_configured"]:
        fmt_kv("SwapUsed",    f"{data['swap_used_kb']} kB",
               f"{data['swap_pct']:.1f}% of swap consumed")
        fmt_kv("Swap status", data["swap_status"], data["swap_status_note"])
    else:
        fmt_kv("SwapTotal",   "0 kB",
               "no swap configured — OOM kill is the only pressure relief valve")

    print()
    print("  -- OOM Proximity --")
    fmt_kv("OOM proximity", data["oom_level"], data["oom_note"])
    print()
    print("  Thresholds: LOW: avail>30%  |  MEDIUM: avail 20-30% (or avail<=30% + swap>80%)")
    print("              HIGH: avail<=10% + swap>90%  |  CRITICAL: avail<=5% + no swap relief")

    print()
    print("  -- Assessment --")
    print()
    marker = {"OK": "OK  ", "WARN": "WARN", "CRIT": "CRIT"}
    for kind, msg in data["signals"]:
        print(f"    [{marker[kind]}] {msg}")
    print()
    print(f"  Conclusion: {data['conclusion']}")
    print()

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
