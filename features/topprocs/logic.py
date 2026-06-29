import glob


def _parse_status(path):
    raw = {}
    with open(path) as f:
        for line in f:
            if ":" in line:
                k, v = line.split(":", 1)
                raw[k.strip()] = v.strip()
    return raw


def _kb(raw, key):
    val = raw.get(key, "0 kB")
    try:
        return int(val.split()[0])
    except (ValueError, IndexError):
        return 0


def fetch():
    procs  = []
    errors = 0

    for status_path in glob.glob("/proc/[0-9]*/status"):
        try:
            raw = _parse_status(status_path)
            procs.append({
                "pid":     int(raw.get("Pid", "0")),
                "name":    raw.get("Name", "?"),
                "rss_kb":  _kb(raw, "VmRSS"),
                "vsz_kb":  _kb(raw, "VmSize"),
                "swap_kb": _kb(raw, "VmSwap"),
            })
        except (FileNotFoundError, PermissionError):
            errors += 1
        except (ValueError, OSError):
            errors += 1

    if not procs:
        return {"error": "[error] no processes found — is this a Linux system with /proc?"}

    top         = sorted(procs, key=lambda p: p["rss_kb"], reverse=True)[:15]
    total_rss_kb = sum(p["rss_kb"] for p in procs)

    return {
        "error":               None,
        "top":                 top,
        "total_procs_scanned": len(procs),
        "total_rss_kb":        total_rss_kb,
        "errors":              errors,
    }
