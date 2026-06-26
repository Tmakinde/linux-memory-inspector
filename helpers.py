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


def fmt_table(headers, rows, col_widths, indent=2):
    sep = "  "
    ind = " " * indent

    header_cells = []
    for i, (h, w) in enumerate(zip(headers, col_widths)):
        header_cells.append(f"{h:<{w}}" if i <= 1 else f"{h:>{w}}")
    print(ind + sep.join(header_cells))
    print(ind + sep.join("-" * w for w in col_widths))

    for row in rows:
        cells = []
        for i, (val, w) in enumerate(zip(row, col_widths)):
            s = str(val)
            if i == 0:
                cells.append(f"{s:<{w}}")
            elif i == 1:
                cells.append(f"{s[:w]:<{w}}")
            else:
                cells.append(f"{s:>{w}}")
        print(ind + sep.join(cells))
