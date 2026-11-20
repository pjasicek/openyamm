#!/usr/bin/env python3
"""
The cinematics' camera gate (devdocs/mm9_rework/MM9_CUTSCENES.md section 9): every camera of a map's cinematics checked
against the compiled BLV it will play in.

For each shot (a fixed camera) and each moving shot sampled every quarter second, the eye must be:
  - inside the map: rays from it in 14 directions all meet a drawn face, and the faces they meet first face the eye
    (BLV face normals point into the rooms): not out at the void, not inside a wall, cliff or floor;
  - at least CLEARANCE units from every drawn face;
and its aim must read:
  - a look_at point or actor: within the 90-degree view (45 degrees off the axis) and in clear sight (no drawn face
    between the eye and the target, short of the target itself);
  - a direction: the first face along it at least FACING_CLEAR units away (not staring into a wall).
Portal faces and invisible faces (collision brushes) are not drawn and do not count.

MM9 had no camera collision and its cameras were placed on its own geometry; a few sit in a wall or behind a slope
where the view still read, and the remade maps differ in places. A camera that fails is moved minimally: first along
its own view axis (forward, then back), then to the nearest valid point of a small search around it; each move is
recorded in the shot's note and returned. One that cannot be fixed is an error (`apply(..., strict=True)`, the
conversion's install) unless the scene lists it in its gate overrides with a reason.

    python3 camera_gate.py <stem> [--root ROOT]      # checks ROOT/worlds/mm9/maps/<stem>.cinematics.yml as installed
"""

from __future__ import annotations

import base64
import json
import math
import struct
import sys
from pathlib import Path

import numpy as np
import yaml

COMMON = Path(__file__).resolve().parent
ROOT = COMMON.parents[2]
sys.path.insert(0, str(ROOT))

CLEARANCE = 16.0
FACING_CLEAR = 96.0
HALF_VIEW = math.radians(45.0)
SAMPLE_SECONDS = 0.25
FACE_INVISIBLE = 0x00002000
MAX_NUDGE = 768.0


def _directions():
    golden = math.pi * (3.0 - math.sqrt(5.0))
    out = []
    for k in range(14):
        z = 1.0 - 2.0 * (k + 0.5) / 14
        r = math.sqrt(max(0.0, 1.0 - z * z))
        out.append((math.cos(golden * k) * r, math.sin(golden * k) * r, z))
    return np.array(out)


RAY_DIRECTIONS = _directions()


class Geometry:
    """The drawn faces of a compiled BLV as triangles with their faces' normals."""

    def __init__(self, blv_path: Path):
        from util.map_export import parse_blv_file
        blv = parse_blv_file(Path(blv_path))["payload"]
        vertices = np.array([(v["x"], v["y"], v["z"]) for v in blv["vertices"]], float)
        a, b, c, normals = [], [], [], []
        for face in blv["faces"]:
            if face["is_portal"] or int(face["attributes"]) & FACE_INVISIBLE:
                continue
            indices = face["vertex_indices"]
            if len(indices) < 3:
                continue
            header = base64.b64decode(face["raw_header_base64"])
            normal = np.array(struct.unpack_from("<3f", header, 0), float)
            points = vertices[indices]
            if not np.isfinite(normal).all() or np.linalg.norm(normal) < 0.5:
                normal = np.cross(points[1] - points[0], points[2] - points[0])
                normal /= max(np.linalg.norm(normal), 1e-9)
            for k in range(1, len(indices) - 1):
                a.append(points[0])
                b.append(points[k])
                c.append(points[k + 1])
                normals.append(normal)
        self.a, self.b, self.c = np.array(a), np.array(b), np.array(c)
        self.normals = np.array(normals)
        self.e1, self.e2 = self.b - self.a, self.c - self.a
        # the ray test's terms that depend only on the direction (kept for the fixed RAY_DIRECTIONS every inside()
        # casts) or only on the origin (kept for the last origin: inside() casts 14 rays from one point); the same
        # arithmetic as computing them per ray (the gate cast 14 000 rays on Thronheim City: a minute)
        self._fixed = {np.asarray(direction, float).tobytes() for direction in RAY_DIRECTIONS}
        self._direction_cache = {}
        self._origin_cache = (None, None)

    def _direction_terms(self, direction: np.ndarray):
        key = direction.tobytes()
        terms = self._direction_cache.get(key)
        if terms is None:
            p = np.cross(direction, self.e2)
            det = np.einsum("ij,ij->i", self.e1, p)
            ok = np.abs(det) > 1e-9
            inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
            terms = (p, ok, inv)
            if key in self._fixed:
                self._direction_cache[key] = terms
        return terms

    def _origin_terms(self, origin: np.ndarray):
        key = origin.tobytes()
        if self._origin_cache[0] != key:
            t_vec = origin - self.a
            q = np.cross(t_vec, self.e1)
            self._origin_cache = (key, (t_vec, q, np.einsum("ij,ij->i", self.e2, q)))
        return self._origin_cache[1]

    def ray(self, origin, direction, max_distance=1e9):
        """The first drawn triangle along the ray: (distance, its face normal) or (None, None)."""
        origin = np.asarray(origin, float)
        direction = np.asarray(direction, float)
        p, ok, inv = self._direction_terms(direction)
        t_vec, q, t_numerator = self._origin_terms(origin)
        u = np.einsum("ij,ij->i", t_vec, p) * inv
        v = (q @ direction) * inv
        t = t_numerator * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-3) & (t < max_distance)
        if not hit.any():
            return None, None
        index = np.where(hit)[0][np.argmin(t[hit])]
        return float(t[index]), self.normals[index]

    def distance(self, point) -> float:
        """The distance from point to the nearest drawn triangle."""
        p = np.asarray(point, float)
        np.seterr(divide="ignore", invalid="ignore")
        # Closest point on each triangle (Ericson, Real-Time Collision Detection 5.1.5), vectorised.
        a, b, c = self.a, self.b, self.c
        ab, ac, ap = b - a, c - a, p - a
        d1, d2 = np.einsum("ij,ij->i", ab, ap), np.einsum("ij,ij->i", ac, ap)
        bp, cp = p - b, p - c
        d3, d4 = np.einsum("ij,ij->i", ab, bp), np.einsum("ij,ij->i", ac, bp)
        d5, d6 = np.einsum("ij,ij->i", ab, cp), np.einsum("ij,ij->i", ac, cp)
        va = d3 * d6 - d5 * d4
        vb = d5 * d2 - d1 * d6
        vc = d1 * d4 - d3 * d2
        denom = np.maximum(va + vb + vc, 1e-12)
        v = vb / denom
        w = vc / denom
        closest = a + ab * v[:, None] + ac * w[:, None]
        # Regions outside the face: clamp to the vertices and edges.
        conds = [
            ((d1 <= 0) & (d2 <= 0), a),
            ((d3 >= 0) & (d4 <= d3), b),
            ((d6 >= 0) & (d5 <= d6), c),
        ]
        for mask, point_on in conds:
            closest[mask] = point_on[mask]
        edge_ab = (vc <= 0) & (d1 >= 0) & (d3 <= 0)
        t = np.where(edge_ab, d1 / np.where(edge_ab, d1 - d3, 1.0), 0.0)
        closest[edge_ab] = (a + ab * t[:, None])[edge_ab]
        edge_ac = (vb <= 0) & (d2 >= 0) & (d6 <= 0)
        t = np.where(edge_ac, d2 / np.where(edge_ac, d2 - d6, 1.0), 0.0)
        closest[edge_ac] = (a + ac * t[:, None])[edge_ac]
        edge_bc = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0)
        t = np.where(edge_bc, (d4 - d3) / np.where(edge_bc, (d4 - d3) + (d5 - d6), 1.0), 0.0)
        closest[edge_bc] = (b + (c - b) * t[:, None])[edge_bc]
        return float(np.sqrt(((closest - p) ** 2).sum(1)).min())

    def inside(self, point) -> str | None:
        """None when the point is inside the map, else why not."""
        escaped = behind = 0
        for direction in RAY_DIRECTIONS:
            distance, normal = self.ray(point, direction)
            if distance is None:
                # Up is open sky over an outdoor room (cities, regions); level or down it is the void.
                escaped += 0 if direction[2] > 0.15 else 1
            elif float(np.dot(normal, direction)) > 0:
                behind += 1
        if escaped > 1:
            return f"outside the map ({escaped} level or downward rays meet nothing)"
        if behind > 4:
            return f"inside solid geometry ({behind} of 14 rays meet a face from behind)"
        return None

    def clear(self, eye, target) -> bool:
        eye, target = np.asarray(eye, float), np.asarray(target, float)
        delta = target - eye
        length = float(np.linalg.norm(delta))
        if length < 1e-6:
            return True
        distance, _ = self.ray(eye, delta / length, max(0.0, length - 32.0))
        return distance is None


def _norm(v):
    v = np.asarray(v, float)
    length = np.linalg.norm(v)
    return v / length if length > 1e-9 else None


class Targets:
    """Where a key's aim points: actors' centres from the map's scene (initial_state actors)."""

    def __init__(self, scene_path: Path | None):
        self.actors = {}
        if scene_path is not None and Path(scene_path).is_file():
            text = Path(scene_path).read_text()
            try:
                scene = json.loads(text)
            except ValueError:
                scene = yaml.load(text, Loader=yaml.CSafeLoader)
            for actor in (scene.get("initial_state") or {}).get("actors") or []:
                p = actor.get("position") or {}
                height = float(actor.get("height") or 160)
                index = actor.get("actor_index", len(self.actors))
                self.actors[int(index)] = np.array([p.get("x", 0), p.get("y", 0), p.get("z", 0) + height * 0.75],
                                                   float)

    def of(self, key: dict):
        if "look_at" in key:
            return np.array(key["look_at"], float)
        if "look_at_actor" in key:
            return self.actors.get(int(key["look_at_actor"]))
        return None


def _key_at(shot: dict, local: float):
    """The eye, aim key pair and blend of a moving shot at local seconds."""
    keys = shot["keys"]
    k = 0
    while k + 1 < len(keys) and keys[k + 1]["at"] <= local:
        k += 1
    j = min(k + 1, len(keys) - 1)
    t = 0.0 if j == k else (local - keys[k]["at"]) / max(keys[j]["at"] - keys[k]["at"], 1e-9)
    t = min(max(t, 0.0), 1.0)
    if shot.get("easing", "smooth") == "smooth":
        t = t * t * (3 - 2 * t)
    eye = np.array(keys[k]["position"], float) * (1 - t) + np.array(keys[j]["position"], float) * t
    return eye, keys[k], keys[j], t


class Gate:
    def __init__(self, geometry: Geometry, targets: Targets):
        self.geometry = geometry
        self.targets = targets

    def problems_at(self, eye, key: dict, forward=None) -> list[str]:
        eye = np.asarray(eye, float)
        problems = []
        where = self.geometry.inside(eye)
        if where:
            return [where]
        clearance = self.geometry.distance(eye)
        if clearance < CLEARANCE:
            problems.append(f"{clearance:.0f} units from a face (needs {CLEARANCE:.0f})")
        target = self.targets.of(key)
        if target is not None:
            to_target = _norm(target - eye)
            axis = forward if forward is not None else to_target
            if to_target is not None and axis is not None and math.acos(
                    max(-1.0, min(1.0, float(np.dot(axis, to_target))))) > HALF_VIEW:
                problems.append("its target is outside the view")
            if not self.geometry.clear(eye, target):
                problems.append("a face hides its target")
        elif "direction" in key:
            distance, _ = self.geometry.ray(eye, _norm(key["direction"]))
            if distance is not None and distance < FACING_CLEAR:
                problems.append(f"looks into a face {distance:.0f} units ahead")
        return problems

    def check_shot(self, shot: dict) -> list[str]:
        if shot.get("party"):
            return []
        if "keys" not in shot:
            return self.problems_at(shot["position"], shot)
        problems = []
        steps = max(1, int(math.ceil(shot["duration"] / SAMPLE_SECONDS)))
        for s in range(steps + 1):
            local = min(shot["duration"], s * SAMPLE_SECONDS)
            eye, a, b, t = _key_at(shot, local)
            key = a if t < 0.5 else b
            forward = None
            if "direction" in a and "direction" in b:
                forward = _norm(np.array(a["direction"]) * (1 - t) + np.array(b["direction"]) * t)
            for problem in self.problems_at(eye, key, forward):
                problems.append(f"at {local:.2f} s: {problem}")
        return problems

    def nudge(self, position, key: dict):
        """The nearest valid eye: along the view axis first, then a search around; (point, how) or (None, None)."""
        position = np.asarray(position, float)
        target = self.targets.of(key)
        axis = _norm(target - position) if target is not None else (
            _norm(key["direction"]) if "direction" in key else None)
        if axis is not None:
            for distance in np.arange(16.0, MAX_NUDGE + 1, 16.0):
                for sign, name in ((1, "forward"), (-1, "back")):
                    candidate = position + axis * distance * sign
                    if not self.problems_at(candidate, key):
                        return candidate, f"moved {distance:.0f} {name} along its view"
        for radius in (32.0, 64.0, 128.0, 256.0):
            for direction in RAY_DIRECTIONS:
                candidate = position + direction * radius
                if not self.problems_at(candidate, key):
                    return candidate, f"moved {radius:.0f} to the nearest clear point"
        return None, None


def _shift_path(gate: Gate, shot: dict) -> str | None:
    original = [list(key["position"]) for key in shot["keys"]]
    axis = _norm(np.mean([_norm(k["direction"]) for k in shot["keys"] if "direction" in k] or [[0, 0, 0]], axis=0))
    offsets = [(np.array([0.0, 0.0, d]), f"{d:.0f} up") for d in np.arange(16.0, 513.0, 16.0)]
    if axis is not None:
        offsets += [(axis * d * sign, f"{d:.0f} {name} along its view") for d in np.arange(16.0, 513.0, 16.0)
                    for sign, name in ((1, "forward"), (-1, "back"))]
    for offset, how in offsets:
        for key, position in zip(shot["keys"], original):
            key["position"] = [round(float(x), 1) for x in np.array(position) + offset]
        if not gate.check_shot(shot):
            return f"path moved {how}"
    for key, position in zip(shot["keys"], original):
        key["position"] = position
    return None


def apply(cinematics: list, blv_path: Path, scene_path: Path | None = None, overrides: dict | None = None,
          strict: bool = False, label: str = "") -> list[str]:
    """Checks (and where needed moves) every camera of the cinematics (cinematics.Cinematic objects) against the
    BLV. Returns the report lines (moves and remaining failures). strict: a remaining failure that overrides does
    not name ("<cinematic id> shot <n>": reason) raises."""
    gate = Gate(Geometry(blv_path), Targets(scene_path))
    overrides = overrides or {}
    report, errors = [], []
    for cinema in cinematics:
        for number, shot in enumerate(cinema.shots, 1):
            name = f"{cinema.id} shot {number}"
            problems = gate.check_shot(shot)
            if not problems:
                continue
            keys = shot["keys"] if "keys" in shot else [shot]
            moves = []
            for key in keys:
                if gate.problems_at(key["position"], key):
                    point, how = gate.nudge(key["position"], key)
                    if point is not None:
                        moves.append(f"{how} ({key['position']} -> {[round(float(x), 1) for x in point]})")
                        key["position"] = [round(float(x), 1) for x in point]
            if "keys" in shot and gate.check_shot(shot):
                # A path that runs through solid between valid keys: the whole path shifted, up first, then along.
                shifted = _shift_path(gate, shot)
                if shifted:
                    moves.append(shifted)
            if moves:
                note = "gate: " + "; ".join(moves)
                shot["note"] = (shot.get("note", "") + "; " + note).lstrip("; ")
                report.append(f"{label}{name}: {note}")
            remaining = gate.check_shot(shot)
            if remaining:
                line = f"{label}{name}: " + "; ".join(remaining[:3]) + (" ..." if len(remaining) > 3 else "")
                if name in overrides:
                    report.append(line + f" (override: {overrides[name]})")
                else:
                    report.append(line)
                    errors.append(line)
    if strict and errors:
        raise ValueError("cinematic cameras fail the gate (add a reasoned override or fix them):\n  "
                         + "\n  ".join(errors))
    return report


def gate_installed(stem: str, yml: Path, blv: Path, scene: Path | None, overrides: dict | None,
                   strict: bool) -> list[str]:
    """The gate over an installed <stem>.cinematics.yml: cameras moved where needed are written back into it."""
    cinemas = _from_yaml(yml)
    report = apply(cinemas, blv, scene, overrides, strict=strict, label=f"{stem} ")
    if any(": gate:" in line for line in report):
        data = yaml.safe_load(Path(yml).read_text())
        for cinema in cinemas:
            data["cinematics"][cinema.id]["shots"] = cinema.shots
        sys.path.insert(0, str(COMMON))
        import cinematics as cinematics_module
        rebuilt = []
        for cinematic_id, body in data["cinematics"].items():
            cinema = cinematics_module.Cinematic(cinematic_id, source=body.get("source", ""),
                                                 skippable=body.get("skippable", True),
                                                 letterbox=body.get("letterbox", True),
                                                 ambient=body.get("ambient", False))
            cinema.shots = body.get("shots") or []
            cinema.cues = body.get("cues") or []
            cinema.letterbox_seconds = body.get("letterbox_seconds")
            rebuilt.append(cinema)
        text = cinematics_module.to_yaml(rebuilt, source=data.get("source", ""))
        Path(yml).write_text(text) if not Path(yml).is_symlink() else None
        return report + [f"{stem}: moved cameras written to {yml}"]
    return report


def _from_yaml(path: Path) -> list:
    """The cinematics of an installed .cinematics.yml as Cinematic-like objects."""
    sys.path.insert(0, str(COMMON))
    import cinematics as cinematics_module
    data = yaml.safe_load(Path(path).read_text())
    out = []
    for cinematic_id, body in (data.get("cinematics") or {}).items():
        cinema = cinematics_module.Cinematic(cinematic_id)
        cinema.shots = body.get("shots") or []
        out.append(cinema)
    return out


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("stems", nargs="+")
    parser.add_argument("--root", type=Path, default=ROOT / "output/mm9_rework/cinematics_pilot_root")
    parser.add_argument("--write", action="store_true",
                        help="move failing cameras in the files (with the projects' overrides.yml cinematics_gate)")
    args = parser.parse_args()
    failures = 0
    for stem in args.stems:
        maps = args.root / "worlds/mm9/maps"
        yml = maps / f"{stem}.cinematics.yml"
        if not yml.is_file():
            print(f"{stem}: no cinematics")
            continue
        overrides = {}
        for project in (COMMON.parent / f"mm9r_{stem}" / "overrides.yml", COMMON.parent / f"mm9r_{stem}_blv" / "overrides.yml"):
            if project.is_file():
                overrides = (yaml.safe_load(project.read_text()) or {}).get("cinematics_gate") or overrides
        if args.write:
            report = gate_installed(stem, yml, maps / f"{stem}.blv", maps / f"{stem}.scene.yml", overrides, False)
            cinemas = _from_yaml(yml)
        else:
            cinemas = _from_yaml(yml)
            report = apply(cinemas, maps / f"{stem}.blv", maps / f"{stem}.scene.yml", overrides, label=f"{stem} ")
        shots = sum(len(c.shots) for c in cinemas)
        bad = [line for line in report if not line.split(": ", 1)[1].startswith("gate:")
               and "(override:" not in line and "moved cameras written" not in line]
        failures += len(bad)
        print(f"{stem}: {len(cinemas)} cinematics, {shots} shots, {len(report)} reported")
        for line in report:
            print("  " + line)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
