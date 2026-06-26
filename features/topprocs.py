import glob

from registry import register
from helpers import section, concept, fmt_kv, fmt_table


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


def _kb_human(kb_val):
    if kb_val >= 1024 * 1024:
        return f"{kb_val / 1024 / 1024:.1f} GB"
    elif kb_val >= 1024:
        return f"{kb_val / 1024:.1f} MB"
    else:
        return f"{kb_val} kB"


@register("topprocs", "Top 15 processes by RSS from /proc/[0-9]*/status")
def feature_topprocs(pid: int) -> None:
    section("Top Processes by Memory Usage", "/proc/[0-9]*/status")

    procs = []
    errors = 0

    for status_path in glob.glob("/proc/[0-9]*/status"):
        try:
            raw = _parse_status(status_path)
            procs.append({
                "pid":  int(raw.get("Pid", "0")),
                "name": raw.get("Name", "?"),
                "rss":  _kb(raw, "VmRSS"),
                "vsz":  _kb(raw, "VmSize"),
                "swap": _kb(raw, "VmSwap"),
            })
        except (FileNotFoundError, PermissionError):
            errors += 1
        except (ValueError, OSError):
            errors += 1

    if not procs:
        print("  [error] no processes found — is this a Linux system with /proc?")
        return

    top = sorted(procs, key=lambda p: p["rss"], reverse=True)[:15]

    print()
    headers = ["PID", "NAME", "VmRSS", "VmSize", "VmSwap"]
    widths  = [6, 16, 10, 10, 9]
    rows = [
        (
            p["pid"],
            p["name"],
            _kb_human(p["rss"]),
            _kb_human(p["vsz"]),
            _kb_human(p["swap"]),
        )
        for p in top
    ]
    fmt_table(headers, rows, widths)

    total_rss = sum(p["rss"] for p in procs)
    print()
    fmt_kv("Processes scanned", len(procs))
    fmt_kv("Total RSS (all)",   _kb_human(total_rss),
           "sum of VmRSS — double-counts shared pages")
    if errors:
        fmt_kv("Scan errors",  errors,
               "processes that exited or were unreadable mid-scan")

    concept(
        "VmRSS (Resident Set Size) is the pages this process currently has "
        "in physical RAM. It includes shared library pages also counted in "
        "other processes, so summing VmRSS across all processes overstates "
        "actual RAM use. A process with high VmSize but low VmRSS has "
        "reserved large virtual address ranges it has not yet touched "
        "(demand paging — pages only land in RAM on first access)."
    )
