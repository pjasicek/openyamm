#!/usr/bin/env python3
"""
What MM9 has at a real screenshot's view (2026-10-31 measurements, devdocs/mm9_rework/overnight/real_mm9/MEASUREMENTS.md):
for each shot of one of our tour YAMLs, read only, nothing written but the report:

- WorldInfo's string (AmbientLight, LMGridSize) and WorldProperties (LightScale, PlayerLightOn, DynamicLightDist);
- the MM9 light sources near the eye: `Light`, `DirLight`, `ObjectLight`, `StaticSunLight` (LightRadius, LightColor,
  BrightScale), `Fire` (LightMin/MaxRadius, LightColor1/2: dynamic flicker), `CandleProp`/torches (dynamic; no radius
  in the DAT, the class's defaults apply) and any other object with a LightRadius, nearest first, with whether the eye
  is inside the radius;
- MM9's static frame predicted from its own data: rays through the real shot's box (x 20-78 %, y 5-88 % of MM9's
  frame, assumed 90 degrees across a 4:3 frame: real_shots.py `ours_frac`; no HUD mask), each hit on the nearest DAT polygon (every world model,
  invisible surfaces skipped), the DTX texel there (the import's bitmap, sampled at MM9's surface mapping) times the
  DAT lightmap texel there (x1, MM9_RENDER_LIGHTING_RE.md). Means over the crop and over its upper, middle and lower
  thirds, by surface kind (floor, wall, ceiling) and by texture. Polygons without a lightmap (MM9 vertex-lights world
  models) are counted apart and left out of the prediction; MM9's models/props/actors are not in it.

    python3 level_generation/projects/mm9r_common/real_context.py level_generation/projects/mm9r_<map> TOUR.yml \
        [--shots name,name] [--grid 64x48] [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dungeon.geometry import newell, poly_ring  # noqa: E402
from dungeon.source import ROOT, SCALE, Project, Source  # noqa: E402
from real_shots import ours_frac  # noqa: E402
from transcode_mm9_dat_to_odm import adjusted_lightmap_origin, lightmap_basis  # noqa: E402

EYE_HEIGHT = 160.0                     # IndoorMovementController eyeHeight, native units
VFOV = math.radians(60.0)
ASPECT = 16 / 9
WEIGHTS = np.array([0.2126, 0.7152, 0.0722])
LIGHT_CLASSES = ("Light", "DirLight", "ObjectLight", "StaticSunLight", "Fire", "CandleProp", "Torch", "FlickerLight")


class DatScene:
    def __init__(self, project: Project):
        self.source = Source(project)
        self.world = self.source.world
        self.grid = float(self.world.world_info.light_map_grid_size) or 32.0
        self.textures: dict[str, np.ndarray | None] = {}
        tris, owner = [], []
        self.polys = []
        for model in self.world.world_models:
            if model.name.startswith(("AITrk", "VisBSP")):
                continue
            for poly in model.polies:
                ring = poly_ring(poly)
                if len(ring) < 3:
                    continue
                surface = model.surfaces[poly.surface_index]
                texture = model.textures[surface.texture_index]
                if surface.flags & 0x4 or Path(texture.replace("\\", "/")).stem.lower() == "invisible":
                    continue
                points = np.array([model.points[i] for i in ring], float)
                index = len(self.polys)
                self.polys.append((model, poly, surface, texture, points))
                for i in range(1, len(points) - 1):
                    tris.append((points[0], points[i], points[i + 1]))
                    owner.append(index)
        tris = np.array(tris, float)
        self.a, self.e1, self.e2 = tris[:, 0], tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]
        self.owner = np.array(owner)

    def cast(self, origin: np.ndarray, directions: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Nearest hit (polygon index, distance) per ray, -1 when none."""
        near = np.linalg.norm(self.a - origin, axis=1) < 12000
        a, e1, e2, own = self.a[near], self.e1[near], self.e2[near], self.owner[near]
        hits, dists = np.full(len(directions), -1), np.full(len(directions), np.inf)
        s = origin - a
        q = np.cross(s, e1)
        for k, d in enumerate(directions):
            p = np.cross(d, e2)
            det = (e1 * p).sum(1)
            with np.errstate(divide="ignore", invalid="ignore"):
                inv = 1.0 / det
                u = (s * p).sum(1) * inv
                v = (q @ d) * inv
                t = (e2 * q).sum(1) * inv
            ok = (np.abs(det) > 1e-9) & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1.0)
            if ok.any():
                j = np.argmin(np.where(ok, t, np.inf))
                hits[k], dists[k] = own[j], t[j]
        return hits, dists

    def texture_rgb(self, texture: str) -> np.ndarray | None:
        key = texture.lower()
        if key not in self.textures:
            entry = self.source.aliases.get(key)
            image = None
            if entry and entry.get("emitted_bitmap"):
                path = (ROOT / "assets_editor_dev/worlds/mm9/maps" / entry["emitted_bitmap"]).resolve()
                if path.exists():
                    image = np.asarray(Image.open(path).convert("RGB"), float)
            self.textures[key] = image
        return self.textures[key]

    def texel(self, index: int, point: np.ndarray) -> np.ndarray | None:
        model, poly, surface, texture, points = self.polys[index]
        image = self.texture_rgb(texture)
        if image is None:
            return None
        u = (point - np.array(surface.uv_origin)) @ np.array(surface.uv_u)
        v = (point - np.array(surface.uv_origin)) @ np.array(surface.uv_v)
        entry = self.source.aliases[texture.lower()]
        w, h = entry["width"], entry["height"]
        x = int(math.floor(u)) % w * image.shape[1] // w
        y = int(math.floor(v)) % h * image.shape[0] // h
        return image[y, x]

    def lightmap(self, index: int, point: np.ndarray) -> np.ndarray | None:
        """The DAT lightmap texel (0-1 RGB) at a point of the polygon, with the import's lightmap mapping."""
        model, poly, surface, texture, points = self.polys[index]
        pixels = poly.lightmap_pixels_bgra
        if not pixels or poly.lightmap_width <= 0 or poly.lightmap_height <= 0:
            return None
        source = [np.array(model.points[d.vertex_index], float) for d in poly.disk_verts]
        normal = None
        for p in source[2:]:
            n = np.cross(source[1] - source[0], p - source[0])
            if np.linalg.norm(n) > 1e-9:
                normal = n / np.linalg.norm(n)
                break
        if normal is None:
            return None
        axis_u, axis_v = (np.array(x, float) for x in lightmap_basis(tuple(normal)))
        unit_u, unit_v = axis_u / np.linalg.norm(axis_u), axis_v / np.linalg.norm(axis_v)
        origin = source[0].copy()
        for p in source:
            du = unit_u @ (p - origin)
            if du < 0:
                origin = origin + unit_u * du
            dv = unit_v @ (p - origin)
            if dv < 0:
                origin = origin + unit_v * dv
        origin = np.array(adjusted_lightmap_origin(tuple(origin), tuple(axis_u), self.grid))
        origin = np.array(adjusted_lightmap_origin(tuple(origin), tuple(axis_v), self.grid))
        pu = (point - origin) @ axis_u / self.grid + 0.5
        pv = (point - origin) @ axis_v / self.grid + 0.5
        w, h = poly.lightmap_width, poly.lightmap_height
        col = int(np.clip(math.floor(w - pu), 0, w - 1))
        row = int(np.clip(math.floor(pv), 0, h - 1))
        value = pixels[row * w + col]
        return np.array([(value >> 16) & 255, (value >> 8) & 255, value & 255], float) / 255


def world_settings(source: Source) -> dict:
    info = source.world.world_info.properties
    out = {"WorldInfo": info.strip()}
    for o in source.objects:
        if o["class"] == "WorldProperties":
            p = o["properties"]
            out["WorldProperties"] = {k: p.get(k) for k in ("LightScale", "NightLightScale", "PlayerLightOn",
                                                            "DynamicLightDist", "EnableFog", "FogColor") if k in p}
    match = re.search(r"ambientlight\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", info, re.I)
    out["AmbientLight"] = [float(v) for v in match.groups()] if match else None
    return out


def nearby_lights(source: Source, eye: np.ndarray, count: int = 10) -> list[dict]:
    found = []
    for o in source.objects:
        p = o["properties"]
        if o["class"] not in LIGHT_CLASSES and "LightRadius" not in p and "LightMaxRadius" not in p:
            continue
        if "Pos" not in p:
            continue
        distance = float(np.linalg.norm(np.array(p["Pos"], float) - eye))
        radius = p.get("LightRadius", p.get("LightMaxRadius"))
        colour = p.get("LightColor", p.get("LightColor1"))
        found.append({"class": o["class"], "name": o["name"], "distance": round(distance),
                      "radius": None if radius is None else round(float(radius)),
                      "colour": None if colour is None else [round(float(c)) for c in colour],
                      "bright_scale": None if "BrightScale" not in p else round(float(p["BrightScale"]), 2),
                      "inside": None if radius is None else bool(distance < float(radius)),
                      "extra": {k: p[k] for k in ("StartOn", "Blue", "FOV", "LightMinRadius") if k in p}})
    found.sort(key=lambda x: x["distance"])
    # nearest `count`, plus every light whose radius reaches the eye
    return [f for k, f in enumerate(found) if k < count or f["inside"]]


def kind(normal: np.ndarray) -> str:
    return "floor" if normal[1] > 0.7 else ("ceiling" if normal[1] < -0.7 else "wall")


def predict(scene: DatScene, project: Project, shot: dict, grid: tuple[int, int]) -> dict:
    x, y, z = shot["position"]
    eye_native = np.array([x, y, z - 1 + EYE_HEIGHT], float)
    eye = project.lt_from_native(eye_native)
    yaw, pitch = shot["yaw"], shot["pitch"]
    fwd = np.array([math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch)])
    right = np.array([math.sin(yaw), -math.cos(yaw), 0.0])
    up = np.cross(right, fwd)
    tan_v = math.tan(VFOV / 2)
    tan_h = tan_v * ASPECT
    nx, ny = grid
    rx = 0.20 + (np.arange(nx) + 0.5) / nx * (0.78 - 0.20)
    ry = 0.05 + (np.arange(ny) + 0.5) / ny * (0.88 - 0.05)
    RX, RY = np.meshgrid(rx, ry)
    SX, SY = ours_frac(RX, RY)
    keep = np.ones(SX.shape, bool)
    band = np.minimum(((RY - 0.05) / 0.83 * 3).astype(int), 2)
    dirs_native = (fwd[None, None] + ((2 * SX - 1) * tan_h)[..., None] * right
                   + ((1 - 2 * SY) * tan_v)[..., None] * up)
    dirs_native /= np.linalg.norm(dirs_native, axis=-1, keepdims=True)
    dirs = dirs_native[..., [0, 2, 1]][keep]
    bands = band[keep]
    hits, dists = scene.cast(eye, dirs)
    rows = []
    for k, (h, d) in enumerate(zip(hits, dists)):
        if h < 0:
            rows.append(None)
            continue
        point = eye + dirs[k] * d
        model, poly, surface, texture, points = scene.polys[h]
        n = newell(points)
        n = n / (np.linalg.norm(n) or 1)
        rows.append({"band": int(bands[k]), "kind": kind(n), "texture": Path(texture.replace("\\", "/")).stem,
                     "model": model.name, "tex": scene.texel(h, point), "lm": scene.lightmap(h, point),
                     "distance": float(d)})
    return {"eye_lt": eye.round(1).tolist(), "rows": rows}


def summarise(rows: list) -> dict:
    lit = [r for r in rows if r and r["lm"] is not None and r["tex"] is not None]
    if not lit:
        return {"n": 0}
    tex = np.array([r["tex"] for r in lit])
    lm = np.array([r["lm"] for r in lit])
    pred = tex * lm
    return {"n": len(lit), "pred_luma": round(float(pred.mean(0) @ WEIGHTS), 1),
            "pred_median": round(float(np.median(pred @ WEIGHTS)), 1),
            "pred_rgb": pred.mean(0).round(0).astype(int).tolist(),
            "lm_rgb": (lm.mean(0) * 255).round(0).astype(int).tolist(),
            "lm_luma": round(float(lm.mean(0) @ WEIGHTS * 255), 1),
            "tex_luma": round(float(tex.mean(0) @ WEIGHTS), 1),
            "tex_rgb": tex.mean(0).round(0).astype(int).tolist()}


def report(name: str, data: dict) -> dict:
    rows = data["rows"]
    total = len(rows)
    out = {"shot": name, "eye_lt": data["eye_lt"], "rays": total,
           "no_hit": sum(r is None for r in rows),
           "no_lightmap": sum(1 for r in rows if r and r["lm"] is None),
           "all": summarise(rows),
           "bands": {b: summarise([r for r in rows if r and r["band"] == k])
                     for k, b in enumerate(("upper", "middle", "lower"))},
           "kinds": {}, "textures": {}, "unlit_models": {}}
    for kd in ("floor", "wall", "ceiling"):
        part = [r for r in rows if r and r["kind"] == kd]
        if part:
            out["kinds"][kd] = dict(summarise(part), share=round(len(part) / total, 2))
    textures = {}
    for r in rows:
        if r:
            textures.setdefault(r["texture"], []).append(r)
    for t, part in sorted(textures.items(), key=lambda kv: -len(kv[1]))[:5]:
        out["textures"][t] = dict(summarise(part), share=round(len(part) / total, 2))
    for r in rows:
        if r and r["lm"] is None:
            out["unlit_models"][r["model"]] = out["unlit_models"].get(r["model"], 0) + 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project", type=Path)
    ap.add_argument("tour", type=Path)
    ap.add_argument("--shots", default="")
    ap.add_argument("--grid", default="64x48")
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    project = Project.load(args.project, install=False)
    scene = DatScene(project)
    tour = yaml.safe_load(args.tour.read_text())
    wanted = set(args.shots.split(",")) if args.shots else None
    grid = tuple(int(v) for v in args.grid.split("x"))
    result = {"map": project.stem, "settings": world_settings(scene.source), "shots": []}
    print(json.dumps(result["settings"]))
    for shot in tour["shots"]:
        if wanted and shot["name"] not in wanted:
            continue
        data = predict(scene, project, shot, grid)
        rep = report(shot["name"], data)
        rep["lights"] = nearby_lights(scene.source, np.array(data["eye_lt"]))
        result["shots"].append(rep)
        print(f"\n== {shot['name']} eye LT {rep['eye_lt']}  rays {rep['rays']} no hit {rep['no_hit']} "
              f"no lightmap {rep['no_lightmap']} {rep['unlit_models']}")
        print("  all   ", rep["all"])
        for b, s in rep["bands"].items():
            print(f"  {b:7s}", s)
        for kd, s in rep["kinds"].items():
            print(f"  {kd:7s}", s)
        for t, s in rep["textures"].items():
            print(f"  tex {t}", s)
        for light in rep["lights"]:
            print("  light", light)
    if args.json:
        args.json.write_text(json.dumps(result, indent=1, default=float) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
