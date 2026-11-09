"""
Ground treasure (devdocs/mm9_rework/GROUND_TREASURE_PLAN.md): MM6-MM8 treasure markers, type-2 spawns that roll a
random item of their level on the map's first visit and after a refill, placed on every converted map listed in
tools/mm9_import_discovery/mm9_ground_treasure.py COUNTS. build.py runs it after pack growth on the written scene and
writes the markers into the scene's `spawns`, so every reconversion places them again; nothing is hand-edited.

How many and what they roll come from mm9_ground_treasure (bonus, main and lower classes from the map's chest tiers).
Where, on the compiled BLV:
- Candidate spots every SAMPLE units on the floor the party reaches from its starts and from where its mobile hostile
  monsters and its chests stand (teleporters and scripted ways the graph cannot follow) (hesper_stage/
  check_walkability's graph: walking, drops, the party's 50-unit climbs and the scene's ladders; never through
  water), with room above
  them, clear of walls, doors and movers along their travel, event faces, ladders, water, starts, chests and actors
  (density.World's tests).
- Depth: the distance from the main start over the BLV's sector graph (portal to portal) and then in plan. The main
  route is the sector path from the main start to every other start (the arrivals beside the exits); spots within
  ROUTE_CLEAR of it are out.
- Secrets: movers whose DAT names read as secret (SECRET_MOVER), breakable walls (destructibles other than
  DestructableProp barrels and crates), PerceptionBrush hint faces and the
  overrides' `bonus_near` names; a spot within SECRET_REACH of one and deeper than it is behind it. Bosses: hostile
  actors flagged boss (mm9_ai, density.BOSS_MONSTER_IDS) or with a unique name, and `bonus_near` actors.
- Scores: guarded (a hostile actor within GUARD_REACH), dead-end sector (one portal neighbour), themed (overrides'
  `themed_near`), secret or boss, depth. Bonus markers only behind secrets or by bosses; lower markers prefer the
  shallow half of the map.
- Shape: the first anchors (about 13% of the count) grow a stash of 2-3 within STASH_REACH, so about a third of the
  markers lie in stashes; an anchor's score drops by SPREAD per marker already in its sector (the regions: within
  REGION_SPREAD_REACH), so markers spread over the map; stashes stand STASH_GAP apart; a sector
  holds at most ROOM_CAP (BONUS_ROOM_CAP behind a secret or by a boss, CHEST_ROOM_CAP where a chest stands). The
  regions (outdoor BLVs, one open sector) have no sector caps, wider gaps, and keep TOWN_CLEAR from their town and
  dock arrivals.
Deterministic from the map stem: a reconversion of the same map places the same markers.

overrides.yml `treasure` (all optional):
  count: N                         # replaces COUNTS
  bonus_near: [DAT name, ...]      # objects or actors whose surroundings count as secrets/bosses
  themed_near: [DAT name, ...]     # rewarding set dressing (bookcases, coffins, weapon racks)
  avoid_near: [{name: DAT name, radius: R} | {at: [x, y, z], radius: R}, ...]
  place: [{at: [x, y, z], class: bonus|main|lower}, ...]   # hand-picked native spots, counted in the total

Outputs: the scene's `spawns`, work/treasure.json (every marker with its class, tiers, index and reasons; counts,
shortfall, guarded and stash shares) and work/treasure.png (a top-down plan).
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from heapq import heappop, heappush
from pathlib import Path

import numpy as np

from .density import BOSS_MONSTER_IDS, World, liquid_textures
from .source import ROOT

SECRET_MOVER = re.compile(r"secret|hidden|pivot|bookcase|treasure|panel|slide|niche|grave|coffin|crypt", re.I)
TOWN_START = re.compile(r"city|town|dock", re.I)
PERCEPTION_COGS = range(23000, 24000)      # perception.HINT_COG_BASE + DAT index

SAMPLE = 128.0            # candidate spacing
REGION_GRID = 64          # the walk raster on the regions (the dungeons keep check_walkability's 16)
HEAD = 128.0              # room above a spot
WALL_CLEAR = 48.0
ZONE_CLEAR = 32.0
START_CLEAR = 1000.0
TOWN_CLEAR = 3000.0
ROUTE_CLEAR = 256.0
OBJECT_CLEAR = 96.0       # from chests and actors
FRIENDLY_CLEAR = 800.0
SECRET_REACH = 1200.0
BOSS_REACH = 1200.0
GUARD_REACH = 1000.0
THEMED_REACH = 600.0
STASH_REACH = 300.0
STASH_SHARE = 0.13        # stashes per marker: a third of the markers in stashes of 2-3 (MM7: 34% within 300 units)
STASH_MIN_COUNT = 6       # a map of this many markers or more has at least one stash
STASH_GAP = 900.0
REGION_STASH_GAP = 2500.0
MEMBER_GAP = 96.0
ROOM_CAP, BONUS_ROOM_CAP, CHEST_ROOM_CAP = 3, 5, 1
SPREAD = 1.5              # a stash anchor's score drops this much per marker already in its sector
REGION_SPREAD_REACH = 4000.0   # the regions' "sector" for SPREAD: markers within this
HOSTILE = 4


def _walk():
    sys.path.insert(0, str(ROOT / "level_generation/projects/hesper_stage"))
    import check_walkability as walk
    tables = [ROOT / "assets_dev/worlds/mm9/data_tables/monster_data.txt"]
    walk.MONSTER_TABLES = tables + [t for t in walk.MONSTER_TABLES if t not in tables]
    return walk


def _xyz(p) -> tuple[float, float, float]:
    if isinstance(p, dict):
        return float(p["x"]), float(p["y"]), float(p["z"])
    return float(p[0]), float(p[1]), float(p[2])


def _segment_distance(p, a, b) -> float:
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(ax + t * dx - p[0], ay + t * dy - p[1])


class Sectors:
    """The BLV's sector graph: portal centres between sectors, Dijkstra depth from the main start, and the route from
    it to each other start."""

    def __init__(self, blv: dict, vertices: np.ndarray):
        self.links = defaultdict(list)            # sector -> [(other sector, portal centre)]
        for face in blv["faces"]:
            if face["is_portal"] and face["room_number"] != face["room_behind_number"]:
                centre = vertices[face["vertex_indices"]].mean(0)
                a, b = face["room_number"], face["room_behind_number"]
                self.links[a].append((b, centre))
                self.links[b].append((a, centre))
        self.neighbours = {s: {t for t, _ in links} for s, links in self.links.items()}

    def solve(self, start_sector: int, start: tuple) -> None:
        self.distance = {start_sector: 0.0}
        self.entry = {start_sector: np.array(start[:3], float)}
        self.parent = {}
        queue = [(0.0, start_sector)]
        while queue:
            d, s = heappop(queue)
            if d > self.distance.get(s, math.inf):
                continue
            for t, centre in self.links.get(s, ()):
                nd = d + float(np.linalg.norm(self.entry[s][:2] - centre[:2]))
                if nd < self.distance.get(t, math.inf):
                    self.distance[t], self.entry[t], self.parent[t] = nd, centre, s
                    heappush(queue, (nd, t))

    def depth(self, sector: int, point) -> float:
        if sector not in self.distance:
            return math.inf
        return self.distance[sector] + math.hypot(point[0] - self.entry[sector][0], point[1] - self.entry[sector][1])

    def route(self, sector: int, point) -> list:
        """The polyline from `point` back to the main start through the portals."""
        line = [np.array(point[:3], float)]
        while sector in self.parent:
            line.append(self.entry[sector])
            sector = self.parent[sector]
        if sector in self.entry:
            line.append(self.entry[sector])
        return line


def _named_points(build, scene: dict, names) -> list[tuple]:
    """Native points of DAT objects (by Name) or placed actors (by their content-report anchor) named in a hint list."""
    points = []
    anchors = {e.get("anchor", "").lower(): e["actor_index"] for e in build.content.report.get("actors", [])}
    actors = {a["actor_index"]: a for a in scene["initial_state"].get("actors", [])}
    for name in names or ():
        key = str(name).lower()
        if key in anchors and anchors[key] in actors:
            points.append(_xyz(actors[anchors[key]]["position"]))
            continue
        found = build.source.by_name.get(key)
        if found is None or "Pos" not in found["properties"]:
            raise SystemExit(f"treasure: overrides.yml names {name!r}, which is no DAT object or placed actor")
        points.append(tuple(float(v) for v in build.project.native(found["properties"]["Pos"])))
    return points


def _scores(c: dict) -> dict:
    base = 2 * c["dead_end"] + 2 * c["themed"] + (c["secret"] or c["boss"]) + c["jitter"]
    return {"bonus": 3 * c["secret"] + 2 * c["boss"] + c["guarded"] + c["depth_norm"] + c["jitter"],
            "main": base + 3 * c["guarded"] + c["depth_norm"],
            "lower": base + 2 * c["guarded"] + 2 * (1 - c["depth_norm"])}


def apply(build, scene: dict) -> None:
    """Places the map's markers into scene["spawns"] (a map without markers keeps no `spawns`); writes the reports."""
    import mm9_ground_treasure as data
    project = build.project
    stem = project.stem
    hints = project.overrides.get("treasure") or {}
    count = int(hints.get("count", data.COUNTS.get(stem, 0)))
    work = project.work / "treasure.json"
    if count <= 0:
        scene.pop("spawns", None)
        work.write_text(json.dumps({"map": stem, "markers": 0, "note": "no markers for this map"}, indent=1) + "\n")
        return
    outdoor = "outdoor" in project.overrides
    walk = _walk()
    if outdoor:
        walk.GRID = REGION_GRID
    sys.path.insert(0, str(ROOT))
    from util.map_export import parse_blv_file
    blv_path = build.runtime / project.map
    blv = parse_blv_file(blv_path)["payload"]
    vertices = np.array([(v["x"], v["y"], v["z"]) for v in blv["vertices"]], float)
    world = World(blv, scene, liquid_textures())
    level = walk.load(blv_path)
    graph = walk.Graph(level)
    rng = random.Random(int(hashlib.sha256(f"treasure:{stem}".encode()).hexdigest()[:16], 16))

    # --- the floor the party reaches ---------------------------------------------------------------------------------
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from dungeon.audit import party_climbs
    climbs = party_climbs(walk, level, graph)
    links = defaultdict(set)
    for ladder in scene.get("ladders") or []:
        ends = [graph.node_near(*_xyz(ladder[k]), tolerance=96) for k in ("bottom", "top_exit", "top") if k in ladder]
        regions = {graph.region[n] for n in ends if n is not None}
        for a in regions:
            links[a] |= regions - {a}
    wet = set()
    for region, members in graph.members.items():
        sample = members[:: max(1, len(members) // 16)]
        wets = sum(world.in_water(*walk.centre_of(graph.cell[n]), graph.z[n]) for n in sample)
        if wets * 2 > len(sample):
            wet.add(region)
    starts = [dict(name=s.get("source_name", ""), point=_xyz(s["position"]))
              for s in scene.get("party_start_points", [])]
    seeds = {graph.region[n] for s in starts if (n := graph.node_near(*s["point"], tolerance=128)) is not None}
    # The floor the map means the party to reach though the walk graph cannot follow (teleporters, scripted lifts and
    # drops, ladders it misses): where a hostile monster that moves stands, and where a chest stands.
    meant = [_xyz(a["position"]) for a in scene["initial_state"].get("actors", [])
             if a.get("hostility_type") == HOSTILE and not a.get("immobile")
             and not (a.get("mm9_ai") or {}).get("dormant")]
    meant += [_xyz(c["position"]) for c in scene.get("loot_containers") or []]
    seeds |= {graph.region[n] for p in meant if (n := graph.node_near(*p, tolerance=64)) is not None
              and graph.region[n] not in wet}
    reached, queue = set(seeds), list(seeds)
    while queue:
        region = queue.pop()
        for nxt in graph.down.get(region, set()) | climbs.get(region, set()) | links.get(region, set()):
            if nxt not in reached and nxt not in wet:
                reached.add(nxt)
                queue.append(nxt)

    # --- depth and the main route ------------------------------------------------------------------------------------
    sectors = Sectors(blv, vertices)
    main = starts[0]["point"]
    _, main_record = world.floor(main[0], main[1], main[2] + 32)
    sectors.solve(main_record["sector"] if main_record else 0, main)
    route = []
    for s in starts[1:] if not outdoor else ():      # a region is one open sector: its starts and towns keep clear
        _, record = world.floor(s["point"][0], s["point"][1], s["point"][2] + 32)
        if record is not None:
            route.append(sectors.route(record["sector"], s["point"]))

    # --- what lies on the map ---------------------------------------------------------------------------------------
    actors = scene["initial_state"].get("actors", [])
    hostile = [_xyz(a["position"]) for a in actors if a.get("hostility_type") == HOSTILE]
    friendly = [_xyz(a["position"]) for a in actors if a.get("hostility_type") != HOSTILE]
    bosses = [_xyz(a["position"]) for a in actors if a.get("hostility_type") == HOSTILE
              and ((a.get("mm9_ai") or {}).get("boss") or a.get("monster_id") in BOSS_MONSTER_IDS
                   or a.get("unique_name_index"))]
    chests = [_xyz(c["position"]) for c in scene.get("loot_containers") or []]
    secrets = []
    for mover in getattr(build, "movers", []) or []:
        names = " ".join([str(mover.get("group", ""))] + [str(m) for m in mover.get("dat_models", [])])
        if SECRET_MOVER.search(names) and mover.get("box"):
            box = np.array(mover["box"], float)
            secrets.append(("mover " + str(mover.get("group")), tuple(box.mean(0))))
    for d in scene.get("destructibles") or []:
        # breakable walls, boards and lids hide things; breakable barrels, crates and urns (DestructableProp) do not
        if d.get("center") and build.source.object_class(str(d.get("name", ""))) != "DestructableProp":
            secrets.append(("destructible " + str(d.get("name")), _xyz(d["center"])))
    for face in blv["faces"]:
        if int((face.get("face_param") or {}).get("cog_number", 0)) in PERCEPTION_COGS:
            secrets.append(("perception", tuple(vertices[face["vertex_indices"]].mean(0))))
    for point in _named_points(build, scene, hints.get("bonus_near")):
        secrets.append(("hint", point))
        bosses.append(point)
    themed = _named_points(build, scene, hints.get("themed_near"))
    avoid = []
    for entry in hints.get("avoid_near") or []:
        point = _named_points(build, scene, [entry["name"]])[0] if "name" in entry else _xyz(entry["at"])
        avoid.append((point, float(entry.get("radius", 600))))
    towns = [s["point"] for s in starts if outdoor and TOWN_START.search(s["name"])]
    secret_depth = [(label, p, sectors.depth(world.floor(p[0], p[1], p[2] + 64)[1]["sector"], p)
                     if world.floor(p[0], p[1], p[2] + 64)[1] else math.inf) for label, p in secrets]
    chest_sectors = Counter(r["sector"] for p in chests if (r := world.floor(p[0], p[1], p[2] + 32)[1]) is not None)
    hostile_sectors = Counter(r["sector"] for p in hostile if (r := world.floor(p[0], p[1], p[2] + 32)[1]) is not None)
    friendly_sectors = Counter(r["sector"] for p in friendly if (r := world.floor(p[0], p[1], p[2] + 32)[1]))

    # --- candidate spots -------------------------------------------------------------------------------------------
    step = max(1, int(round(SAMPLE / walk.GRID)))
    candidates, rejected = [], Counter()
    for n, (i, j) in enumerate(graph.cell):
        if i % step or j % step or graph.region[n] not in reached:
            continue
        x, y = walk.centre_of((i, j))
        z = graph.z[n]
        point = (x, y, z)
        if graph.face[n].door is not None:
            rejected["mover"] += 1
            continue
        if level.headroom(x, y, z) < HEAD:
            rejected["headroom"] += 1
            continue
        fz, record = world.floor(x, y, z + 8)
        if record is None or abs(fz - z) > 8 or record["kind"]:
            rejected[record["kind"] if record else "no floor"] += 1
            continue
        if world.in_water(x, y, z):
            rejected["water"] += 1
            continue
        if world.wall_distance(x, y, z + 8, z + 100, WALL_CLEAR) < WALL_CLEAR:
            rejected["wall"] += 1
            continue
        if world.in_zone(x, y, z - 8, z + 100, ZONE_CLEAR):
            rejected["zone"] += 1
            continue
        near = lambda points, reach: any(math.hypot(x - p[0], y - p[1]) < reach and abs(z - p[2]) < 400
                                         for p in points)
        if near([s["point"] for s in starts], START_CLEAR) or near(towns, TOWN_CLEAR):
            rejected["start"] += 1
            continue
        if near(chests, OBJECT_CLEAR) or near(hostile, OBJECT_CLEAR) or near(friendly, FRIENDLY_CLEAR):
            rejected["object or friendly"] += 1
            continue
        if any(math.hypot(x - p[0], y - p[1]) < r for p, r in avoid):
            rejected["avoid_near"] += 1
            continue
        if any(_segment_distance(point, a, b) < ROUTE_CLEAR for line in route for a, b in zip(line, line[1:])):
            rejected["main route"] += 1
            continue
        sector = record["sector"]
        if not outdoor and friendly_sectors.get(sector) and not hostile_sectors.get(sector):
            rejected["peaceful sector"] += 1
            continue
        depth = sectors.depth(sector, point)
        if math.isinf(depth):
            depth = math.hypot(x - main[0], y - main[1])
        behind = [label for label, p, d in secret_depth
                  if math.hypot(x - p[0], y - p[1]) < SECRET_REACH and abs(z - p[2]) < 600 and depth > d + 64]
        candidates.append({
            "point": point, "sector": sector, "depth": depth,
            "secret": bool(behind), "secret_by": behind[:2],
            "boss": any(math.hypot(x - p[0], y - p[1]) < BOSS_REACH and abs(z - p[2]) < 600 for p in bosses),
            "guarded": any(math.hypot(x - p[0], y - p[1]) < GUARD_REACH and abs(z - p[2]) < 400 for p in hostile),
            "dead_end": not outdoor and len(sectors.neighbours.get(sector, ())) == 1,
            "themed": any(math.hypot(x - p[0], y - p[1]) < THEMED_REACH for p in themed),
            "jitter": rng.random() * 0.5,
        })
    deepest = max((c["depth"] for c in candidates), default=1.0) or 1.0
    for c in candidates:
        c["depth_norm"] = c["depth"] / deepest
        c["scores"] = _scores(c)

    # --- selection ---------------------------------------------------------------------------------------------------
    bonus_spots = [c for c in candidates if c["secret"] or c["boss"]]
    hand = [dict(point=_xyz(p["at"]), cls=p.get("class", "main")) for p in hints.get("place") or []]
    wanted = data.class_counts(stem, max(0, count - len(hand)), bool(bonus_spots))
    gap = REGION_STASH_GAP if outdoor else STASH_GAP
    chosen = [dict(point=p["point"], cls=p["cls"], sector=None, stash=None, reasons=["hand-placed"]) for p in hand]
    per_sector = Counter()

    def cap(c) -> int:
        if outdoor:
            return 10 ** 6
        if chest_sectors.get(c["sector"]):
            return CHEST_ROOM_CAP
        return BONUS_ROOM_CAP if c["secret"] or c["boss"] else ROOM_CAP

    def free(c, reach: float, centre=None) -> bool:
        if per_sector[c["sector"]] >= cap(c):
            return False
        x, y, z = c["point"]
        if centre is not None and math.hypot(x - centre[0], y - centre[1]) > STASH_REACH:
            return False
        for o in chosen:
            d = math.hypot(x - o["point"][0], y - o["point"][1])
            if d < (MEMBER_GAP if centre is not None else reach) and abs(z - o["point"][2]) < 400:
                return False
        return True

    def take(c, cls: str, stash) -> None:
        reasons = [k for k in ("secret", "boss", "guarded", "dead_end", "themed") if c[k]]
        chosen.append(dict(point=c["point"], cls=cls, sector=c["sector"], stash=stash, reasons=reasons,
                           secret_by=c["secret_by"]))
        per_sector[c["sector"]] += 1

    def crowd(c) -> int:
        if outdoor:
            x, y = c["point"][0], c["point"][1]
            return sum(math.hypot(x - o["point"][0], y - o["point"][1]) < REGION_SPREAD_REACH for o in chosen)
        return per_sector[c["sector"]]

    stash_id = 0
    stashes_left = max(1, round(count * STASH_SHARE)) if count >= STASH_MIN_COUNT else 0
    shortfall = {}
    for cls in ("bonus", "main", "lower"):
        need = wanted[cls]
        pool = sorted(bonus_spots if cls == "bonus" else candidates, key=lambda c: -c["scores"][cls])
        while need > 0:
            first = max((c for c in pool if free(c, gap)), key=lambda c: c["scores"][cls] - SPREAD * crowd(c),
                        default=None)
            if first is None:
                break
            stash_id += 1
            take(first, cls, stash_id)
            need -= 1
            if need > 0 and stashes_left > 0:
                members = 0
                for _ in range(min(need, rng.choice((1, 2)))):
                    member = next((c for c in pool if c["sector"] == first["sector"] and c is not first
                                   and free(c, gap, first["point"])), None)
                    if member is None:
                        break
                    take(member, cls, stash_id)
                    need -= 1
                    members += 1
                stashes_left -= 1 if members else 0
        if need > 0 and cls == "bonus":
            wanted["main"] += need          # too few spots behind secrets or by bosses: the rest are main markers
        elif need > 0:
            shortfall[cls] = need

    # --- the scene's spawns and the reports -------------------------------------------------------------------------
    tiers = data.marker_tiers(stem)
    spawns = []
    for k, marker in enumerate(chosen):
        x, y, z = marker["point"]
        marker["tiers"] = list(tiers[marker["cls"]])
        marker["index"] = data.marker_index(stem, tiers[marker["cls"]])
        spawns.append({"spawn_index": k, "position": {"x": int(round(x)), "y": int(round(y)), "z": int(math.floor(z))},
                       "radius": data.MARKER_RADIUS, "type_id": 2, "index": marker["index"], "attributes": 0,
                       "group": 0})
    scene["spawns"] = spawns
    stashes = Counter(m["stash"] for m in chosen if m["stash"] is not None)
    report = {
        "map": stem, "wanted": count, "placed": len(chosen), "shortfall": shortfall,
        "by_class": dict(Counter(m["cls"] for m in chosen)), "tiers": {k: list(v) for k, v in tiers.items()},
        "guarded_share": round(sum("guarded" in m["reasons"] for m in chosen) / max(1, len(chosen)), 2),
        "stash_share": round(sum(stashes[m["stash"]] > 1 for m in chosen) / max(1, len(chosen)), 2),
        "secrets_used": sorted({s for m in chosen for s in m.get("secret_by", [])}),
        "candidates": len(candidates), "bonus_spots": len(bonus_spots), "rejected": dict(rejected),
        "secret_anchors": len(secrets), "bosses": len(bosses), "starts": [s["name"] for s in starts],
        "markers": [{k: (list(map(round, v)) if k == "point" else v) for k, v in m.items()} for m in chosen],
    }
    work.write_text(json.dumps(report, indent=1) + "\n")
    _plan_image(project.work / "treasure.png", graph, walk, reached, chosen, hostile, chests, starts, route, secrets)
    build.treasure = {k: report[k] for k in ("wanted", "placed", "shortfall", "by_class", "guarded_share",
                                             "stash_share")}
    print(f"treasure: {len(chosen)} of {count} markers ({report['by_class']}, guarded {report['guarded_share']}, "
          f"stashed {report['stash_share']}, shortfall {shortfall or 'none'}; work/treasure.json, treasure.png)")


def _plan_image(path: Path, graph, walk, reached: set, chosen: list, hostile: list, chests: list, starts: list,
                route: list, secrets: list) -> None:
    """A top-down plan: the reached floor grey, the main route blue, markers by class (bonus gold, main green, lower
    pale), stashes ringed, hostile actors red, chests brown, secrets violet, starts cyan."""
    from PIL import Image, ImageDraw
    cells = [graph.cell[n] for n in range(len(graph.cell)) if graph.region[n] in reached]
    if not cells:
        return
    xs = [walk.centre_of(c)[0] for c in cells]
    ys = [walk.centre_of(c)[1] for c in cells]
    x0, x1, y0, y1 = min(xs) - 256, max(xs) + 256, min(ys) - 256, max(ys) + 256
    scale = 1600 / max(x1 - x0, y1 - y0)
    image = Image.new("RGB", (int((x1 - x0) * scale) + 1, int((y1 - y0) * scale) + 1), (20, 20, 24))
    draw = ImageDraw.Draw(image)
    to = lambda x, y: ((x - x0) * scale, (y1 - y) * scale)
    half = max(1.0, walk.GRID * scale / 2)
    for x, y in zip(xs, ys):
        px, py = to(x, y)
        draw.rectangle((px - half, py - half, px + half, py + half), fill=(70, 70, 76))
    for line in route:
        draw.line([to(p[0], p[1]) for p in line], fill=(60, 110, 220), width=2)
    for _, p in secrets:
        px, py = to(p[0], p[1])
        draw.rectangle((px - 4, py - 4, px + 4, py + 4), outline=(170, 90, 230), width=2)
    for p in chests:
        px, py = to(p[0], p[1])
        draw.rectangle((px - 4, py - 4, px + 4, py + 4), fill=(150, 100, 50))
    for p in hostile:
        px, py = to(p[0], p[1])
        draw.ellipse((px - 2, py - 2, px + 2, py + 2), fill=(210, 50, 50))
    for s in starts:
        px, py = to(s["point"][0], s["point"][1])
        draw.polygon([(px, py - 7), (px - 6, py + 5), (px + 6, py + 5)], fill=(60, 220, 230))
    colours = {"bonus": (250, 200, 40), "main": (70, 210, 90), "lower": (210, 210, 190)}
    stash_sizes = Counter(m["stash"] for m in chosen if m["stash"] is not None)
    for m in chosen:
        px, py = to(m["point"][0], m["point"][1])
        if stash_sizes.get(m["stash"], 0) > 1:
            draw.ellipse((px - 9, py - 9, px + 9, py + 9), outline=(255, 255, 255), width=1)
        draw.ellipse((px - 5, py - 5, px + 5, py + 5), fill=colours[m["cls"]], outline=(0, 0, 0))
    image.save(path)
