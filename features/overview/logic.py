def fetch(pid):
    try:
        raw = {}
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if ":" in line:
                    k, v = line.split(":", 1)
                    raw[k.strip()] = v.strip()
    except FileNotFoundError:
        return {"error": f"[error] /proc/{pid}/status not found — process may have exited"}
    except PermissionError:
        return {"error": f"[error] permission denied reading /proc/{pid}/status"}

    return {
        "error": None,
        "pid":   pid,
        "fields": {
            "VmPeak": raw.get("VmPeak", "n/a"),
            "VmSize": raw.get("VmSize", "n/a"),
            "VmRSS":  raw.get("VmRSS",  "n/a"),
            "VmSwap": raw.get("VmSwap", "n/a"),
            "VmStk":  raw.get("VmStk",  "n/a"),
            "VmData": raw.get("VmData", "n/a"),
            "VmLib":  raw.get("VmLib",  "n/a"),
            "VmPTE":  raw.get("VmPTE",  "n/a"),
        },
    }
