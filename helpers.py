import shutil
import textwrap


def section(title, source):
    width = min(shutil.get_terminal_size((80, 24)).columns, 80)
    print()
    print("=" * width)
    print(f"  {title}")
    print(f"  source: {source}")
    print("=" * width)


def concept(text):
    width = min(shutil.get_terminal_size((80, 24)).columns, 80)
    print()
    wrapped = textwrap.fill("CONCEPT: " + text, width=width,
                            subsequent_indent="         ")
    print(wrapped)
    print()


def fmt_kv(key, value, annotation=""):
    ann = f"  [{annotation}]" if annotation else ""
    print(f"  {key:<22} {str(value):>14}{ann}")
