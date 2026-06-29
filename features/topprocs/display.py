from helpers import section, concept, fmt_kv, fmt_table


def _kb_human(kb_val):
    if kb_val >= 1024 * 1024:
        return f"{kb_val / 1024 / 1024:.1f} GB"
    elif kb_val >= 1024:
        return f"{kb_val / 1024:.1f} MB"
    else:
        return f"{kb_val} kB"


def render(data):
    if data.get("error"):
        print(f"  {data['error']}")
        return

    section("Top Processes by Memory Usage", "/proc/[0-9]*/status")

    print()
    headers = ["PID", "NAME", "VmRSS", "VmSize", "VmSwap"]
    widths  = [6, 16, 10, 10, 9]
    rows = [
        (
            p["pid"],
            p["name"],
            _kb_human(p["rss_kb"]),
            _kb_human(p["vsz_kb"]),
            _kb_human(p["swap_kb"]),
        )
        for p in data["top"]
    ]
    fmt_table(headers, rows, widths)

    print()
    fmt_kv("Processes scanned", data["total_procs_scanned"])
    fmt_kv("Total RSS (all)",   _kb_human(data["total_rss_kb"]),
           "sum of VmRSS — double-counts shared pages")
    if data["errors"]:
        fmt_kv("Scan errors",  data["errors"],
               "processes that exited or were unreadable mid-scan")

    concept(
        "VmRSS (Resident Set Size) is the pages this process currently has "
        "in physical RAM. It includes shared library pages also counted in "
        "other processes, so summing VmRSS across all processes overstates "
        "actual RAM use. A process with high VmSize but low VmRSS has "
        "reserved large virtual address ranges it has not yet touched "
        "(demand paging — pages only land in RAM on first access)."
    )
