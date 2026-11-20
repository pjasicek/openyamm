#!/usr/bin/env python3
"""Before/after table of two hue_vs_lightmaps.py outputs (the re-light of 2026-10-31): per zone MM9's lightmap luma, our
luma before and after, the ratios ours/MM9, and B/R, G/R of MM9 and after. Markdown on stdout.

    python3 level_generation/projects/mm9r_common/relight_table.py hue_before.txt hue_after.txt
"""
import sys

LUMA = (0.2126, 0.7152, 0.0722)


def read(path):
    rows = {}
    for line in open(path):
        parts = line.split()
        if len(parts) > 8 and parts[1] in ("MM9", "ours"):
            try:
                r, g, b = (float(v) for v in parts[2:5])
            except ValueError:
                continue
            rows.setdefault(parts[0], {})[parts[1]] = (r, g, b)
    return rows


def luma(rgb):
    return sum(c * w for c, w in zip(rgb, LUMA))


def main() -> int:
    before, after = read(sys.argv[1]), read(sys.argv[2])
    print("| Zone | MM9 luma | before | after | ratio before -> after | B/R MM9 / after | G/R MM9 / after |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    for zone, values in after.items():
        mm9, new = values.get("MM9"), values.get("ours")
        old = before.get(zone, {}).get("ours")
        if not mm9 or not new:
            continue
        lm = luma(mm9)
        old_text = f"{luma(old):.3f}" if old else "-"
        old_ratio = f"{luma(old) / lm:.2f}" if old else "-"
        print(f"| {zone} | {lm:.3f} | {old_text} | {luma(new):.3f} | {old_ratio} -> **{luma(new) / lm:.2f}** | "
              f"{mm9[2] / mm9[0]:.2f} / {new[2] / new[0]:.2f} | {mm9[1] / mm9[0]:.2f} / {new[1] / new[0]:.2f} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
