#!/usr/bin/env python3
"""
A dry run of the converter's pack growth (dungeon/density.py) on installed maps: where the copies would go and how
many fit, from the installed scene, BLV and map Lua (assets_dev/worlds/mm9/maps/<stem>.scene.yml and .blv,
events/maps/<stem>.lua) with the members' anchors from the project's work/content.json (the baseline conversion, as
density_anchors.py reads it). Nothing is converted or installed.

    python3 level_generation/projects/mm9r_common/density_dry_check.py bathhouse 1000terrors sturmford templeofhonk
    python3 level_generation/projects/mm9r_common/density_dry_check.py --all --out /tmp/density_dry.json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import yaml

COMMON = Path(__file__).resolve().parent
sys.path.insert(0, str(COMMON))
import dungeon  # noqa: E402
from dungeon import density  # noqa: E402
from dungeon.source import ROOT, Project, Source  # noqa: E402

sys.path.insert(0, str(ROOT))
from util.map_export import parse_blv_file  # noqa: E402

MAPS = ROOT / "assets_dev/worlds/mm9/maps"
EVENTS = ROOT / "assets_dev/worlds/mm9/events/maps"


def project_hooks(project: Path):
    """The project's Hooks class (its convert.py, imported, not run) when it sets density_lua_directories (each
    city's convert.py imports its own citylua: not two in one process)."""
    if "density_lua_directories" not in (project / "convert.py").read_text():
        return dungeon.Hooks
    spec = importlib.util.spec_from_file_location(f"convert_{project.name}", project / "convert.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    classes = [v for v in vars(module).values()
               if isinstance(v, type) and issubclass(v, dungeon.Hooks) and v.__module__ == module.__name__]
    return classes[0] if classes else dungeon.Hooks


def check(stem: str, entry: dict) -> dict:
    project = ROOT / "level_generation/projects" / entry["project"]
    scene = yaml.load((MAPS / f"{stem}.scene.yml").read_text(), Loader=yaml.CSafeLoader)
    actors = scene["initial_state"]["actors"]
    content = json.loads((project / "work/content.json").read_text())["actors"]
    report_actors = [a for a in content if "copy_of" not in a]
    if len(report_actors) > len(actors) or any(a["actor_index"] != s["actor_index"] or a["monster_id"] != s["monster_id"]
                                                for a, s in zip(report_actors, actors)):
        raise SystemExit(f"{stem}: work/content.json does not match the installed scene")
    anchors = {a["anchor"]: a["actor_index"] for a in report_actors}
    overrides = yaml.safe_load((project / "overrides.yml").read_text())
    if not (overrides.get("map") or {}).get("density", True):
        _, result = density.grow(stem, actors, {}, [], None, set(), density.counted_today(stem))
        return dict(result, note="growth off")
    world = density.World(parse_blv_file(MAPS / f"{stem}.blv")["payload"], scene, density.liquid_textures())
    directories = density.lua_name_tables(project_hooks(project))
    lua = (EVENTS / f"{stem}.lua").read_text()
    cinematics = MAPS / f"{stem}.cinematics.yml"
    references = density.References.of(
        Source(Project.load(project, install=False)), lua, directories,
        yaml.load(cinematics.read_text(), Loader=yaml.CSafeLoader) if cinematics.is_file() else None)
    _, result = density.grow(stem, actors, anchors, density.map_packs(stem), world,
                             density.lua_actor_indices(lua, directories), density.counted_today(stem), references)
    # the sector rule reads the BLV floor's room as the scene's sector_id: members whose own floor disagrees
    mismatched = 0
    for pack in density.map_packs(stem):
        for anchor in pack["members"]:
            member = actors[anchors[anchor]]
            p = member["position"]
            _, record = world.floor(p["x"], p["y"], p["z"] + 1)
            mismatched += record is not None and record["sector"] != member["sector_id"]
    result["members_sector_mismatch"] = mismatched
    result["skipped_reasons"] = dict(Counter(r for pack in result["packs"] for r in pack["skipped"].values()))
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stems", nargs="*")
    parser.add_argument("--all", action="store_true", help="every map of density_anchors.json")
    parser.add_argument("--out", type=Path, help="write the per-pack results here (JSON)")
    arguments = parser.parse_args(argv)
    maps = json.loads(density.ANCHORS.read_text())["maps"]
    stems = list(maps) if arguments.all else arguments.stems
    results, totals = {}, Counter()
    for stem in stems:
        if stem not in maps:
            raise SystemExit(f"{stem}: not in {density.ANCHORS.name}")
        result = check(stem, maps[stem])
        results[stem] = result
        s = result["summary"]
        totals.update({k: s.get(k, 0) for k in ("target_total", "placed_total", "wanted_adds", "placed_adds",
                                               "moved_adds", "unplaced_adds")})
        print(f"{stem:22} total {s.get('placed_total', 0):4} of {s.get('target_total', 0):4}  adds {s['placed_adds']:4} "
              f"of {s['wanted_adds']:4} (moved {s['moved_adds']:3}, unplaced {s['unplaced_adds']:3} "
              f"{s['unplaced_reasons']})  skipped members {result.get('skipped_reasons', {})}  "
              f"sector mismatches {result.get('members_sector_mismatch', 0)}")
    print(f"{'all':22} total {totals['placed_total']:4} of {totals['target_total']:4}  adds {totals['placed_adds']:4} of "
          f"{totals['wanted_adds']:4} (moved {totals['moved_adds']}, unplaced {totals['unplaced_adds']})")
    if arguments.out:
        arguments.out.write_text(json.dumps(results, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
