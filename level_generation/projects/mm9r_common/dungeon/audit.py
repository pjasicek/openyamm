"""
The walkability audit of a built dungeon: the shared check (level_generation/projects/hesper_stage/
check_walkability.py: steps, flights, unreachable regions, pits, movers, actors) on work/runtime/<map>.blv and its
scene, with the MM9 world's monster table for the flyers; findings in work/walkability.json. Every step and flight
it lists must be explained in the map's README (MM9 stairs too steep for the party, door frame lips, ...).

Water (a scene with `water_volumes`, overrides.yml `map: {swim: true}`, dungeon/water.py): the shared check measures
floors for monsters, which walk a bed; the party swims. Every floor region with floor inside a volume (under its top:
a bed, a ledge, the foot of a ramp) or beside it at most SURFACE_JUMP_REACH over the top (a rim the surface jump
climbs onto) is one swim set the party moves through freely. From it the party walks and drops as monsters do and climbs up to
PARTY_STEP (50: the monsters' graph stops at 40); when that reaches the party start's region the party gets out, and
a pit or unreachable finding in the set is marked `water` (the party swims out; not a fault for it, still one for
walking monsters, as in MM9). walkability.json gets a `water` record per volume: its regions, whether the party gets
out, and its rims out of the surface jump's reach.

    python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_<map>
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dungeon.source import ROOT, Project  # noqa: E402

# From the surface pose (the eye point 1 over the surface, the feet 134 under it) the surface jump (704 up, gravity
# 1280) lifts the feet about 193: 59 over the surface (devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md §2).
SURFACE_JUMP_REACH = 59.0
REACH = 40.0                # a floor this far past a volume's outline is beside it (about a party radius)


def _inside(x: float, y: float, ring: np.ndarray) -> bool:
    hit = False
    for (x1, y1), (x2, y2) in zip(ring, np.roll(ring, -1, axis=0)):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def _distance_outside(x: float, y: float, ring: np.ndarray) -> float:
    if _inside(x, y, ring):
        return 0.0
    best = math.inf
    for a, b in zip(ring, np.roll(ring, -1, axis=0)):
        ab = b - a
        t = np.clip(((x - a[0]) * ab[0] + (y - a[1]) * ab[1]) / max(ab @ ab, 1e-9), 0.0, 1.0)
        best = min(best, math.hypot(x - a[0] - t * ab[0], y - a[1] - t * ab[1]))
    return best


def party_climbs(walk, level, graph) -> dict:
    """Region -> the regions the party climbs onto from it: neighbouring floors MONSTER_STEP to PARTY_STEP higher (the
    monsters' graph has these as drops only), with no wall between."""
    climbs = {}
    for (i, j), ids in graph.nodes.items():
        for other in ((i + 1, j), (i, j + 1), (i - 1, j), (i, j - 1)):
            for m in graph.nodes.get(other, ()):
                for n in ids:
                    dz = graph.z[m] - graph.z[n]
                    if not walk.MONSTER_STEP < dz <= walk.PARTY_STEP or graph.region[m] == graph.region[n]:
                        continue
                    if (i, j) in level.wall_cells or other in level.wall_cells:
                        if level.blocked(*walk.centre_of((i, j)), *walk.centre_of(other), graph.z[m] + walk.BODY):
                            continue
                    climbs.setdefault(graph.region[n], set()).add(graph.region[m])
    return climbs


def party_reach(walk, level, graph, swim: set, cache: dict = {}) -> set:
    """The regions the party reaches from a swim set: it swims between them, walks and drops as monsters do and climbs
    up to PARTY_STEP."""
    key = id(graph)
    if cache.get("key") != key:
        cache.update(key=key, climbs=party_climbs(walk, level, graph))
    climbs = cache["climbs"]
    seen, queue = set(swim), list(swim)
    while queue:
        region = queue.pop()
        for nxt in graph.down.get(region, set()) | climbs.get(region, set()):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen


def water_audit(walk, blv: Path, json_path: Path) -> dict | None:
    scene = json.loads(blv.with_suffix(".scene.yml").read_text())
    volumes = scene.get("water_volumes") or []
    if not volumes:
        return None
    level = walk.load(blv)
    findings, graph = walk.analyse(level, [])
    start = graph.node_near(*level.start, tolerance=48)
    main = graph.region[start]
    records, sets = {}, {}
    for volume in volumes:
        regions, rims = set(), {}
        for n, z in enumerate(graph.z):
            x, y = walk.centre_of(graph.cell[n])
            for piece in volume["pieces"]:
                ring = np.array(piece["polygon"], float)
                lo, hi = ring.min(0) - REACH, ring.max(0) + REACH
                if not (lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1]):
                    continue
                if piece["bottom"] - 1.0 <= z < piece["top"] and _inside(x, y, ring):
                    regions.add(graph.region[n])
                elif piece["top"] <= z and _distance_outside(x, y, ring) <= REACH:
                    over = z - piece["top"]
                    if over <= SURFACE_JUMP_REACH:
                        regions.add(graph.region[n])
                    elif over < walk.WALL * 2:
                        rims[graph.region[n]] = min(rims.get(graph.region[n], math.inf), over)
        sets[volume["id"]] = (regions, rims)
    # Volumes that share a floor region are one water (the crevasse's BlueWater0 and BlueWater1 over one bed)
    for volume_id, (regions, rims) in sets.items():
        joined = set(regions)
        grown = True
        while grown:
            grown = False
            for other, (other_regions, _) in sets.items():
                if other_regions & joined and not other_regions <= joined:
                    joined |= other_regions
                    grown = True
        party_out = main in party_reach(walk, level, graph, joined) if joined else False
        record = {"regions": len(regions), "party_gets_out": party_out,
                  "rims_beyond_surface_jump": sorted({round(v) for r, v in rims.items() if r not in joined})}
        records[volume_id] = (record, regions if party_out else set())
    report = json.loads(json_path.read_text())
    marked = 0
    for name, entry in report.items():
        for finding in entry["findings"]:
            if finding["kind"] not in ("pit", "unreachable"):
                continue
            n = graph.node_near(*finding["at"], tolerance=8)
            if n is None:
                continue
            for volume_id, (_, regions) in records.items():
                if graph.region[n] in regions:
                    finding["water"] = f"{volume_id}: the party swims out (monsters walk its bed)"
                    marked += 1
                    break
        entry["water"] = {volume_id: record for volume_id, (record, _) in records.items()}
        entry["water_marked_findings"] = marked
    json_path.write_text(json.dumps(report, indent=1) + "\n")
    print(f"water: {marked} pit/unreachable findings the party swims out of")
    for volume_id, (record, _) in records.items():
        print(f"  {volume_id}: {record['regions']} floor regions, the party gets out: {record['party_gets_out']}, "
              f"rims beyond the surface jump ({SURFACE_JUMP_REACH:.0f}): {record['rims_beyond_surface_jump']}")
    return records


def run(project, workers: int = 1) -> None:
    sys.path.insert(0, str(ROOT / "level_generation/projects/hesper_stage"))
    import check_walkability as walk
    walk.MONSTER_TABLES = [ROOT / "assets_dev/worlds/mm9/data_tables/monster_data.txt"] + list(walk.MONSTER_TABLES)
    blv = project.work / "runtime" / project.map
    json_path = project.work / "walkability.json"
    walk.audit([blv], {"__none__"}, json_path, workers=workers)
    water_audit(walk, blv, json_path)


if __name__ == "__main__":
    run(Project.load(Path(sys.argv[1])))
