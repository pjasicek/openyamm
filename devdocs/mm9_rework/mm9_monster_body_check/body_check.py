"""usage: python3 body_check.py <map stem> [<actors_only.json>]; writes check_<stem>.json here.

Consequences of MM9's monster bodies on the built review-root maps, without rebuilding them: per placed actor of an
MM9 monster row the old body (the scene's) and the new one (actors_only.json from the converter when given, else the
new table's row body when the scene's body was the old table's), the walkability audit's actor findings (wall within
the radius, ceiling under the height, overhang) for both, and whether the actor can still (or now) walk to the party
start through gaps of its radius (a 4-neighbour clearance field over the floor cells)."""
import json, math, sys, csv
from collections import defaultdict, deque
from pathlib import Path
ROOT = Path("/home/pjasicek/github/OpenYAMM")
S = Path(__file__).resolve().parent      # old_monster_descriptors.txt (the table before 2026-10-31), outputs
sys.path.insert(0, str(ROOT / "level_generation/projects/hesper_stage"))
import check_walkability as walk
walk.MONSTER_TABLES = [ROOT / "assets_dev/worlds/mm9/data_tables/monster_data.txt"]
MAPS = ROOT / "output/mm9_rework/assets_dev/worlds/mm9/maps"

def table(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        f = line.rstrip("\n").split("\t")
        if f and f[0].isdigit():
            out[int(f[0])] = (int(f[2]), int(f[3]))
    return out
OLD = table(S / "old_monster_descriptors.txt")
NEW = table(ROOT / "assets_dev/worlds/mm9/data_tables/monster_descriptors.txt")

def clearance_field(level):
    """node -> (cells to the nearest boundary, z, cell); adjacency within MONSTER_STEP without a wall at z + BODY."""
    nodes, z_of, cell_of = {}, [], []
    for cell, entries in level.cells.items():
        ids = []
        for z, face in sorted(entries, key=lambda e: e[0]):
            if ids and abs(z_of[ids[-1]] - z) < 1:
                continue
            ids.append(len(z_of)); z_of.append(z); cell_of.append(cell)
        nodes[cell] = ids
    adj = defaultdict(list)
    for (i, j), ids in nodes.items():
        for other in ((i + 1, j), (i, j + 1)):
            for m in nodes.get(other, ()):
                for n in ids:
                    if abs(z_of[m] - z_of[n]) > walk.MONSTER_STEP:
                        continue
                    if ((i, j) in level.wall_cells or other in level.wall_cells) and level.blocked(
                            *walk.centre_of((i, j)), *walk.centre_of(other), max(z_of[n], z_of[m]) + walk.BODY):
                        continue
                    adj[n].append(m); adj[m].append(n)
    dist = [-1] * len(z_of)
    q = deque()
    for n in range(len(z_of)):
        if len(adj[n]) < 4:
            dist[n] = 0; q.append(n)
    while q:
        n = q.popleft()
        for m in adj[n]:
            if dist[m] < 0:
                dist[m] = dist[n] + 1; q.append(m)
    head = [level._room(level.surfaces.get(cell_of[n], ()), z_of[n]) for n in range(len(z_of))]
    return nodes, z_of, cell_of, adj, dist, head

def node_near(nodes, z_of, x, y, z, tol=40):
    ci, cj = walk.cell_of(x, y); best = None
    for i in (ci - 1, ci, ci + 1):
        for j in (cj - 1, cj, cj + 1):
            for n in nodes.get((i, j), ()):
                if abs(z_of[n] - z) <= tol:
                    cx, cy = walk.centre_of((i, j)); d = math.hypot(cx - x, cy - y)
                    if best is None or d < best[0]:
                        best = (d, n)
    return None if best is None else best[1]

def reach(field, start, goal, radius, height):
    nodes, z_of, cell_of, adj, dist, head = field
    ok = lambda n: (dist[n] + 0.5) * walk.GRID >= radius and head[n] >= height
    seen, q = {start}, deque([start])
    while q:
        n = q.popleft()
        if n == goal:
            return True
        for m in adj[n]:
            if m not in seen and ok(m):
                seen.add(m); q.append(m)
    return False

def run(stem, harness=None):
    blv = MAPS / f"{stem}.blv"
    scene = json.loads(blv.with_suffix(".scene.yml").read_text())
    level = walk.load(blv)
    new_by_index = {}
    if harness and Path(harness).exists():
        for a in json.loads(Path(harness).read_text()):
            new_by_index[a["actor_index"]] = (a["height"], a["radius"], a["monster_id"], a["name"])
    rows = []
    for a in scene["initial_state"].get("actors", []):
        mid = a["monster_id"]
        if mid < 9000:
            continue
        old = (a["height"], a["radius"])
        if harness and a["actor_index"] in new_by_index:
            h, r, hmid, hname = new_by_index[a["actor_index"]]
            if hmid != mid:
                print(f"  ! {stem} actor {a['actor_index']} monster {mid} vs harness {hmid}")
            new = (h, r)
        elif old == OLD.get(mid):
            new = NEW[mid]
        else:
            new = old          # the converter's own body: a rebuild keeps it
        rows.append((a, old, new))
    changed = [(a, o, n) for a, o, n in rows if o != n]
    # actor findings before / after
    def findings(bodies):
        for actor in level.actors:
            if actor["index"] in bodies:
                actor["height"], actor["radius"] = bodies[actor["index"]]
        return {f["actor"]: f["text"] for f in walk.actor_findings(level)}
    before = findings({a["actor_index"]: o for a, o, n in rows})
    after = findings({a["actor_index"]: n for a, o, n in rows})
    field = clearance_field(level)
    st = scene["party_start_points"][0]["position"]
    st = st if isinstance(st, list) else [st["x"], st["y"], st["z"]]
    goal = node_near(field[0], field[1], st[0], st[1], st[2], tol=60)
    flying = walk.flyers()
    out = []
    for a, o, n in changed:
        idx = a["actor_index"]
        p = a["position"]
        line = {"map": stem, "actor": idx, "name": a["name"], "monster": a["monster_id"], "old": o, "new": n,
                "at": [p["x"], p["y"], p["z"]], "flies": a["monster_info_id"] in flying,
                "immobile": bool(a.get("immobile")), "hidden": bool(a.get("attributes", 0) & 0x0)}
        if idx in after and idx not in before:
            line["new_fit_problem"] = after[idx]
        elif idx in before and idx not in after:
            line["fit_fixed"] = before[idx]
        elif idx in after:
            line["fit_problem_both"] = after[idx]
        start = node_near(field[0], field[1], p["x"], p["y"], p["z"])
        if goal is not None and start is not None and not line["flies"] and not line["immobile"]:
            ro = reach(field, start, goal, o[1], o[0]); rn = reach(field, start, goal, n[1], n[0])
            if ro != rn:
                line["reach_party_start"] = f"{ro} -> {rn}"
        out.append(line)
    return {"map": stem, "mm9_actors": len(rows), "changed": len(changed), "goal": goal is not None, "actors": out}

if __name__ == "__main__":
    stem = sys.argv[1]; harness = sys.argv[2] if len(sys.argv) > 2 else None
    result = run(stem, harness)
    (S / f"check_{stem}.json").write_text(json.dumps(result, indent=1))
    probs = [l for l in result["actors"] if any(k in l for k in ("new_fit_problem", "reach_party_start", "fit_fixed"))]
    print(stem, "mm9 actors", result["mm9_actors"], "changed", result["changed"], "flagged", len(probs))
