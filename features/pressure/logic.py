from pathlib import Path


def fetch():
    # --- PSI ---
    psi_path = Path("/proc/pressure/memory")
    psi_available       = False
    psi_permission_error = False
    psi_lines           = []
    psi_full_avg10      = 0.0

    if psi_path.exists():
        psi_available = True
        try:
            for line in psi_path.read_text().strip().splitlines():
                parts = line.split()
                kind  = parts[0]
                kvs   = dict(p.split("=") for p in parts[1:])
                psi_lines.append({
                    "kind":   kind,
                    "avg10":  kvs.get("avg10",  "n/a"),
                    "avg60":  kvs.get("avg60",  "n/a"),
                    "avg300": kvs.get("avg300", "n/a"),
                    "total":  kvs.get("total",  "n/a"),
                })
                if kind == "full":
                    try:
                        psi_full_avg10 = float(kvs.get("avg10", "0"))
                    except ValueError:
                        pass
        except PermissionError:
            psi_permission_error = True

    # --- meminfo ---
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
    swap_total    = kb("SwapTotal")
    swap_free     = kb("SwapFree")
    swap_used     = swap_total - swap_free
    cached        = kb("Cached")
    s_reclaimable = kb("SReclaimable")

    avail_pct       = (mem_available / mem_total * 100) if mem_total else 0
    swap_pct        = (swap_used / swap_total * 100)    if swap_total else 0
    reclaimable_kb  = cached + s_reclaimable
    reclaimable_pct = (reclaimable_kb / mem_total * 100) if mem_total else 0

    # pressure level
    if avail_pct > 20:
        pressure_level = "LOW"
        pressure_note  = "plenty of reclaimable memory"
    elif avail_pct > 10:
        pressure_level = "MEDIUM"
        pressure_note  = "kswapd may wake for background reclaim"
    elif avail_pct > 5:
        pressure_level = "HIGH"
        pressure_note  = "direct reclaim likely — allocations will stall"
    else:
        pressure_level = "CRITICAL"
        pressure_note  = "OOM killer may fire soon"

    # swap status
    swap_configured = swap_total > 0
    if swap_configured:
        if swap_pct > 80 and avail_pct <= 20:
            swap_status      = "WARNING"
            swap_status_note = "heavy swap use with low RAM — active memory pressure"
        elif swap_pct > 80:
            swap_status      = "HIGH USAGE"
            swap_status_note = "many pages swapped out; RAM is healthy — likely cold/inactive pages"
        elif swap_pct > 20:
            swap_status      = "IN USE"
            swap_status_note = "some pages swapped out"
        else:
            swap_status      = "OK"
            swap_status_note = "minimal swap use"
    else:
        swap_status      = ""
        swap_status_note = ""

    # OOM proximity
    if avail_pct <= 5 and (swap_total == 0 or swap_pct > 90):
        oom_level = "CRITICAL"
        oom_note  = "OOM kill imminent — RAM exhausted and no swap relief"
    elif avail_pct <= 5 or (avail_pct <= 10 and swap_total > 0 and swap_pct > 90):
        oom_level = "HIGH"
        oom_note  = "OOM kill possible — RAM critically low and swap nearly exhausted"
    elif avail_pct <= 20 or (avail_pct <= 30 and swap_total > 0 and swap_pct > 80):
        oom_level = "MEDIUM"
        oom_note  = "Memory constrained; kswapd active, watch allocation latency"
    else:
        oom_level = "LOW"
        oom_note  = "System has headroom; OOM kill not imminent"

    # assessment signals
    signals = []

    if avail_pct > 30:
        signals.append(("OK",   f"Plenty of available RAM ({avail_pct:.0f}%)"))
    elif avail_pct > 20:
        signals.append(("WARN", f"Available RAM moderate ({avail_pct:.0f}%) — watch for growth"))
    else:
        signals.append(("CRIT", f"Available RAM low ({avail_pct:.0f}%) — pressure likely"))

    if psi_full_avg10 == 0.0:
        signals.append(("OK",   "No active memory stalls (PSI full avg10 = 0.00)"))
    elif psi_full_avg10 < 1.0:
        signals.append(("WARN", f"Minor stalls detected (PSI full avg10 = {psi_full_avg10:.2f}%)"))
    else:
        signals.append(("CRIT", f"Significant stalls (PSI full avg10 = {psi_full_avg10:.2f}%) — allocations blocked"))

    if reclaimable_pct > 20:
        signals.append(("OK",   f"Large reclaimable cache ({reclaimable_pct:.0f}% of RAM) — kernel has headroom"))
    else:
        signals.append(("WARN", f"Low reclaimable cache ({reclaimable_pct:.0f}%) — less room to maneuver"))

    if swap_configured:
        if swap_pct > 80 and avail_pct <= 20:
            signals.append(("CRIT", f"Swap nearly full ({swap_pct:.0f}%) with low RAM — no relief valve"))
        elif swap_pct > 80:
            signals.append(("WARN", f"Swap heavily used ({swap_pct:.0f}%) — likely cold pages, RAM is still healthy"))
        elif swap_pct > 20:
            signals.append(("WARN", f"Swap in use ({swap_pct:.0f}%)"))
        else:
            signals.append(("OK",   f"Swap usage low ({swap_pct:.0f}%)"))

    crits = sum(1 for k, _ in signals if k == "CRIT")
    warns = sum(1 for k, _ in signals if k == "WARN")
    if crits:
        conclusion = "UNDER PRESSURE — investigate immediately."
    elif warns:
        conclusion = "MOSTLY HEALTHY — one or more indicators warrant monitoring."
    else:
        conclusion = "HEALTHY — no active memory pressure detected."

    return {
        "error":               None,
        "psi_available":       psi_available,
        "psi_permission_error": psi_permission_error,
        "psi_lines":           psi_lines,
        "psi_full_avg10":      psi_full_avg10,
        "mem_total_kb":        mem_total,
        "mem_available_kb":    mem_available,
        "swap_total_kb":       swap_total,
        "swap_used_kb":        swap_used,
        "reclaimable_kb":      reclaimable_kb,
        "avail_pct":           avail_pct,
        "swap_pct":            swap_pct,
        "reclaimable_pct":     reclaimable_pct,
        "pressure_level":      pressure_level,
        "pressure_note":       pressure_note,
        "swap_configured":     swap_configured,
        "swap_status":         swap_status,
        "swap_status_note":    swap_status_note,
        "oom_level":           oom_level,
        "oom_note":            oom_note,
        "signals":             signals,
        "conclusion":          conclusion,
    }
