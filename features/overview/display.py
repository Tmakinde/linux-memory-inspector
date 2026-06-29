from helpers import section, concept, fmt_kv

FIELDS = [
    ("VmPeak", "peak virtual memory — highest watermark since process start"),
    ("VmSize", "current virtual address space size — includes unmapped regions"),
    ("VmRSS",  "resident set size — pages actually in physical RAM"),
    ("VmSwap", "pages currently swapped out to disk"),
    ("VmStk",  "stack segment size"),
    ("VmData", "data + BSS segment size (heap lives here)"),
    ("VmLib",  "shared library code size"),
    ("VmPTE",  "page table entries — overhead of mapping virtual→physical"),
]


def render(data):
    if data.get("error"):
        print(f"  {data['error']}")
        return

    section("Process Memory Overview", f"/proc/{data['pid']}/status")

    for key, annotation in FIELDS:
        fmt_kv(key, data["fields"][key], annotation)

    concept(
        "VmSize >> VmRSS because Linux uses demand paging — virtual address "
        "ranges are reserved with mmap() but pages are only faulted into "
        "physical RAM on first access. A 500 MB mmap() costs zero physical "
        "pages until you touch the data. The gap between VmSize and VmRSS "
        "is the 'lazy' portion: allocated but never yet touched. "
        "VmPTE shows the cost of maintaining the virtual-to-physical mapping "
        "itself — each 4 KB page needs an entry in the page table hierarchy."
    )
