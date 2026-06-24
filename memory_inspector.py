#!/usr/bin/env python3
"""
memory_inspector.py — Linux memory inspector.
Reads kernel interfaces under /proc and /sys and explains the concepts behind
each metric.
"""

import os
import sys
import argparse
import platform

from registry import FEATURES
import features  # triggers __init__.py → self-registers all features


def main():
    if platform.system() != "Linux":
        print(f"[warning] This tool reads Linux procfs/sysfs. "
              f"Running on {platform.system()} — most features will fail.")
        print("          Tip: run inside a Linux VM or container for real data.\n")

    parser = argparse.ArgumentParser(
        description="Linux memory inspector — reads /proc and /sys, "
                    "explains the kernel concepts."
    )
    parser.add_argument("--pid", type=int, default=os.getpid(),
                        help="PID to inspect (default: this process)")
    parser.add_argument("--feature", metavar="NAME",
                        help="Run a single feature by name (see --list)")
    parser.add_argument("--list", action="store_true",
                        help="List available features and exit")
    args = parser.parse_args()

    if args.list:
        print("Available features (--feature <name>):")
        for name, (desc, _) in FEATURES.items():
            print(f"  {name:<12}  {desc}")
        sys.exit(0)

    if args.feature and args.feature not in FEATURES:
        print(f"[error] Unknown feature '{args.feature}'. "
              f"Use --list to see options.")
        sys.exit(1)

    for name, (desc, fn) in FEATURES.items():
        if args.feature is None or args.feature == name:
            fn(args.pid)

    print()


if __name__ == "__main__":
    main()
