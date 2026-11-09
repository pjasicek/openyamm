#!/usr/bin/env python3
"""Apply a gait rollout package's bindings.yml to the worlds' actors.yml, keeping the file's comments and layout.

    python3 level_generation/creatures/gait_rollout_20261031/apply_bindings.py <package>/bindings.yml [--dry-run]

Each entry names a world, its descriptors, an optional `walking` clip (clips.walking) and `animation` keys to set (a
null value removes the key). A key that exists is rewritten in place; a new one goes after the animation block's
gait keys (stride_length and friends). The result is read back with YAML and compared with the request.
"""
import argparse
import difflib
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[3]
GAIT_KEYS = ("stride_length", "run", "run_stride_length", "sprint", "sprint_stride_length", "gait_rate")


def blocks(lines):
    """descriptor -> (first line, end line) of its actors.yml entry."""
    starts = [i for i, line in enumerate(lines) if line.startswith("- descriptor:")]
    result = {}
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(lines)
        name = yaml.safe_load(lines[start][2:])["descriptor"]
        result[name] = (start, end)
    return result


def expand_flow(lines, start, end, name):
    """Rewrite a one-line `  name: {...}` mapping of an entry as a block, so its keys can be edited by line; returns
    the number of lines added."""
    for i in range(start, end):
        if lines[i].startswith(f"  {name}: {{"):
            last = i
            while "\n".join(lines[i:last + 1]).count("{") > "\n".join(lines[i:last + 1]).count("}"):
                last += 1
            mapping = yaml.safe_load("\n".join(line.strip() for line in lines[i:last + 1]))[name]
            lines[i:last + 1] = [f"  {name}:"] + [f"    {key}: {format_value(value)}" for key, value in mapping.items()]
            return len(mapping) - (last - i)
    return 0


def section(lines, start, end, name):
    """(line of `  name:`, end of its block) inside an entry, or None."""
    end += expand_flow(lines, start, end, name)
    for i in range(start, end):
        if lines[i].rstrip() == f"  {name}:":
            stop = i + 1
            while stop < end and (lines[stop].startswith("    ") or not lines[stop].strip()):
                stop += 1
            return i, stop
    return None


def format_value(value):
    return yaml.safe_dump(value, default_flow_style=True).strip().removesuffix("...").strip()


def apply_entry(lines, entry):
    for descriptor in entry["descriptors"]:
        where = blocks(lines).get(descriptor)
        if where is None:
            sys.exit(f"{entry['world']}: no descriptor {descriptor!r}")
        start, end = where
        if "walking" in entry:
            clips = section(lines, start, end, "clips")
            line = next((i for i in range(*clips) if lines[i].strip().startswith("walking:")), None)
            if line is None:
                sys.exit(f"{descriptor}: no clips.walking line")
            lines[line] = f"    walking: {entry['walking']}"
        for key, value in (entry.get("animation") or {}).items():
            start, end = blocks(lines)[descriptor]
            animation = section(lines, start, end, "animation")
            if animation is None:
                sys.exit(f"{descriptor}: no block-style animation section")
            first, stop = animation
            line = next((i for i in range(first + 1, stop) if lines[i].startswith(f"    {key}:")), None)
            if value is None:
                if line is not None:
                    del lines[line]
                continue
            text = f"    {key}: {format_value(value)}"
            if line is not None:
                lines[line] = text
            else:
                after = max((i for i in range(first + 1, stop)
                             if any(lines[i].startswith(f"    {k}:") for k in GAIT_KEYS)), default=first)
                lines.insert(after + 1, text)


def check(path, entry):
    actors = {a["descriptor"]: a for a in yaml.safe_load(path.read_text())["actors"]}
    for descriptor in entry["descriptors"]:
        actor = actors[descriptor]
        if "walking" in entry and actor["clips"]["walking"] != entry["walking"]:
            sys.exit(f"{descriptor}: walking not applied")
        for key, value in (entry.get("animation") or {}).items():
            if actor.get("animation", {}).get(key) != value:
                sys.exit(f"{descriptor}: animation.{key} reads {actor.get('animation', {}).get(key)!r}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("bindings", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    entries = yaml.safe_load(args.bindings.read_text())
    for world in sorted({entry["world"] for entry in entries}):
        path = ROOT / f"assets_dev/worlds/{world}/models/actors.yml"
        text = path.read_text()
        lines = text.split("\n")
        for entry in entries:
            if entry["world"] == world:
                apply_entry(lines, entry)
        result = "\n".join(lines)
        if args.dry_run:
            changed = sum(1 for line in difflib.unified_diff(text.split("\n"), lines, lineterm="", n=0)
                          if line[:1] in "+-" and not line.startswith(("+++", "---")))
            print(f"{world}: {changed} diff lines")
            continue
        path.write_text(result)
        for entry in entries:
            if entry["world"] == world:
                check(path, entry)
        print(f"{world}: applied {sum(len(e['descriptors']) for e in entries if e['world'] == world)} descriptors")


if __name__ == "__main__":
    main()
