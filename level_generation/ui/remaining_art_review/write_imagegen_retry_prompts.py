#!/usr/bin/env python3
"""Freeze strict retry prompts for regularly packed held UI sprites."""

import json
from pathlib import Path


RUN = Path(__file__).resolve().parent / "imagegen_regen"


def prompt(sheet: dict) -> str:
    count = len(sheet["cells"])
    name = sheet["id"]
    if "inventory" in name:
        subject = "inventory objects"
        details = ("Restore the exact object identity, silhouette, pose, material, colors, holes, and any original "
                   "lettering or distinctive marks. Preserve small and partial objects as they are.")
    elif "effects" in name:
        subject = "UI animation and spell-effect frames"
        details = ("Restore each original state, including faint fragments and intentional gaps. Keep each symbol, "
                   "spark, glow and animation order; do not fill the transparent holes or add unrelated effects.")
    else:
        subject = "opaque UI controls and panels"
        details = ("Restore the original straight borders, precise symbols, lettering, lengths, widths, colors "
                   "and distinct control states. Do not add ornament or extend any strip beyond its slot.")
    alpha = "True transparent RGBA outside the art" if sheet["role"] == "alpha" else "Pure magenta in gutters"
    return f"""Use case: precise-object-edit
Asset type: high-resolution Might and Magic {subject}, {count} separate source cells in a regular grid.
Input image: attached sheet contains the original native artwork. The magenta areas are temporary separators only.
Primary request: genuinely repaint each source cell at more than 2× resolution with continuous smooth painted contours and faithful fine detail. {details}
Layout: keep all {count} independent cells in exactly the same positions, order, sizes and rectangular slots. Each restored subject must retain its exact relative scale and center within its own slot. Leave generous empty gutters, no overlapping or neighboring-cell content. Preserve original full canvas and partial edges rather than trimming.
Background: {alpha}; no residual magenta, red/yellow/white fringing, painted checkerboard, new shadows or backing panels.
Constraints: no missing or merged subjects, no changed text, no crop, zoom, recentering, source-pixel mosaic, blur-only upscale, duplicated object or extra decoration."""


def main() -> None:
    plan = json.loads((RUN / "retry_plan.json").read_text())
    folder = RUN / "retry_prompts"
    folder.mkdir(exist_ok=True)
    for sheet in plan["sheets"]:
        (folder / f"{sheet['id']}.txt").write_text(prompt(sheet) + "\n")
    print(f"Wrote {len(plan['sheets'])} retry prompts")


if __name__ == "__main__":
    main()
