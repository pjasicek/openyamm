#!/usr/bin/env python3
"""
Every MM9 door plays its own MM9 sounds, and only those (DUNGEON_PLAYBOOK.md "Door sounds"): a check over the built
scenes of every mm9r_* project.

    python3 level_generation/projects/mm9r_common/door_sound_check.py            # the review roots
    python3 level_generation/projects/mm9r_common/door_sound_check.py --assets assets_dev

For each scene door: it has a `sounds` block (a door without one plays MM6-MM8's environment door loop); a mover's first
part carries exactly the sounds its DAT object names (movers.door_sounds), its invisible and glass parts an empty block;
every named sound exists in the MM9 world's audio. A door whose overrides.yml rule names `sounds` carries exactly those. Exits 1 on any failure; prints a line per map.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dungeon.movers import door_sounds  # noqa: E402

PROJECTS = ROOT / "level_generation/projects"
RAW = ROOT / "assets_editor_dev/worlds/mm9/maps"
ISLE_ROOT = ROOT / "output/mm9_rework/isleofashes_blv_root"
REVIEW_ROOT = ROOT / "output/mm9_rework/assets_dev"
SOUND_PROPERTIES = ("OpenSoundName", "CloseSoundName", "OpenStartSound", "OpenBusySound", "OpenStopSound",
                    "CloseStartSound", "CloseBusySound", "CloseStopSound", "JiggleSound")


def dat_properties(stem: str) -> dict[str, dict]:
    """The sound properties of every named DAT object of a map (the old import's raw_objects.yml)."""
    path = RAW / f"{stem}.raw_objects.yml"
    objects, current, name = {}, None, None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("  - object_index"):
            current, name = {}, None
            continue
        if current is None:
            continue
        match = re.match(r'\s+- name: "(.*)"$', line)
        if match:
            name = match.group(1)
            continue
        match = re.match(r"\s+value_json: (.*)$", line)
        if match and name is not None:
            if name == "Name" or name in SOUND_PROPERTIES:
                value = json.loads(json.loads(match.group(1)))
                if name == "Name":
                    objects.setdefault(value, current)
                else:
                    current[name] = value
            name = None
    return objects


def audio_names(assets: Path) -> set[str]:
    audio = assets / "worlds/mm9/audio"
    return {path.relative_to(audio).as_posix().lower() for path in audio.rglob("*.wav")}


def check(project: Path, assets: Path, sounds_on_disk: set[str], totals: Counter) -> list[str]:
    overrides = yaml.safe_load((project / "overrides.yml").read_text())
    stem = overrides["map"]["stem"]
    doors_file = project / "work/doors.json"
    if not doors_file.exists():
        return [f"{project.name}: no work/doors.json (not built)"]
    # the outdoor regions rebuilt as BLVs (mm9r_*_blv) build into their own review root
    root = ISLE_ROOT if project.name.endswith("_blv") and assets == REVIEW_ROOT else assets
    scene_path = root / f"worlds/mm9/maps/{stem}.scene.yml"
    if not scene_path.exists():
        return [f"{project.name}: no scene {scene_path}"]
    scene = yaml.safe_load(scene_path.read_text())
    doors = {door["door_id"]: door for door in (scene.get("initial_state") or {}).get("doors") or []}
    movers = json.loads(doors_file.read_text())
    dat = dat_properties(stem) if (RAW / f"{stem}.raw_objects.yml").exists() else {}
    failures, counts = [], Counter()
    first_parts = {}
    for mover in movers:
        # a mover's parts follow its first one with consecutive ids: the first names the DAT object
        key = (mover["node"].removesuffix("_INV").split("_GLASS")[0])
        first_parts.setdefault(key, mover["door_id"])
    for mover in movers:
        door = doors.get(mover["door_id"])
        label = f"{project.name}: door {mover['door_id']} {mover['node']}"
        if door is None:
            failures.append(f"{label}: not in the scene")
            continue
        block = door.get("sounds")
        counts["doors"] += 1
        if block is None:
            spinner = (mover.get("mover") or {}).get("spin") is not None
            if not spinner:
                failures.append(f"{label}: no sounds block (MM6-MM8's environment door loop plays)")
            counts["spinners" if spinner else "missing"] += 1
            continue
        first = first_parts[mover["node"].removesuffix("_INV").split("_GLASS")[0]] == mover["door_id"]
        model = (mover.get("dat_models") or [None])[0]
        if first and mover.get("sounds_overridden"):
            # overrides.yml gives this door its own sounds (movers.mover_sounds)
            if block != mover["sounds"]:
                failures.append(f"{label}: sounds {block} but overrides.yml names {mover['sounds']}")
            counts["overridden"] += 1
        elif first and model in dat:
            expected = door_sounds(dat[model])
            if block != expected:
                failures.append(f"{label}: sounds {block} but its DAT object {model} names {expected}")
        elif not first and block:
            failures.append(f"{label}: a second part with sounds {block} (they would play twice)")
        counts["with_sounds" if block else "silent"] += 1
        for name in block.values():
            if isinstance(name, str) and name.lower() not in sounds_on_disk:
                failures.append(f"{label}: sound {name} is not in worlds/mm9/audio")
    totals.update(counts)
    print(f"{project.name:28s} {stem:22s} doors {counts['doors']:4d}  sounding {counts['with_sounds']:4d}  "
          f"silent {counts['silent']:4d}  missing {counts['missing']:3d}  spinners {counts['spinners']:2d}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--assets", type=Path, default=REVIEW_ROOT, help="asset root whose MM9 scenes are checked")
    args = parser.parse_args()
    assets = args.assets if args.assets.is_absolute() else ROOT / args.assets
    sounds_on_disk = audio_names(ROOT / "assets_dev")
    failures, totals = [], Counter()
    for project in sorted(PROJECTS.glob("mm9r_*")):
        if (project / "overrides.yml").exists() and (project / "convert.py").exists():
            failures += check(project, assets, sounds_on_disk, totals)
    print(f"total: {dict(totals)}")
    for failure in failures:
        print("FAIL", failure)
    print(f"{len(failures)} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
