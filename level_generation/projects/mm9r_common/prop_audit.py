#!/usr/bin/env python3
"""
Prop placement audit for the remade MM9 maps (the user, 2026-11-06: parchments, shields and other wall items, things on
desks and wardrobes placed wrong). For every decoration of a built BLV in the review root that stands for an MM9 DAT
model object, the decoration's GLB placed as the engine places it (binding height and z_offset, facing, glTF
(x, y, z) -> native (-x, z, y)) is compared with MM9's own placement of the ABC: its first animation's first key (the
pose LithTech draws, prop_pose.py), the DAT Scale and the full Euler Rotation (pitch, yaw, roll: decorations turn about
the vertical only), at the DAT Pos.

Per prop: `fit` (median distance of our vertices from MM9's mesh), the best quarter turn of our mesh about its own
position against MM9's (`turn`, with the fit it gives), the box-centre shift and the bottom difference (`dz`). Each
prop is also checked against its surroundings in our map: `gap` (its bottom over the highest upward surface under its
footprint: BLV floors and the other decorations' tops; negative = sunk) and, for a prop MM9 hangs on a wall (no support
under it, its back within reach of a wall), `wall` (our mesh's distance from that wall; negative = inside it).
MoveToFloor props are compared in plan only (LithTech drops them at load), their height by `gap`.

    python3 level_generation/projects/mm9r_common/prop_audit.py [stem ...]   # all maps without stems
    python3 level_generation/projects/mm9r_common/prop_audit.py --props stem  # props.json as a convert would place it
writes output/mm9_rework/prop_audit_20261107/<stem>.json and the summary table devdocs/mm9_rework/PROP_PLACEMENT_AUDIT.md
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import yaml
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

import review_root                                              # noqa: E402
from dungeon import prop_pose                                   # noqa: E402
from dungeon.source import Project, Source                      # noqa: E402
from util.map_export import parse_blv_file                      # noqa: E402

OUT = ROOT / "output/mm9_rework/prop_audit_20261107"
MAPS = review_root.ASSETS / "worlds/mm9/maps"
REGION_MAPS = review_root.REVIEW / "isleofashes_blv_root/worlds/mm9/maps"     # the regions' root (outdoor_blv.py)
FIT_BAD = 6.0           # native units: median vertex distance that marks a misplaced prop
TURN_GAIN = 0.5         # a quarter turn is flagged when it at least halves the fit and the fit is bad
GAP_BAD = 4.0           # native units: floating over / sunk into the surface under it
WALL_REACH = 8.0        # native units: MM9's mesh within this of a wall face hangs on it
WALL_BAD = 4.0


def map_path(stem: str, directory: Path) -> Path:
    """The built BLV of a map project: a region's (`*_blv` projects) in the regions' root, else the review root's."""
    return (REGION_MAPS if directory.name.endswith("_blv") else MAPS) / f"{stem}.blv"


def stems() -> dict:
    """map stem -> project directory, for every MM9 remake project with an overrides.yml."""
    found = {}
    for directory in sorted((ROOT / "level_generation/projects").glob("mm9r_*")):
        overrides = directory / "overrides.yml"
        if overrides.is_file():
            stem = yaml.safe_load(overrides.read_text())["map"]["stem"]
            found[stem] = directory
    return found


def decoration_names() -> dict:
    """decoration list id -> name, as content.decoration_ids()."""
    world = yaml.safe_load(review_root.mirror_path("worlds/mm9/world.yml").read_text())
    tables = ["engine/data_tables/decoration_data.txt"] + [
        "worlds/mm9/" + c["path"] for c in world.get("tableContributions", []) if c.get("table") == "decorations"]
    names = {}
    for table in tables:
        for cells in (line.split("\t") for line in review_root.mirror_path(table).read_text(encoding="latin-1")
                      .splitlines()):
            if len(cells) > 1 and cells[0].strip().isdigit():
                names[int(cells[0]) - 1] = cells[1].strip().lower()
    return names


def bindings() -> dict:
    found = {}
    for path in (review_root.mirror_path("worlds/mm9/models/indoor_decorations.yml"),
                 ROOT / "assets_dev/worlds/mm9/models/indoor_decorations.yml",
                 review_root.mirror_path("engine/models/indoor_decorations.yml")):
        if path.is_file():
            for b in yaml.safe_load(path.read_text())["decorations"]:
                found.setdefault(b["name"].lower(), b)
    return found


# --- GLB meshes ------------------------------------------------------------------------------------------------------
def rz(degrees: float) -> np.ndarray:
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def placed_ours(binding: dict, position, facing: float):
    points, triangles = prop_pose.decoration_mesh(binding, facing)
    return points + np.asarray(position, float), triangles


def placed_mm9(project: Project, obj: dict):
    """MM9's mesh of a DAT object as MM9 draws it (prop_pose.mm9_mesh: the posed ABC at the DAT Scale, Rotation and
    binding translation) at its DAT Pos raised by its initial update's lift (prop_pose.lift). MoveToFloor objects
    drop after it at load; the audit compares those in plan only."""
    properties = obj["properties"]
    position = project.native(np.asarray(properties["Pos"], float))
    rise = prop_pose.lift(properties, obj["class"])
    return prop_pose.mm9_mesh(properties, position + np.array([0.0, 0.0, rise]))


# --- Map geometry ----------------------------------------------------------------------------------------------------
class Geometry:
    """The built BLV's faces as triangles: upward ones (floors, for support) and steep ones (walls)."""
    def __init__(self, blv: dict):
        v = np.array([[p["x"], p["y"], p["z"]] for p in blv["vertices"]], float)
        tris, polys = [], []
        for f in blv["faces"]:
            if f.get("is_portal"):
                continue
            idx = f["vertex_indices"][:f["vertex_per_face_count"]]
            if len(idx) < 3:
                continue
            poly = v[idx]
            polys.append(poly)
            for k in range(1, len(idx) - 1):
                tris.append((poly[0], poly[k], poly[k + 1]))
        self.tris = np.array(tris, float)
        n = np.cross(self.tris[:, 1] - self.tris[:, 0], self.tris[:, 2] - self.tris[:, 0])
        length = np.linalg.norm(n, axis=1)
        keep = length > 1e-6
        self.tris, n = self.tris[keep], n[keep] / length[keep, None]
        self.normal = n
        self.up = self.tris[n[:, 2] > 0.5]
        self.walls = self.tris[np.abs(n[:, 2]) < 0.35]
        self.wall_normal = n[np.abs(n[:, 2]) < 0.35]
        self.up_low, self.up_high = self.up.min(1), self.up.max(1)
        self.wall_low, self.wall_high = self.walls.min(1), self.walls.max(1)


def cross2(edge: np.ndarray, dx, dy) -> np.ndarray:
    return edge[:, 0] * dy - edge[:, 1] * dx


def support_heights(tris: np.ndarray, xy: np.ndarray, z_max: float) -> np.ndarray:
    """Per query point the highest point of the upward triangles over it at or below z_max (nan where none)."""
    best = np.full(len(xy), np.nan)
    if not len(tris):
        return best
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    for i, (x, y) in enumerate(xy):
        d = (cross2(b - a, x - a[:, 0], y - a[:, 1]), cross2(c - b, x - b[:, 0], y - b[:, 1]),
             cross2(a - c, x - c[:, 0], y - c[:, 1]))
        inside = ((d[0] >= -1e-6) & (d[1] >= -1e-6) & (d[2] >= -1e-6)) | (
            (d[0] <= 1e-6) & (d[1] <= 1e-6) & (d[2] <= 1e-6))
        if not inside.any():
            continue
        t = tris[inside]
        n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        ok = np.abs(n[:, 2]) > 1e-9
        t, n = t[ok], n[ok]
        z = t[:, 0, 2] - (n[:, 0] * (x - t[:, 0, 0]) + n[:, 1] * (y - t[:, 0, 1])) / n[:, 2]
        z = z[z <= z_max]
        if len(z):
            best[i] = z.max()
    return best


def footprint_samples(points: np.ndarray) -> np.ndarray:
    """Plan samples under a mesh's lowest part: the vertices within 2 units of its bottom, thinned."""
    low = points[points[:, 2] <= points[:, 2].min() + 2.0][:, :2]
    if len(low) > 24:
        low = low[np.linspace(0, len(low) - 1, 24).astype(int)]
    centre = (points[:, :2].min(0) + points[:, :2].max(0)) / 2
    shrunk = centre + (low - centre) * 0.8          # off the very edge: a lip overhanging its support is fine
    return np.vstack([shrunk, centre])


def wall_distance(geometry: Geometry, points: np.ndarray):
    """(signed distance, wall normal) of a mesh from the nearest wall triangle whose plane its vertices face: the
    smallest distance in front of the wall over the vertices projecting inside the triangle; negative = the deepest
    vertex behind it (within 64 units)."""
    lo, hi = points.min(0) - 16, points.max(0) + 16
    near = np.nonzero(np.all(geometry.wall_high >= lo, 1) & np.all(geometry.wall_low <= hi, 1))[0]
    best = None
    for i in near:
        t, n = geometry.walls[i], geometry.wall_normal[i]
        d = (points - t[0]) @ n
        # the projection inside the triangle (in the wall plane)
        e0, e1 = t[1] - t[0], t[2] - t[0]
        rel = points - t[0] - np.outer(d, n)
        d00, d01, d11 = e0 @ e0, e0 @ e1, e1 @ e1
        den = d00 * d11 - d01 * d01
        if abs(den) < 1e-9:
            continue
        b0, b1 = rel @ e0, rel @ e1
        v = (d11 * b0 - d01 * b1) / den
        w = (d00 * b1 - d01 * b0) / den
        inside = (v >= -0.02) & (w >= -0.02) & (v + w <= 1.02)
        if not inside.any():
            continue
        dd = d[inside]
        if dd.min() < -64:
            continue
        value = float(dd.min())
        if best is None or abs(value) < abs(best[0]):
            best = (value, n)
    return best


def props_entities(directory: Path, source: Source, binds: dict, ids: dict, geometry: "Geometry") -> list[dict]:
    """The decorations a convert would place from the project's props.json (before converting it): its entries with
    prop_pose's pose, initial-update lift and MoveToFloor drop (content.props, the built map's floors), positions
    rounded as content.entity rounds them (the tree swap and the stat barrels are left out)."""
    def floor_at(x, y, z_max):
        z = prop_pose.surface_heights(geometry.up, np.array([[x, y]]), z_max)[0]
        return float(z) if np.isfinite(z) else None

    rows = []
    for entry in json.loads((directory / "props.json").read_text()):
        decoration = str(entry["decoration"]).lower()
        position, yaw = (entry["x"], entry["y"], entry["z"]), entry["yaw_degrees"]
        posed = prop_pose.placement(entry, source.objects, binds.get(decoration))
        if posed is not None:
            position, yaw = posed
        position = np.asarray(position, float)
        if not directory.name.endswith("_blv"):     # a region's props.json is in its map's frame (outdoor_blv.populate)
            position = position - np.asarray(source.project.offset, float)                 # the old map's frame
        moved = prop_pose.lifted(entry, source.objects, binds.get(decoration), position, source.project.native)
        if moved is not None:
            position = np.asarray(moved, float)
        rows.append((entry, decoration, position, yaw))
    items = []
    for index, (entry, decoration, position, yaw) in enumerate(rows):
        binding = binds.get(decoration)
        obj = source.objects[entry["source_object"]] if isinstance(entry.get("source_object"), int) else None
        if binding is None or obj is None or not isinstance(entry.get("source_object"), int):
            continue
        points, triangles = prop_pose.decoration_mesh(binding, float(yaw))
        items.append({"key": index, "points": points, "triangles": triangles, "position": tuple(position),
                      "move_to_floor": bool(obj["properties"].get("MoveToFloor", 0)) and not binding.get("z_offset"),
                      "dat_z": float(source.project.native(np.asarray(obj["properties"]["Pos"], float))[2])})

    for key, z in prop_pose.move_to_floor(items, floor_at).items():
        rows[key][2][2] = z
    return [{"name": entry["source_name"], "decoration_list_id": ids.get(decoration, -1),
             "facing": int(round(yaw)) % 360,
             "position": {"x": int(round(position[0])), "y": int(round(position[1])),
                          "z": int(math.ceil(position[2] - 0.05))}}
            for entry, decoration, position, yaw in rows]


def audit_map(stem: str, directory: Path, names: dict, binds: dict, from_props: bool = False) -> list[dict]:
    project = Project.load(directory, install=False)
    source = Source(project)
    blv = parse_blv_file(map_path(stem, directory))["payload"]
    geometry = Geometry(blv)
    entities = blv["entities"]
    if from_props:
        entities = props_entities(directory, source, binds, {v: k for k, v in names.items()}, geometry)
    placed = []
    for entity in entities:
        name = names.get(entity["decoration_list_id"], "")
        binding = binds.get(name)
        obj = source.by_name.get(str(entity["name"]).lower())
        if obj is None and str(entity["name"]).startswith("obj_"):
            obj = source.by_name.get(str(entity["name"])[4:].lower())     # a region's entity: obj_<DAT name>
        renamed = re.fullmatch(r"(.+)_(\d+)", str(entity["name"]))
        if renamed and int(renamed.group(2)) < len(source.objects) \
                and source.objects[int(renamed.group(2))]["name"].lower() == renamed.group(1).lower():
            obj = source.objects[int(renamed.group(2))]          # a repeated DAT name, renamed <name>_<index>
        if binding is None or obj is None:
            continue
        props = obj["properties"]
        if not str(props.get("Filename", "")).lower().endswith(".abc"):
            continue
        pos = entity["position"]
        ours, ours_tris = placed_ours(binding, (pos["x"], pos["y"], pos["z"]), float(entity["facing"]))
        placed.append({"entity": entity, "decoration": name, "binding": binding, "object": obj,
                       "ours": ours, "tris": ours_tris})
    # every decoration's upward triangles: the surfaces other props rest on
    for p in placed:
        t = p["ours"][p["tris"]]
        n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        length = np.linalg.norm(n, axis=1)
        good = length > 1e-9
        up = np.zeros(len(t), bool)
        up[good] = (n[good, 2] / length[good]) > 0.7
        p["up"] = t[up]
        p["low"], p["high"] = p["ours"].min(0), p["ours"].max(0)

    def support(points: np.ndarray, skip: int, floor_reach: float, prop_reach: float) -> float | None:
        """The highest surface under a mesh's footprint: BLV floors up to floor_reach, the other decorations' tops up
        to prop_reach."""
        samples = footprint_samples(points)
        lo, hi = points.min(0) - 2, points.max(0) + 2
        near = np.all(geometry.up_high[:, :2] >= lo[:2], 1) & np.all(geometry.up_low[:, :2] <= hi[:2], 1)
        best = support_heights(geometry.up[near], samples, floor_reach)
        others = [q["up"] for j, q in enumerate(placed) if j != skip and len(q["up"])
                  and np.all(q["high"][:2] >= lo[:2]) and np.all(q["low"][:2] <= hi[:2])]
        if others:
            best = np.fmax(best, support_heights(np.concatenate(others), samples, prop_reach))
        return None if not np.isfinite(best).any() else float(np.nanmax(best))

    def surface_gap(points: np.ndarray, skip: int) -> float | None:
        """A mesh's bottom over the highest surface under it: BLV floors up to 60 units over its bottom (a prop sunk
        into its floor), the other decorations' tops up to 24 (half its height for a small one)."""
        bottom, height = float(points[:, 2].min()), float(np.ptp(points[:, 2]))
        top = support(points, skip, bottom + min(60.0, 0.6 * height), bottom + min(24.0, 0.5 * height))
        return None if top is None else round(bottom - top, 1)

    rows = []
    for i, p in enumerate(placed):
        props, entity = p["object"]["properties"], p["entity"]
        mm9 = placed_mm9(project, p["object"])
        if mm9 is None:
            continue
        ours = p["ours"]
        move_to_floor = bool(props.get("MoveToFloor", 0))
        # MM9's height is not authoritative (LithTech drops MoveToFloor props; a chair's DAT position is its base
        # although its ABC origin is mid-height): plan and orientation are compared with the bottoms aligned
        dz = float(ours[:, 2].min() - mm9[:, 2].min())
        aligned = mm9 + np.array([0.0, 0.0, dz])
        tree = cKDTree(aligned)
        fit = float(np.median(tree.query(ours)[0]))
        centre = np.array([entity["position"]["x"], entity["position"]["y"], 0.0])
        best_turn, best_fit = 0, fit
        for turn in (90, 180, 270):
            turned = (ours - centre) @ rz(turn).T + centre
            f = float(np.median(tree.query(turned)[0]))
            if f < best_fit:
                best_turn, best_fit = turn, f
        shift = (aligned.min(0) + aligned.max(0)) / 2 - (ours.min(0) + ours.max(0)) / 2
        gap = surface_gap(ours, i)
        # MM9 hangs it (on a wall or from the ceiling) when nothing is under its DAT position or its drawn mesh within
        # 24 units: there its DAT height is the authority; a standing prop must rest on the surface under it
        pos_z = float(project.native(np.asarray(props["Pos"], float))[2])
        mm9_bottom = float(mm9[:, 2].min())
        under = support(mm9, i, max(pos_z, mm9_bottom) + 8, max(pos_z, mm9_bottom) + 8)
        mm9_gap = None if under is None else round(mm9_bottom - under, 1)
        hanging = not move_to_floor and (under is None or min(pos_z, mm9_bottom) - under > 24)
        wall_mm9 = wall_distance(geometry, mm9) if hanging else None
        hung = hanging and wall_mm9 is not None and abs(wall_mm9[0]) <= WALL_REACH
        wall_ours = wall_distance(geometry, ours) if hung else None
        rotation = [round(math.degrees(float(v)), 1) for v in (list(props.get("Rotation") or [0, 0, 0]) + [0] * 3)[:3]]
        row = {"name": entity["name"], "decoration": p["decoration"], "model": str(props.get("Filename")),
               "class": p["object"]["class"], "position": [entity["position"][k] for k in "xyz"],
               "facing": entity["facing"], "mm9_rotation_deg": rotation, "move_to_floor": move_to_floor,
               "fit": round(fit, 1), "turn": best_turn, "turn_fit": round(best_fit, 1),
               "shift": [round(float(v), 1) for v in shift], "dz": round(dz, 1),
               "gap": gap, "mm9_gap": mm9_gap, "hanging": hanging, "hung": hung,
               "wall_mm9": None if wall_mm9 is None else round(wall_mm9[0], 1),
               "wall": None if wall_ours is None else round(wall_ours[0], 1),
               "size": [round(float(v)) for v in np.ptp(mm9, 0)]}
        row["flags"] = flags(row)
        rows.append(row)
    return rows


def flags(row: dict) -> list[str]:
    out = []
    tilted = abs(row["mm9_rotation_deg"][0]) > 5 or abs(row["mm9_rotation_deg"][2]) > 5
    if row["turn"] and row["fit"] > FIT_BAD and row["turn_fit"] < row["fit"] * TURN_GAIN:
        out.append(f"turn{row['turn']}")
    elif row["fit"] > FIT_BAD:
        out.append("tilt_lost" if tilted else "misfit")
    if row["hanging"]:
        if row["hung"]:
            if row["wall"] is None or row["wall"] > WALL_BAD:
                out.append("off_wall")
            elif row["wall"] < -WALL_BAD:
                out.append("in_wall")
        if abs(row["dz"]) > GAP_BAD:
            out.append("height")
    elif row["gap"] is None:
        out.append("no_support")
    elif abs(row["gap"]) > GAP_BAD and not (
            not row["move_to_floor"] and (abs(row["dz"]) <= 3 and row["fit"] <= FIT_BAD or row["mm9_gap"] is not None
                                          and abs(row["gap"] - row["mm9_gap"]) <= 3)):
        out.append("floating" if row["gap"] > 0 else "sunk")      # unless MM9 draws it so too (its DAT height)
    return out


REPORT = ROOT / "devdocs/mm9_rework/PROP_PLACEMENT_AUDIT.md"
# Decorations that stand for something else on purpose: the regions' trees (trees.py), the drinkable stat barrels.
REPORT_SKIP = ("mm9v_", "mm9_statbarrel")


def report() -> None:
    """devdocs/mm9_rework/PROP_PLACEMENT_AUDIT.md: its hand-written part (everything before "## Per map") kept and,
    per map audited (OUT/<stem>.json), the flagged decorations grouped by decoration and flag set."""
    def median(values):
        values = [v for v in values if v is not None]
        return "" if not values else f"{float(np.median(values)):.0f}"
    head = REPORT.read_text().split("## Per map")[0].rstrip("\n") if REPORT.is_file() else "# MM9 prop placement audit"
    lines = [head, "", "## Per map (built review-root BLVs)", ""]
    for path in sorted(OUT.glob("*.json")):
        if path.name.endswith(".props.json"):
            continue
        rows = [r for r in json.loads(path.read_text()) if not r["decoration"].startswith(REPORT_SKIP)]
        if not rows:
            continue
        flagged = [r for r in rows if r["flags"]]
        lines += [f"### {path.stem}", "", f"{len(rows)} props compared, {len(flagged)} flagged.", ""]
        if not flagged:
            continue
        groups = {}
        for r in flagged:
            groups.setdefault((r["decoration"], " ".join(r["flags"])), []).append(r)
        lines += ["| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |",
                  "|---|---|---|---|---|---|---|---|"]
        for (decoration, flag_text), group in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            lines.append(
                f"| {decoration} | {flag_text} | {len(group)} | {median([r['fit'] for r in group])} "
                f"| {median([r['dz'] for r in group])} | {median([r['gap'] for r in group])} "
                f"({median([r['mm9_gap'] for r in group])}) | {median([r['wall'] for r in group])} "
                f"({median([r['wall_mm9'] for r in group])}) | {', '.join(r['name'] for r in group[:4])} |")
        lines.append("")
    REPORT.write_text("\n".join(lines) + "\n")
    print("wrote", REPORT)


def main(argv: list[str]) -> None:
    if argv == ["--report"]:
        report()
        return
    OUT.mkdir(parents=True, exist_ok=True)
    from_props = "--props" in argv           # audit what props.json would place, against the built map's geometry
    argv = [a for a in argv if a != "--props"]
    found = stems()
    wanted = argv or [s for s in found if map_path(s, found[s]).is_file()]
    names, binds = decoration_names(), bindings()
    for stem in wanted:
        try:
            rows = audit_map(stem, found[stem], names, binds, from_props)
        except Exception as error:                       # report and go on: one broken map must not stop the audit
            print(f"{stem}: FAILED {error!r}")
            continue
        (OUT / f"{stem}{'.props' if from_props else ''}.json").write_text(json.dumps(rows, indent=1) + "\n")
        flagged = [r for r in rows if r["flags"]]
        print(f"{stem}: {len(rows)} props, {len(flagged)} flagged")


if __name__ == "__main__":
    main(sys.argv[1:])
