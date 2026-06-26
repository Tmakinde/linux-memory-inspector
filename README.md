# memory-inspector

A Linux command-line tool that reads kernel memory interfaces under `/proc` and explains the concepts behind each metric. Useful for diagnosing memory pressure, understanding per-process footprints, and learning how the Linux kernel manages RAM.

## Requirements

- Linux (kernel 3.14+ for `MemAvailable`; kernel 4.20+ with `CONFIG_PSI=y` for PSI pressure data)
- Python 3.6+

## Usage

Run from the project root:

```bash
python memory_inspector.py
```

**Options:**

```
--pid PID       PID to inspect for per-process features (default: current process)
--feature NAME  Run a single feature by name
--list          List all available features and exit
```

**Examples:**

```bash
# Run all features for the current process
python memory_inspector.py

# Inspect a specific process
python memory_inspector.py --pid 1234

# Run only the memory pressure feature
python memory_inspector.py --feature pressure

# List available features
python memory_inspector.py --list
```

> Always run from the project root directory. Running feature files directly (e.g. `python features/topprocs.py`) will fail with `ModuleNotFoundError` because Python won't find `registry.py`.

## Features

### `meminfo` — System-wide memory (`/proc/meminfo`)

Displays physical RAM, kernel-managed pages (page cache, slab, swap), and a tiered verdict on whether memory is actually under pressure:

| Verdict | Condition |
|---|---|
| HEALTHY | MemAvailable > 20% |
| HEALTHY (cache-heavy) | Low MemFree but >30% is reclaimable cache |
| MODERATE PRESSURE | MemAvailable 10–20% |
| HIGH PRESSURE | MemAvailable 5–10% |
| CRITICAL | MemAvailable < 5% — OOM kill risk |

### `overview` — Per-process memory (`/proc/<pid>/status`)

Reports the memory footprint of a single process: virtual address space (`VmSize`), resident RAM (`VmRSS`), swap usage (`VmSwap`), stack, heap/data, and page table overhead.

### `pressure` — Memory pressure detection

Combines two data sources:

- **PSI** (`/proc/pressure/memory`): fraction of time tasks were stalled waiting for memory (`some` = at least one task; `full` = all tasks)
- **Heuristic indicators** from `/proc/meminfo`: available memory percentage, swap consumption, and a pressure level (LOW / MEDIUM / HIGH / CRITICAL)

Also includes an **OOM Proximity** section that cross-references available RAM and swap exhaustion to estimate how close the system is to invoking the OOM killer.

### `topprocs` — Top processes by RSS (`/proc/[0-9]*/status`)

Scans all running processes and prints the top 15 by resident set size (VmRSS), along with virtual size (VmSize) and swap usage. Handles processes that exit mid-scan gracefully.

## Project structure

```
memory_inspector.py   entry point — arg parsing, feature dispatch
registry.py           feature registry (@register decorator)
helpers.py            shared output helpers (section, fmt_kv, fmt_table, concept)
features/
  __init__.py         imports all feature modules (triggers self-registration)
  meminfo.py          /proc/meminfo inspector
  overview.py         /proc/<pid>/status inspector
  pressure.py         PSI + meminfo pressure analysis
  topprocs.py         top processes by RSS
```

## Adding a feature

1. Create `features/myfeature.py` with a function decorated with `@register("name", "description")`.
2. Import it in `features/__init__.py`.

```python
# features/myfeature.py
from registry import register
from helpers import section, fmt_kv

@register("myfeature", "One-line description shown in --list")
def feature_myfeature(pid: int) -> None:
    section("My Feature", "/proc/source")
    fmt_kv("some_key", "some_value", "annotation")
```