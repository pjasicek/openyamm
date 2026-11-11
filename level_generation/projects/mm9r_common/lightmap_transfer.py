#!/usr/bin/env python3
"""
MM9's own DAT lightmaps as the static light of a rebuilt MM9 dungeon (devdocs/mm9_rework/MM9_LIGHTMAP_TRANSFER.md).
One command per map:

    python3 level_generation/projects/mm9r_common/lightmap_transfer.py level_generation/projects/mm9r_<map> --install
    python3 level_generation/projects/mm9r_common/lightmap_transfer.py <project> --cycles-only --install   # revert
    python3 level_generation/projects/mm9r_common/lightmap_transfer.py <project> --backup      # once, before anything
    python3 level_generation/projects/mm9r_common/lightmap_transfer.py <project> --measure     # MM9's resolution only

**Base.** The map's Cycles bake in output/mm9_rework/bakes/<stem>/ (`<stem>.lighting`, `scene.json`, `<stem>.bake.json`,
from dungeon/lighting.py) gives the atlas, the charts and per-face page maps, the fallback texels and the per-sector
actor ambient. When the installed BLV is not the one baked (a rebuild that removed invisible faces), the base is carried
over: the current scene is exported from the game (`--headless-export-indoor-bake-scene`) and every charted face of the
bake is matched to the current face with the same texture, mover flag and vertices (stored pose for a mover); a drawn
face of the current BLV without a match has no lightmap (vertex-lit, listed in the report) and a large number of them
means: bake again (dungeon/lighting.py) and rerun this.

**Transfer.** For every texel of a chart: its world position on the chart's plane, the coplanar DAT polygons of any
world model (same facing, plane within PLANE_TOLERANCE LT at the chart's centre) that contain it, and a bilinear sample
of the most-inside one's lightmap; chart texels outside our faces (padding) take the nearest coplanar polygon within
OUTSIDE_REACH, clamped, as MM9's own filter does at a polygon's edge. MM9's lightmap frame (LithTech
`lightmap_planes.cpp`, `CPrePoly::FindTextureOrigin`, `ApplyLightsToPoly`): N the ring normal, P = N x Q0, Q = P x N, Q0
the down vector of the principal plane N faces most, the origin pulled back to cover the ring and snapped to the grid,
texel (x, y) at O + (P x + Q y) G / |P|^2, columns stored backwards (W-1-x). G is the world's `LMGridSize` (the DAT's
default 20 where the WorldInfo string has none) for every polygon: the stored sizes fit it on 95-99.4 % of the polygons
of every map, and the rest fit no single other grid.

**Encoding** `display` (default): stored value = byte / 255, our shader's `texture * lighting` then shows exactly MM9's
`texture * lightmap` (devdocs/mm9_rework/MM9_LIGHTING_GLOBAL_MODEL.md). `linear` ((byte/255)^2.2) is for comparison.

**World models** (doors, movers, destructible brushes) use their own lightmaps in the same frame: LithTech's preprocessor
lights them in world space (`CLightMapMaker::SetupWorldModels` leaves `m_bUsingTransform` false), and their stored values
follow their ring normal as the PhysicsBSP's do (unshadowed prediction from MM9's Light and DirLight objects against the
reversed normal: Lich Lab rotating doors 317:7, Yanmir's Fort movers 283:76, PhysicsBSP 464:121). Yanmir's dark basement
planks are MM9's own light: Planks0 bridges a pit with no floor under it, lit cyan from below (undersides, inner sides
and the ceiling above the gap 253-255), while no light object reaches the room over it (tops 33,33,41, the
AmbientLight 35,35,40). overrides.yml `map: {lightmap_fallback_models: [...]}` sends a model's texels to the fallback
should a map ever need it (none does).

**Fallback.** A texel of our faces with no MM9 polygon (restored holes, welds, our own faces, the flagged models) keeps
the Cycles bake scaled per chart, per channel, to the transferred texels around it: the ratio MM9 / bake over the
transferred texels in 64-LT voxels within 128 LT of the chart facing the same principal direction (any direction when
too few; 512 LT when none), clamped to 0.1-4. No per-map factor. Emitter charts (sky faces, lit panes: the bake's
profile `emitters`) keep their display value. A chart with no MM9 lightmap within 128 LT next to charts left vertex-lit
(MM9 lit its polygons per vertex) is vertex-lit too, not the layout's grey scaled from afar: Drangheim City, whose DAT
has 56 lightmapped polygons of 12 814, had 427 such charts of roofs and towers (2026-11-07). `coverage_core` is the
transferred share of the lightmapped charts' texels (none when there are none: Mountain Pass, terrain only) and
`lightmapped_share` their share of all charted texels.

**Dark rooms option** `--min-light V` (or overrides.yml `map: {lightmap_min_light: V}`; default 0, off): a floor under
every texel, the stand-in for a player light. MM9's PlayerLightOn is a grey light of radius 36 LT with no visible effect
(MM9_LIGHTING_GLOBAL_MODEL.md 1.1), so the default keeps MM9's dark rooms as dark as MM9 draws them.

**Daylight pages** (a map whose scene has a `daylight` block: the cities and regions open to the sky; display
encoding). MM9's lightmaps hold its AmbientLight, its StaticSunLight (with shadows) and its lamps in one value, which
showed noon at midnight in our streets. The sidecar is then version 2 (devdocs/INDOOR_BAKED_LIGHTING.md "Daylight
pages"): per page, the open air's share D and the rest (lamps, interiors), V = rest + D. Per texel and channel, the lamps
are predicted as MM9's preprocessor lights them, unshadowed (LithTech LightMapMaker CalcLightSample: Light and DirLight
colour x BrightScale, the quartic window, N.L, a DirLight's cone; on MM9's own shaded faces the prediction matches the
lightmap's light over the ambient at a median ratio of 1.01, Sturmford City), and D = clamp(V - lamps, min(A, V),
min(V, A + sun x clamp(gain x N.L))): the ambient A is always the sky's, the sun's share never exceeds an unshadowed sun
(gain MM9_SUN_GAIN; none without a StaticSunLight, so a face turned away from the sun keeps only A), and a texel MM9 lit
past saturation keeps its predicted lamps. The renderer scales D by the hour on the faces of sectors open to the sky.

**Actor ambient** (the sector records) stays the bake's: actors, decorations and items keep their existing lighting path.

**Recipe and staleness.** The installed `<stem>.bake.json` is the transfer's recipe: tool hash, DAT path and hash,
encoding, parameters, the fallback models and the base bake's own Cycles recipe (embedded). The sidecar records the BLV,
its scene file, that recipe and the base bake's texture dependencies (the fallback texels' materials), so
tools/lighting/stale_bakes.py audits it like any bake. The DAT is original data outside the asset tree: its hash is in
the recipe. Any BLV rebuild invalidates the sidecar (the game ignores it): run this again.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[3]
COMMON = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools/mm9_import_discovery"))
sys.path.insert(0, str(ROOT / "tools/lighting"))
sys.path.insert(0, str(COMMON))
from mm9_units import MM9_TO_OPENYAMM_COORDINATE_SCALE as SCALE  # noqa: E402
from transcode_mm9_dat_to_odm import read_dat_world  # noqa: E402
from bake_geometry import rgbm, rle_bgra  # noqa: E402
from dungeon.geometry import poly_ring  # noqa: E402
from dungeon.source import MM9_SUN_GAIN  # noqa: E402
import review_root  # noqa: E402

PLANE_TOLERANCE = 1.5      # LT units between our face's plane and a DAT polygon's
NORMAL_DOT = 0.998
INSIDE_EPS = 4.5           # LT: a core texel within about half of our texel (16 native = 6.25 LT) of a polygon
OUTSIDE_REACH = 24.0       # LT: chart texels outside our faces sample a polygon this close (clamped)
VOXEL = 64.0               # LT: fallback neighbourhood cells
NEAR_CELLS, FAR_CELLS = 2, 8
MIN_NEIGHBOURS = 64        # transferred texels a fallback chart needs for its own scale
LMPLANES = [((0, 1, 0), (0, 0, -1)), ((0, -1, 0), (0, 0, 1)), ((0, 0, 1), (0, 1, 0)), ((0, 0, -1), (0, -1, 0)),
            ((1, 0, 0), (0, -1, 0)), ((-1, 0, 0), (0, -1, 0))]
LUMA = np.array([0.2126, 0.7152, 0.0722])
MAPS = "worlds/mm9/maps"
PRODUCER = "mm9r_common/lightmap_transfer.py"


def fnv(data: bytes) -> int:
    """FNV-1a 64 of a byte string (bake_geometry.fnv: the hash every bake records)."""
    value = 14695981039346656037
    prime = 1099511628211
    for byte in data:
        value = ((value ^ byte) * prime) & 0xFFFFFFFFFFFFFFFF
    return value


def fnv_file(path: Path, cache: dict) -> int:
    key = str(path)
    if key not in cache:
        cache[key] = fnv(path.read_bytes())
    return cache[key]


# --- sidecars ------------------------------------------------------------------------------------------------------

def read_sidecar(path: Path) -> dict:
    data = path.read_bytes()
    magic, version, header = struct.unpack_from("<8sII", data, 0)
    assert magic == b"OYILIT1\0" and version in (1, 2) and header == 64, path
    geometry_hash, face_count, sector_count, page_count, dep_count, page_off, face_off, sector_off, dep_off, \
        pixel_off, length = struct.unpack_from("<Q10I", data, 16)
    assert length == len(data)
    pages, dims = [], []
    for i in range(page_count):
        width, height, offset, size = struct.unpack_from("<4I", data, page_off + 16 * i)
        payload = np.frombuffer(data, np.uint8, size, offset)
        out = np.empty((width * height, 4), np.uint8)
        pos = filled = 0
        while pos < size:
            tag = int(payload[pos])
            count = (tag & 127) + 1
            if tag & 128:
                out[filled:filled + count] = payload[pos + 1:pos + 5]
                pos += 5
            else:
                out[filled:filled + count] = payload[pos + 1:pos + 1 + 4 * count].reshape(count, 4)
                pos += 1 + 4 * count
            filled += count
        assert filled == width * height and pos == size
        rgb = out[:, [2, 1, 0]].astype(np.float32) / 255 * (out[:, 3:4].astype(np.float32) / 255) * 4
        pages.append(rgb.reshape(height, width, 3))
        dims.append((width, height))
    faces = []
    for i in range(face_count):
        page, flags, *axes = struct.unpack_from("<HH8f", data, face_off + 36 * i)
        faces.append(None if page == 0xFFFF else (page, tuple(axes[:4]), tuple(axes[4:])))
    if version == 2:
        # daylight pairs (static, daylight): the total light per page, faces on the pair
        pages = [pages[i] + pages[i + 1] for i in range(0, len(pages), 2)]
        dims = dims[::2]
        faces = [None if f is None else (f[0] // 2, f[1], f[2]) for f in faces]
    sectors = [struct.unpack_from("<3f", data, sector_off + 12 * i) for i in range(sector_count)]
    deps, cursor = {}, dep_off
    for _ in range(dep_count):
        size, digest = struct.unpack_from("<IQ", data, cursor)
        deps[data[cursor + 12:cursor + 12 + size].decode()] = digest
        cursor += 12 + size
    return {"hash": geometry_hash, "face_count": face_count, "sector_count": sector_count, "pages": pages,
            "dims": dims, "faces": faces, "sectors": sectors, "deps": deps}


def write_sidecar(path: Path, geometry_hash: int, faces: list, sectors: list, deps: dict, pages: list, dims: list,
                  daylight_pages: list | None = None):
    """Version 1, or with daylight_pages version 2: each page followed by its daylight page, faces on the first."""
    version = 1
    if daylight_pages is not None:
        version = 2
        pages = [page for pair in zip(pages, daylight_pages) for page in pair]
        dims = [size for size in dims for _ in range(2)]
        faces = [None if record is None else (record[0] * 2, record[1], record[2]) for record in faces]
    face_records = b"".join(struct.pack("<HH8f", 0xFFFF, 0, *([0.0] * 8)) if record is None
                            else struct.pack("<HH8f", record[0], 1, *record[1], *record[2]) for record in faces)
    sector_records = b"".join(struct.pack("<3f", *value) for value in sectors)
    dependency_records = b""
    for name, digest in sorted(deps.items()):
        encoded = name.encode()
        dependency_records += struct.pack("<IQ", len(encoded), digest) + encoded
    payloads = [rle_bgra(rgbm(np.concatenate([p, np.ones(p.shape[:2] + (1,), np.float32)], 2))) for p in pages]
    page_off = 64
    face_off = page_off + 16 * len(pages)
    sector_off = face_off + len(face_records)
    dep_off = sector_off + len(sector_records)
    pixel_off = dep_off + len(dependency_records)
    records, cursor = b"", pixel_off
    for (width, height), payload in zip(dims, payloads):
        records += struct.pack("<4I", width, height, cursor, len(payload))
        cursor += len(payload)
    header = b"OYILIT1\0" + struct.pack("<IIQ10I", version, 64, geometry_hash, len(faces), len(sectors), len(pages),
                                        len(deps), page_off, face_off, sector_off, dep_off, pixel_off, cursor)
    data = header + records + face_records + sector_records + dependency_records + b"".join(payloads)
    assert len(data) == cursor
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(data)
    os.replace(temporary, path)


# --- MM9's lightmaps ------------------------------------------------------------------------------------------------

def lithtech_frame(ring: np.ndarray, n: np.ndarray, grid: float):
    plane = max(range(6), key=lambda k: float(np.dot(LMPLANES[k][0], n)))
    p_axis = np.cross(n, LMPLANES[plane][1])
    q_axis = np.cross(p_axis, n)
    unit_p = p_axis / np.linalg.norm(p_axis)
    unit_q = q_axis / np.linalg.norm(q_axis)
    cur = ring[0].copy()
    for point in ring[1:]:
        dot = unit_p @ (point - cur)
        if dot < 0:
            cur += unit_p * dot
        dot = unit_q @ (point - cur)
        if dot < 0:
            cur += unit_q * dot
    for unit in (unit_p, unit_q):
        rest = np.fmod(unit @ cur, grid)
        cur -= unit * (rest if rest >= 0 else grid + rest)
    return p_axis, q_axis, cur


def lithtech_size(ring, p_axis, q_axis, origin, grid):
    """CPrePoly::CalculateTextureSize: ceil(max P.(p - O)) up to a grid multiple, / grid, + 1 (96 % exact)."""
    def extent(axis):
        value = float(np.ceil(max((ring - origin) @ axis) - 1e-3))
        return int(np.ceil(value / grid - 1e-6)) + 1
    return extent(p_axis), extent(q_axis)


class DatLightmaps:
    """Every lightmapped DAT polygon: ring (LT), unit normal, plane distance, its own grid and lightmap frame."""

    def __init__(self, world, skip_models=()):
        self.grid = float(world.world_info.light_map_grid_size)
        self.polys, self.unlit, self.grids, self.unlit_polys = [], 0, {}, []
        skip = {name.lower() for name in skip_models}
        for model in world.world_models:
            if model.name.lower() in skip:
                continue
            for poly in model.polies:
                ring = np.array([model.points[i] for i in poly_ring(poly)], float)
                if len(ring) < 3:
                    continue
                n = np.cross(ring, np.roll(ring, -1, 0)).sum(0)
                if np.linalg.norm(n) < 1e-6:
                    continue
                n /= np.linalg.norm(n)
                if not poly.lightmap_pixels_bgra:
                    # MM9 lit it per vertex (its regions' terrain, cliffs and sea): no lightmap for it here either
                    self.unlit += 1
                    self.unlit_polys.append({"ring": ring, "n": n, "d": float(n @ ring[0])})
                    continue
                value = np.array(poly.lightmap_pixels_bgra, np.int64)
                rgb = np.stack([(value >> 16) & 255, (value >> 8) & 255, value & 255], 1).astype(np.float32)
                rgb = rgb.reshape(poly.lightmap_height, poly.lightmap_width, 3)
                grid, fit = self.polygon_grid(ring, n, poly.lightmap_width, poly.lightmap_height)
                self.grids[(grid, fit)] = self.grids.get((grid, fit), 0) + 1
                p_axis, q_axis, origin = lithtech_frame(ring, n, grid)
                self.polys.append({"model": model.name, "ring": ring, "n": n, "d": float(n @ ring[0]), "rgb": rgb,
                                   "p": p_axis, "q": q_axis, "o": origin, "g": grid})
        self.normals = np.array([p["n"] for p in self.polys]).reshape(-1, 3)
        self.dists = np.array([p["d"] for p in self.polys])
        self.unlit_normals = np.array([p["n"] for p in self.unlit_polys]).reshape(-1, 3)
        self.unlit_dists = np.array([p["d"] for p in self.unlit_polys])

    def unlit_fraction(self, normal, points) -> float:
        """The share of LT points (n, 3) on a coplanar polygon MM9 lit per vertex (no lightmap)."""
        if not len(points) or not len(self.unlit_polys):
            return 0.0
        centre = points.mean(0)
        cand = np.nonzero((self.unlit_normals @ normal > NORMAL_DOT)
                          & (np.abs(self.unlit_normals @ centre - self.unlit_dists) < PLANE_TOLERANCE))[0]
        if not len(cand):
            return 0.0
        a2, b2 = plane_basis_2d(normal)
        p2 = np.stack([points @ a2, points @ b2], 1)
        covered = np.zeros(len(points), bool)
        for index in cand:
            ring = self.unlit_polys[index]["ring"]
            covered |= margins(p2, np.stack([ring @ a2, ring @ b2], 1)) >= -INSIDE_EPS
        return float(covered.mean())

    def polygon_grid(self, ring, n, width, height):
        """The world grid, and whether the stored size fits it (the size formula plus the edge row: 0 or 1 more per
        axis). It fits 95-99.4 % of the polygons of every map (87.5 % on Dragon Stadium); the rest are slivers that fit
        several other grids at once, no one grid, so no polygon takes another grid (2026-10-31, all 24 maps)."""
        p_axis, q_axis, origin = lithtech_frame(ring, n, self.grid)
        w, h = lithtech_size(ring, p_axis, q_axis, origin, self.grid)
        return self.grid, "fits" if 0 <= width - w <= 1 and 0 <= height - h <= 1 else "size off"

    def candidates(self, normal, point):
        return np.nonzero((self.normals @ normal > NORMAL_DOT)
                          & (np.abs(self.normals @ point - self.dists) < PLANE_TOLERANCE))[0]

    def sample(self, index, points):
        """Bilinear lightmap of polygon `index` at LT points (n, 3), clamped to its texels; bytes 0-255."""
        poly = self.polys[index]
        rgb, grid = poly["rgb"], poly["g"]
        height, width = rgb.shape[:2]
        rel = points - poly["o"]
        x = np.clip((width - 1) - (rel @ poly["p"]) / grid, 0, width - 1)
        y = np.clip((rel @ poly["q"]) / grid, 0, height - 1)
        x0 = np.minimum(np.floor(x).astype(int), width - 1)
        y0 = np.minimum(np.floor(y).astype(int), height - 1)
        x1 = np.minimum(x0 + 1, width - 1)
        y1 = np.minimum(y0 + 1, height - 1)
        fx = (x - x0)[:, None]
        fy = (y - y0)[:, None]
        top = rgb[y0, x0] * (1 - fx) + rgb[y0, x1] * fx
        bottom = rgb[y1, x0] * (1 - fx) + rgb[y1, x1] * fx
        return top * (1 - fy) + bottom * fy


def margins(points2d: np.ndarray, ring2d: np.ndarray) -> np.ndarray:
    """Signed distance inside a convex ring (positive inside), the minimum over its edges."""
    area = np.sum(ring2d[:, 0] * np.roll(ring2d[:, 1], -1) - np.roll(ring2d[:, 0], -1) * ring2d[:, 1])
    if area < 0:
        ring2d = ring2d[::-1]
    result = np.full(len(points2d), np.inf)
    for a, b in zip(ring2d, np.roll(ring2d, -1, 0)):
        edge = b - a
        length = np.hypot(*edge)
        if length < 1e-6:
            continue
        inward = np.array([-edge[1], edge[0]]) / length
        result = np.minimum(result, (points2d - a) @ inward)
    return result


def plane_basis_2d(normal):
    helper = np.array([0.0, 0.0, 1.0]) if abs(normal[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    a = np.cross(normal, helper)
    a /= np.linalg.norm(a)
    return a, np.cross(normal, a)


# --- the map ---------------------------------------------------------------------------------------------------------

def lt_forward(rotation) -> np.ndarray:
    """The LithTech unit vector of an object's Euler (pitch, yaw) (gr_SetupMatrixEuler's forward)."""
    pitch, yaw = float(rotation[0]), float(rotation[1])
    return np.array([math.cos(pitch) * math.sin(yaw), -math.sin(pitch), math.cos(pitch) * math.cos(yaw)])


# MM9's lights over the open land (radius 750 LT and up: the regions' huge white or sun-coloured Lights that stand in
# for the sun on their terrain and structures, a few city squares'); its lamps reach at most 700 LT (survey of the 12
# regions and 7 cities, 2026-11-07). Their light is the open air's (D), so it goes with the sun at night; the engine
# treats the same lights in the vertex light alike (IndoorOpenAirLightMinRadius, devdocs/INDOOR_OPEN_SKY.md
# "Open-air lights").
OPEN_AIR_LIGHT_RADIUS_LT = 750.0


class DaylightSplit:
    """The open air's share of MM9's lightmap texels (the module's "Daylight pages"), in display units (byte / 255)."""

    def __init__(self, world):
        match = re.search(r"ambientlight\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", world.world_info.properties, re.I)
        self.ambient = np.array([float(v) for v in match.groups()]) / 255 if match else np.zeros(3)
        self.to_sun, self.sun = None, np.zeros(3)
        self.lights = []
        self.open_air = []
        for obj in world.objects:
            p = {prop.name: prop.value for prop in obj.properties}
            if obj.name == "StaticSunLight" and self.to_sun is None:
                self.to_sun = -lt_forward(p["Rotation"])
                self.sun = np.minimum(np.array(p.get("InnerColor", [255, 255, 255]), float)
                                      * float(p.get("BrightScale", 1.0)), 255) / 255
            elif obj.name in ("Light", "DirLight"):
                # LithTech AddLight: LightColor, else InnerColor; x BrightScale; quartic window over LightRadius
                colour = np.array(p.get("InnerColor", p.get("LightColor", [255, 255, 255])), float)
                cone = None
                if obj.name == "DirLight":
                    cone = (lt_forward(p["Rotation"]), math.cos(math.radians(float(p.get("FOV", 90.0))) / 2))
                radius = float(p.get("LightRadius", 300.0))
                light = (np.array(p["Pos"], float), radius, colour * float(p.get("BrightScale", 1.0)) / 255, cone)
                (self.open_air if radius >= OPEN_AIR_LIGHT_RADIUS_LT else self.lights).append(light)

    def lamps(self, lt: np.ndarray, n: np.ndarray, lights: list | None = None) -> np.ndarray:
        """MM9's lamps (or the given lights) at LT points on a plane of normal n, unshadowed (CalcLightSample)."""
        out = np.zeros((len(lt), 3))
        lo, hi = lt.min(0), lt.max(0)
        for pos, radius, colour, cone in self.lights if lights is None else lights:
            if (np.maximum(lo - pos, 0) + np.maximum(pos - hi, 0)) @ np.ones(3) > radius * 1.8:
                continue
            to = pos - lt
            dist2 = np.einsum("ij,ij->i", to, to)
            near = dist2 < radius * radius
            if not near.any():
                continue
            dist = np.sqrt(dist2[near])
            facing = np.clip((to[near] @ n) / np.maximum(dist, 1e-6), 0, 1)
            weight = (1 - dist2[near] / (radius * radius)) ** 2 * facing
            if cone is not None:
                axis, cos_half = cone
                along = (-to[near] @ axis) / np.maximum(dist, 1e-6)
                weight = weight * np.clip((along - cos_half) / (1 - cos_half), 0, 1)
            out[near] += weight[:, None] * colour
        return out

    def daylight(self, v: np.ndarray, lt: np.ndarray, n: np.ndarray) -> np.ndarray:
        """D per texel and channel (v (k, 3) display, lt (k, 3), n the unit LT normal)."""
        floor = np.minimum(self.ambient, v)
        facing = float(np.clip(MM9_SUN_GAIN * (n @ self.to_sun), 0, 1)) if self.to_sun is not None else 0.0
        open_air = self.lamps(lt, n, self.open_air) if self.open_air else 0.0
        ceiling = np.maximum(np.minimum(v, self.ambient + self.sun * facing + open_air), floor)
        return np.clip(v - self.lamps(lt, n), floor, ceiling)


class Map:
    def __init__(self, project: Path, root: Path):
        self.project = project.resolve()
        overrides = yaml.safe_load((self.project / "overrides.yml").read_text())
        self.settings = overrides["map"]
        self.stem = self.settings["stem"]
        self.offset = self.settings.get("offset", (0, 0, 0))
        self.dat = ROOT / "mm9/extracted/WORLDS/WORLDS" / self.settings.get("dat", f"{self.stem.upper()}.dat")
        self.root = root.resolve()
        self.bake = ROOT / f"output/mm9_rework/bakes/{self.stem}"
        self.out = ROOT / f"output/mm9_rework/lightmap_transfer/{self.stem}"
        self.work = self.project / "work/lightmap_transfer"

    def installed(self, suffix: str) -> Path:
        return self.root / MAPS / f"{self.stem}{suffix}"

    def daylight(self) -> bool:
        """Whether the installed scene opens the map to the sky with a `daylight` block (the daylight pages)."""
        scene = self.installed(".scene.yml")
        return scene.exists() and bool((yaml.safe_load(scene.read_text()) or {}).get("daylight"))

    def native_to_lt(self, points: np.ndarray) -> np.ndarray:
        o = self.offset
        return np.stack([(points[..., 0] + o[0]) / SCALE, (points[..., 2] + o[2]) / SCALE,
                         (points[..., 1] + o[1]) / SCALE], -1)


def export_scene(m: Map) -> dict:
    m.work.mkdir(parents=True, exist_ok=True)
    path = m.work / "scene.json"
    subprocess.run([str(ROOT / "build/game/openyamm"), "--asset-root", str(m.root), "--world", "mm9",
                    "--headless-export-indoor-bake-scene", f"{m.stem}.blv", str(path)], cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL)
    return json.loads(path.read_text())


def face_key(face: dict) -> tuple:
    """A face's geometry: mover flag and vertices (the stored pose for a mover). The texture is matched apart: a
    rebuild may give a face another texture (Yanmir's water, WATEZWECUN to lqw115mm9) without moving it."""
    points = face["stored_points"] if face["mover"] else face["points"]
    return (bool(face["mover"]), tuple(tuple(int(round(v)) for v in p) for p in points))


def base_on_current(m: Map, cache: dict):
    """The Cycles bake's records (pages, sector ambient, dependencies) mapped onto the current BLV's faces."""
    base = read_sidecar(m.bake / f"{m.stem}.lighting")
    base_scene = json.loads((m.bake / "scene.json").read_text())
    base_recipe = json.loads((m.bake / f"{m.stem}.bake.json").read_text())
    assert "profile" in base_recipe, "the bake directory's recipe is not a Cycles bake"
    assert base["face_count"] == base_scene["face_count"], "scene.json is not the bake's scene"
    blv = m.installed(".blv")
    current_hash = fnv_file(blv, cache)
    report = {"base_geometry_hash": f"{base['hash']:016x}", "current_geometry_hash": f"{current_hash:016x}"}
    if current_hash == base["hash"]:
        scene = base_scene
        faces = list(base["faces"])
        report.update(carried_over=False, faces=len(faces))
    else:
        scene = export_scene(m)
        if scene["sector_count"] != base["sector_count"]:
            raise SystemExit(f"{m.stem}: the rebuilt BLV has {scene['sector_count']} sectors, the bake "
                             f"{base['sector_count']}: bake it again (dungeon/lighting.py), then rerun")
        charted, uncharted = {}, set()
        for face in base_scene["faces"]:
            record = base["faces"][face["index"]]
            if record is not None:
                charted.setdefault(face_key(face), []).append((face["texture"].lower(), record))
            else:
                uncharted.add(face_key(face))
        faces, unmatched, used, retextured = [None] * scene["face_count"], [], 0, {}
        for face in scene["faces"]:
            records = charted.get(face_key(face))
            if records:
                texture = face["texture"].lower()
                pick = next((k for k, (t, _) in enumerate(records) if t == texture), 0)
                old_texture, faces[face["index"]] = records.pop(pick)
                used += 1
                if old_texture != texture:
                    retextured[f"{old_texture} -> {texture}"] = retextured.get(f"{old_texture} -> {texture}", 0) + 1
            elif face_key(face) in uncharted:
                # the bake charted no lightmap here (its skip_textures: the regions' terrain), so it has none now either
                pass
            elif face["visible"] and not face["attributes"] & 0x00400000 and (
                    not face["mover"] or face.get("mover_receiver")):
                unmatched.append({"index": face["index"], "texture": face["texture"], "points": face["points"][:3]})
        report.update(carried_over=True, faces=scene["face_count"], base_faces=base["face_count"],
                      charted_faces_matched=used, charted_faces_left=sum(len(v) for v in charted.values()),
                      retextured=retextured,
                      drawn_faces_unmatched=len(unmatched), unmatched_examples=unmatched[:20])
        if len(unmatched) > 50:
            raise SystemExit(f"{m.stem}: {len(unmatched)} drawn faces of the current BLV have no chart in the bake: "
                             "bake it again (dungeon/lighting.py), then rerun")
    return base, base_scene, base_recipe, scene, faces, current_hash, report


def charts_of(scene: dict, faces: list):
    groups = {}
    for face in scene["faces"]:
        record = faces[face["index"]]
        if record is None:
            continue
        points = np.array(face["stored_points"] if face["mover"] else face["points"], float)
        groups.setdefault(record, []).append((face, points))
    return groups


def pixel_inside(pixels: np.ndarray, polygon: np.ndarray, eps: float) -> np.ndarray:
    inside = np.zeros(len(pixels), bool)
    x, y = pixels[:, 0], pixels[:, 1]
    count = len(polygon)
    for i in range(count):
        (x1, y1), (x2, y2) = polygon[i], polygon[(i + 1) % count]
        with np.errstate(divide="ignore", invalid="ignore"):
            cross = ((y1 > y) != (y2 > y)) & (x < x1 + (y - y1) * (x2 - x1) / np.where(y2 == y1, 1e-12, y2 - y1))
        inside ^= cross
    if eps > 0:
        near = np.zeros(len(pixels), bool)
        for i in range(count):
            a, b = polygon[i], polygon[(i + 1) % count]
            edge = b - a
            t = np.clip(((pixels - a) @ edge) / max(edge @ edge, 1e-12), 0, 1)
            near |= np.hypot(*(pixels - (a + t[:, None] * edge)).T) <= eps
        inside |= near
    return inside


def principal(normal: np.ndarray) -> int:
    axis = int(np.argmax(np.abs(normal)))
    return axis * 2 + (0 if normal[axis] > 0 else 1)


def transfer(m: Map, encoding: str, min_light: float, cache: dict) -> dict:
    started = time.time()
    base, base_scene, base_recipe, scene, faces, current_hash, report = base_on_current(m, cache)
    world = read_dat_world(m.dat)
    fallback_models = sorted(m.settings.get("lightmap_fallback_models") or [])
    dat = DatLightmaps(world, fallback_models)
    emitter_textures = {t.lower() for e in base_recipe["profile"].get("emitters") or [] for t in e["textures"]}
    pages = [p.copy() for p in base["pages"]]
    dims = base["dims"]
    stats = {"core": 0, "core_transferred": 0, "rim": 0, "rim_transferred": 0, "charts": 0, "charts_matched": 0,
             "models": {}}
    kept_by, kept_charts, fallback_jobs = {}, [], []
    vertex_lit_cells = set()             # VOXEL cells of the charts left vertex-lit as MM9 lit them
    # a layout-only base (dungeon/lighting.py --layout-only) has no bake light: the actors' per-sector ambient is
    # recomputed from the transferred texels
    layout_only = bool(base_recipe["profile"].get("layout_only"))
    sector_sum = np.zeros((scene["sector_count"], 3))
    sector_count = np.zeros(scene["sector_count"])
    cell_keys, cell_ours, cell_mm9 = [], [], []
    pair_ours, pair_mm9 = [], []
    split_jobs = []
    for (page, u_axis, v_axis), members in charts_of(scene, faces).items():
        stats["charts"] += 1
        width, height = dims[page]
        ua, va = np.array(u_axis, float), np.array(v_axis, float)
        pts0 = members[0][1]
        normal = np.cross(pts0, np.roll(pts0, -1, 0)).sum(0)
        normal /= np.linalg.norm(normal)
        plane_normal = members[0][0]["plane_normal"]
        if plane_normal is not None and normal @ np.array(plane_normal, float) < 0:
            normal = -normal
        distance = float(normal @ pts0.mean(0))
        outlines = []
        for _face, pts in members:
            hom = np.c_[pts, np.ones(len(pts))]
            outlines.append(np.stack([hom @ ua * width, hom @ va * height], 1))
        allpx = np.concatenate(outlines)
        x0 = max(0, int(np.floor(allpx[:, 0].min() - 0.5 + 1e-3)) - 2)
        x1 = min(width - 1, int(np.ceil(allpx[:, 0].max() - 0.5 - 1e-3)) + 2)
        y0 = max(0, int(np.floor(allpx[:, 1].min() - 0.5 + 1e-3)) - 2)
        y1 = min(height - 1, int(np.ceil(allpx[:, 1].max() - 0.5 - 1e-3)) + 2)
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        xs, ys = xs.ravel(), ys.ravel()
        centres = np.stack([xs + 0.5, ys + 0.5], 1)
        core = np.zeros(len(centres), bool)
        for outline in outlines:
            # only the texels within the outline's box and reach can be inside it (a region's terrain chart has
            # thousands of faces, each tested against all its texels: two minutes of the Isle of Ashes)
            low, high = outline.min(0) - 1.51, outline.max(0) + 1.51
            near = np.flatnonzero((centres[:, 0] >= low[0]) & (centres[:, 0] <= high[0])
                                  & (centres[:, 1] >= low[1]) & (centres[:, 1] <= high[1]))
            core[near] |= pixel_inside(centres[near], outline, 0.51)
        matrix = np.array([ua[:3], va[:3], normal])
        rhs = np.stack([centres[:, 0] / width - ua[3], centres[:, 1] / height - va[3],
                        np.full(len(centres), distance)], 1)
        lt = m.native_to_lt(np.linalg.solve(matrix, rhs.T).T)
        n_lt = np.array([normal[0], normal[2], normal[1]])
        texture = members[0][0]["texture"].lower()
        if texture in emitter_textures:
            continue                     # the sky or a lit pane: the bake's display value
        cand = dat.candidates(n_lt, lt[core].mean(0) if core.any() else lt.mean(0))
        best = np.full(len(lt), -np.inf)
        best_index = np.full(len(lt), -1)
        if len(cand):
            a2, b2 = plane_basis_2d(n_lt)
            p2 = np.stack([lt @ a2, lt @ b2], 1)
            lo2, hi2 = p2.min(0) - OUTSIDE_REACH, p2.max(0) + OUTSIDE_REACH
            for index in cand:
                poly = dat.polys[index]
                ring2 = np.stack([poly["ring"] @ a2, poly["ring"] @ b2], 1)
                if (ring2.max(0) < lo2).any() or (ring2.min(0) > hi2).any():
                    continue
                sel = np.nonzero((p2[:, 0] >= ring2[:, 0].min() - OUTSIDE_REACH)
                                 & (p2[:, 0] <= ring2[:, 0].max() + OUTSIDE_REACH)
                                 & (p2[:, 1] >= ring2[:, 1].min() - OUTSIDE_REACH)
                                 & (p2[:, 1] <= ring2[:, 1].max() + OUTSIDE_REACH))[0]
                if not len(sel):
                    continue
                margin = margins(p2[sel], ring2)
                better = margin > best[sel]
                best[sel[better]] = margin[better]
                best_index[sel[better]] = index
        take = np.where(core, best >= -INSIDE_EPS, best >= -OUTSIDE_REACH) & (best_index >= 0)
        # Mostly on polygons MM9 lit per vertex (a region's terrain, cliffs, sea): the face stays vertex-lit, as there
        if core.any() and (core & take).sum() < 0.5 * core.sum() \
                and dat.unlit_fraction(n_lt, lt[core & ~take]) > 0.5:
            for face, _points in members:
                faces[face["index"]] = None
            stats["vertex_lit_charts"] = stats.get("vertex_lit_charts", 0) + 1
            stats["vertex_lit_texels"] = stats.get("vertex_lit_texels", 0) + int(core.sum())
            vertex_lit_cells.update(map(tuple, np.floor(lt[core] / VOXEL).astype(np.int64).tolist()))
            continue
        split_jobs.append((page, ys, xs, lt, n_lt))
        stats["core"] += int(core.sum())
        stats["core_transferred"] += int((core & take).sum())
        stats["rim"] += int((~core).sum())
        stats["rim_transferred"] += int((~core & take).sum())
        kept = core & ~take
        if kept.any():
            key = ("mover " if members[0][0]["mover"] else "") + members[0][0]["texture"] \
                + (" translucent" if "translucency" in members[0][0] else "")
            kept_by[key] = kept_by.get(key, 0) + int(kept.sum())
            kept_charts.append((int(kept.sum()), key, lt[kept].mean(0).round(0).tolist(), len(cand)))
            rest = ~take
            fallback_jobs.append((page, ys[rest], xs[rest], lt[kept], principal(n_lt), key, members,
                                  int(core.sum()), int((core & take).sum())))
        if take.any():
            stats["charts_matched"] += 1
            values = np.zeros((len(lt), 3), np.float32)
            for index in np.unique(best_index[take]):
                sel = take & (best_index == index)
                values[sel] = dat.sample(index, lt[sel])
                model = dat.polys[index]["model"]
                name = "PhysicsBSP" if model == "PhysicsBSP" else "other models"
                stats["models"][name] = stats["models"].get(name, 0) + int((sel & core).sum())
            values = values / 255.0
            if encoding == "linear":
                values = values ** 2.2
            ours = pages[page][ys[take], xs[take]].copy()
            core_take = core[take]
            sector = members[0][0]["sector"]
            if 0 <= sector < len(sector_count):
                sector_sum[sector] += values[take][core_take].sum(0)
                sector_count[sector] += int(core_take.sum())
            pair_ours.append(ours[core_take])
            pair_mm9.append(values[take][core_take])
            where = lt[take][core_take]
            cells = np.floor(where / VOXEL).astype(np.int64)
            cell_keys.append(((cells[:, 0] + 4096) * 8192 + (cells[:, 1] + 4096)) * 8192 * 6
                             + (cells[:, 2] + 4096) * 6 + principal(n_lt))
            cell_ours.append(ours[core_take])
            cell_mm9.append(values[take][core_take])
            pages[page][ys[take], xs[take]] = values[take]
    # fallback: per chart and channel, MM9 / bake over the transferred texels around it
    keys = np.concatenate(cell_keys) if cell_keys else np.zeros(0, np.int64)
    unique, inverse = np.unique(keys, return_inverse=True)
    sum_ours = np.zeros((len(unique), 3))
    sum_mm9 = np.zeros((len(unique), 3))
    counts = np.zeros(len(unique))
    if len(keys):
        np.add.at(sum_ours, inverse, np.concatenate(cell_ours))
        np.add.at(sum_mm9, inverse, np.concatenate(cell_mm9))
        np.add.at(counts, inverse, 1)
    lookup = {int(k): i for i, k in enumerate(unique)}
    fallback_report = {"charts": len(fallback_jobs), "near_same_facing": 0, "near_any": 0, "far": 0, "none": 0,
                       "vertex_lit": 0, "scales": []}

    def gather(cells, reach, facing):
        so, sm, count = np.zeros(3), np.zeros(3), 0.0
        seen = set()
        offsets = range(-reach, reach + 1)
        for cell in cells:
            for dx in offsets:
                for dy in offsets:
                    for dz in offsets:
                        c = (cell[0] + dx, cell[1] + dy, cell[2] + dz)
                        base_key = ((c[0] + 4096) * 8192 + (c[1] + 4096)) * 8192 * 6 + (c[2] + 4096) * 6
                        for f in ((facing,) if facing is not None else range(6)):
                            index = lookup.get(base_key + f)
                            if index is not None and index not in seen:
                                seen.add(index)
                                so += sum_ours[index]
                                sm += sum_mm9[index]
                                count += counts[index]
        return so, sm, count

    for page, ys_, xs_, lt_kept, facing, key, members, core_texels, core_taken in fallback_jobs:
        cells = {tuple(c) for c in np.floor(lt_kept / VOXEL).astype(np.int64).tolist()}
        if len(cells) > 400:
            cells = set(list(cells)[::max(1, len(cells) // 400)])
        so, sm, count = gather(cells, NEAR_CELLS, facing)
        kind = "near_same_facing"
        if count < MIN_NEIGHBOURS:
            so, sm, count = gather(cells, NEAR_CELLS, None)
            kind = "near_any"
        if count < MIN_NEIGHBOURS and any((c[0] + dx, c[1] + dy, c[2] + dz) in vertex_lit_cells for c in cells
                                          for dx in range(-NEAR_CELLS, NEAR_CELLS + 1)
                                          for dy in range(-NEAR_CELLS, NEAR_CELLS + 1)
                                          for dz in range(-NEAR_CELLS, NEAR_CELLS + 1)):
            # no MM9 lightmap near but faces MM9 lit per vertex: vertex-lit as they are (Drangheim City's roofs and
            # towers, our faces off MM9's planes amid its vertex-lit city), not the layout's grey scaled from afar
            for face, _points in members:
                faces[face["index"]] = None
            fallback_report["vertex_lit"] += 1
            stats["core"] -= core_texels
            stats["core_transferred"] -= core_taken
            stats["vertex_lit_charts"] = stats.get("vertex_lit_charts", 0) + 1
            stats["vertex_lit_texels"] = stats.get("vertex_lit_texels", 0) + core_texels
            continue
        if count < MIN_NEIGHBOURS:
            so, sm, count = gather(cells, FAR_CELLS, None)
            kind = "far"
        if count < 1 or (so <= 1e-6).any():
            fallback_report["none"] += 1
            continue
        fallback_report[kind] += 1
        scale = np.clip(sm / so, 0.1, 4.0)
        fallback_report["scales"].append(float(scale @ LUMA))
        pages[page][ys_, xs_] = np.minimum(pages[page][ys_, xs_] * scale, 1.0)
    scales = np.array(fallback_report.pop("scales")) if fallback_report["charts"] else np.zeros(0)
    if len(scales):
        fallback_report["scale_luma_p10_50_90"] = np.percentile(scales, [10, 50, 90]).round(3).tolist()
    if min_light > 0:
        for p in pages:
            np.maximum(p, min_light, out=p)
    daylight_pages = None
    if m.daylight() and encoding == "display":
        daylight_pages, split_report = split_daylight(DaylightSplit(world), pages, split_jobs)
        report["daylight_split"] = split_report
    if layout_only:
        base = dict(base, sectors=[tuple(float(v) for v in np.clip(sector_sum[i] / sector_count[i], 0, 4))
                                   if sector_count[i] > 0 else tuple(base["sectors"][i])
                                   for i in range(len(sector_count))])
    ours = np.concatenate(pair_ours) if pair_ours else np.zeros((1, 3))
    mm9 = np.concatenate(pair_mm9) if pair_mm9 else np.zeros((1, 3))
    lum_ours, lum_mm9 = ours @ LUMA, mm9 @ LUMA
    grids = {f"{grid:g} {fit}": count for (grid, fit), count in sorted(dat.grids.items())}
    report.update(stats)
    report.update({
        "map": m.stem, "encoding": encoding, "min_light": min_light, "seconds": round(time.time() - started, 1),
        "world_grid_lt": dat.grid, "polygon_grids": grids, "dat_lightmapped_polys": len(dat.polys),
        "dat_unlit_polys": dat.unlit, "fallback_models": fallback_models,
        # over the lightmapped charts; none on a map MM9 lit wholly per vertex (Mountain Pass: terrain only)
        "coverage_core": round(stats["core_transferred"] / stats["core"], 5) if stats["core"] else None,
        "lightmapped_share": round(stats["core"] / max(stats["core"] + stats.get("vertex_lit_texels", 0), 1), 5),
        "kept_core_texels": stats["core"] - stats["core_transferred"], "fallback": fallback_report,
        "transferred_mean_rgb_bake": ours.mean(0).round(4).tolist(),
        "transferred_mean_rgb_mm9": mm9.mean(0).round(4).tolist(),
        "transferred_mean_luma_bake_mm9": [round(float(lum_ours.mean()), 4), round(float(lum_mm9.mean()), 4)],
        "core_kept_by_texture_top": sorted(kept_by.items(), key=lambda item: -item[1])[:20],
        "core_kept_charts_top": sorted(kept_charts, key=lambda item: -item[0])[:30],
    })
    return {"base": base, "base_recipe": base_recipe, "scene": scene, "faces": faces, "pages": pages,
            "daylight_pages": daylight_pages, "hash": current_hash, "report": report,
            "fallback_models": fallback_models}


def split_daylight(split: DaylightSplit, pages: list, jobs: list) -> tuple[list, dict]:
    """The daylight pages (D) of the charts' texels; `pages` keeps the rest. A texel two charts' rims share is split
    once, by the first."""
    daylight_pages = [np.zeros_like(p) for p in pages]
    done = [np.zeros(p.shape[:2], bool) for p in pages]
    total = np.zeros(3)
    day = np.zeros(3)
    for page, ys, xs, lt, n_lt in jobs:
        fresh = ~done[page][ys, xs]
        if not fresh.any():
            continue
        ys_, xs_, lt_ = ys[fresh], xs[fresh], lt[fresh]
        v = pages[page][ys_, xs_].astype(np.float64)
        d = split.daylight(v, lt_, n_lt)
        daylight_pages[page][ys_, xs_] = d
        pages[page][ys_, xs_] = v - d
        done[page][ys_, xs_] = True
        total += v.sum(0)
        day += d.sum(0)
    return daylight_pages, {"texels": int(sum(int(d.sum()) for d in done)),
                            "daylight_share_rgb": (day / np.maximum(total, 1e-9)).round(3).tolist(),
                            "ambient": split.ambient.round(4).tolist(), "sun": split.sun.round(4).tolist(),
                            "sun_gain": MM9_SUN_GAIN, "lights": len(split.lights),
                            "open_air_lights": len(split.open_air)}


# --- recipe, dependencies, install --------------------------------------------------------------------------------

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dependencies(m: Map, scene: dict, recipe_name: str, recipe_bytes: bytes, base_deps: dict, cache: dict) -> dict:
    """The BLV, its scene file, the recipe, and the base bake's texture dependencies (the fallback's materials)."""
    deps = {f"{MAPS}/{m.stem}.blv": fnv_file(m.installed(".blv"), cache)}
    if scene.get("scene_path"):
        deps[scene["scene_path"]] = fnv_file(m.root / scene["scene_path"], cache)
    deps[recipe_name] = fnv(recipe_bytes)
    for name, digest in base_deps.items():
        if "/textures/" in name:
            deps[name] = digest
    # a texture a rebuild gave a face since the bake (its current hash: the fallback/bake texels were made with the
    # old one, which stays listed)
    known = {Path(name).stem.lower() for name in deps if "/textures/" in name}
    drawn = {f["texture"].lower() for f in scene["faces"] if f["visible"] and not f["attributes"] & 0x00400000}
    missing = drawn - known
    if missing:
        from bake_assets import bake_texture_paths, source_roots
        paths, _ = bake_texture_paths(m.root, "mm9", [])
        for texture in sorted(missing):
            if texture in paths:
                path = paths[texture]
                base = next((r for r in source_roots(m.root) if path.is_relative_to(r)), m.root)
                deps[str(path.relative_to(base))] = fnv_file(path, cache)
    return deps


def write_outputs(m: Map, result: dict, mode: str, cache: dict) -> tuple[Path, Path]:
    """`<stem>.lighting` and `<stem>.bake.json` in output/mm9_rework/lightmap_transfer/<stem>/<mode>/."""
    out = m.out / mode
    out.mkdir(parents=True, exist_ok=True)
    recipe_name = f"{MAPS}/{m.stem}.bake.json"
    if mode == "cycles":
        recipe = result["base_recipe"]
    else:
        report = result["report"]
        recipe = {"producer": PRODUCER, "producer_sha256": sha256(Path(__file__)),
                  "dat": str(m.dat.relative_to(ROOT)), "dat_sha256": sha256(m.dat), "encoding": report["encoding"],
                  "min_light": report["min_light"],
                  "parameters": {"plane_tolerance_lt": PLANE_TOLERANCE, "normal_dot": NORMAL_DOT,
                                 "inside_eps_lt": INSIDE_EPS, "outside_reach_lt": OUTSIDE_REACH,
                                 "fallback_voxel_lt": VOXEL, "fallback_cells": [NEAR_CELLS, FAR_CELLS]},
                  "fallback_models": result["fallback_models"],
                  "daylight_pages": result.get("daylight_pages") is not None,
                  "base": {"bake": str(m.bake.relative_to(ROOT)), "geometry_hash": report["base_geometry_hash"],
                           "carried_over": report["carried_over"],
                           "lighting_sha256": sha256(m.bake / f"{m.stem}.lighting"), "recipe": result["base_recipe"]}}
    recipe_bytes = (json.dumps(recipe, sort_keys=True, indent=2) + "\n").encode()
    recipe_path = out / f"{m.stem}.bake.json"
    recipe_path.write_bytes(recipe_bytes)
    deps = dependencies(m, result["scene"], recipe_name, recipe_bytes, result["base"]["deps"], cache)
    lighting = out / f"{m.stem}.lighting"
    write_sidecar(lighting, result["hash"], result["faces"], result["base"]["sectors"], deps,
                  result["pages"], result["base"]["dims"], result.get("daylight_pages"))
    return lighting, recipe_path


def install(m: Map, lighting: Path, recipe: Path) -> None:
    """Into the review root by its own install (a temporary file, then a rename over the hard link)."""
    assert m.root == review_root.ASSETS.resolve(), "--install writes only into the review root"
    review_root.install_file(f"{MAPS}/{m.stem}.bake.json", recipe)
    review_root.install_file(f"{MAPS}/{m.stem}.lighting", lighting)


def backup(m: Map) -> Path:
    """work/lighting_before_transfer/: the installed sidecar pair, the profile, the map's bake.py and overrides."""
    target = m.project / "work/lighting_before_transfer"
    if target.exists():
        return target
    target.mkdir(parents=True)
    for source in (m.installed(".lighting"), m.installed(".bake.json"),
                   ROOT / f"tools/lighting/baked_indoors/profiles/mm9_{m.stem}.yml",
                   m.project / "bake.py", m.project / "overrides.yml"):
        if source.exists():
            shutil.copy2(source, target / source.name)
    if not m.installed(".lighting").exists():
        (target / "REVERT.md").write_text(
            f"# Before the MM9 lightmap transfer ({time.strftime('%Y-%m-%d %H:%M')})\n\n"
            f"No `{m.stem}.lighting` was installed (the map had no Cycles bake): revert by deleting "
            f"`{MAPS}/{m.stem}.lighting` and `{MAPS}/{m.stem}.bake.json` from the review root. The map's overrides.yml "
            "as it was is here.\n")
        return target
    (target / "REVERT.md").write_text(
        f"# Before the MM9 lightmap transfer ({time.strftime('%Y-%m-%d %H:%M')})\n\n"
        f"Installed `{m.stem}.lighting` (sha256 {sha256(m.installed('.lighting'))}) and `{m.stem}.bake.json`: the "
        "Cycles bake; the map's profile, bake.py and overrides.yml as they were.\n\n"
        "Revert on the current BLV (the Cycles bake carried over onto it, with its own recipe):\n\n"
        "    python3 level_generation/projects/mm9r_common/lightmap_transfer.py "
        f"level_generation/projects/{m.project.name} --cycles-only --install\n\n"
        f"Restore the profile with `cp {m.stem}.yml`-style copies of the files here (mm9_{m.stem}.yml to "
        "tools/lighting/baked_indoors/profiles/, bake.py to the project). These two sidecar files are valid only for "
        "the BLV they were baked from (before the 2026-10-31 invisible-bottoms rebuild).\n")
    return target


def measure(m: Map) -> dict:
    world = read_dat_world(m.dat)
    dat = DatLightmaps(world)
    sizes = np.array([p["rgb"].shape[1::-1] for p in dat.polys])
    return {"map": m.stem, "info": world.world_info.properties.strip(), "grid_lt": dat.grid,
            "grid_native": dat.grid * SCALE, "lightmapped_polys": len(dat.polys), "unlit_polys": dat.unlit,
            "texels": int(sizes.prod(1).sum()),
            "polygon_grids": {f"{grid:g} {fit}": count for (grid, fit), count in sorted(dat.grids.items())}}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", type=Path)
    ap.add_argument("--root", type=Path, default=review_root.ASSETS, help="asset root holding the map (read)")
    ap.add_argument("--encoding", choices=("display", "linear"), default="display")
    ap.add_argument("--min-light", type=float, help="floor under every texel (default: overrides map.lightmap_min_light"
                                                    " or 0, off)")
    ap.add_argument("--cycles-only", action="store_true", help="the Cycles bake on the current BLV (revert)")
    ap.add_argument("--install", action="store_true", help="install into the review root (backs up first)")
    ap.add_argument("--backup", action="store_true", help="only back up the installed lighting and settings")
    ap.add_argument("--measure", action="store_true", help="only MM9's lightmap resolution and grids")
    args = ap.parse_args()
    if args.root.resolve() == (review_root.REVIEW / "isleofashes_blv_root").resolve():
        # the open-air maps' own review root (their convert.py sets the same): --install writes there
        review_root.ASSETS = review_root.REVIEW / "isleofashes_blv_root"
        review_root.OWNED = review_root.REVIEW / "isleofashes_blv_owned.txt"
    m = Map(args.project, args.root)
    if args.measure:
        print(json.dumps(measure(m), indent=1))
        return 0
    if args.backup:
        print("backup", backup(m))
        return 0
    cache: dict = {}
    if args.install:
        backup(m)
    if args.cycles_only:
        base, _bs, base_recipe, scene, faces, current_hash, report = base_on_current(m, cache)
        result = {"base": base, "base_recipe": base_recipe, "scene": scene, "faces": faces, "pages": base["pages"],
                  "hash": current_hash, "report": report}
        lighting, recipe = write_outputs(m, result, "cycles", cache)
        print(json.dumps(report, indent=1))
    else:
        min_light = args.min_light if args.min_light is not None else float(m.settings.get("lightmap_min_light", 0))
        result = transfer(m, args.encoding, min_light, cache)
        lighting, recipe = write_outputs(m, result, args.encoding, cache)
        m.work.mkdir(parents=True, exist_ok=True)
        (m.work / f"report_{args.encoding}.json").write_text(json.dumps(result["report"], indent=1) + "\n")
        report = result["report"]
        print(json.dumps({k: report[k] for k in ("map", "coverage_core", "lightmapped_share", "kept_core_texels",
                                                 "carried_over",
                                                 "polygon_grids", "fallback_models", "fallback", "seconds",
                                                 "transferred_mean_luma_bake_mm9", "daylight_split")
                          if k in report}, indent=1))
    print("wrote", lighting)
    if args.install:
        install(m, lighting, recipe)
        print("installed", m.installed(".lighting"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
