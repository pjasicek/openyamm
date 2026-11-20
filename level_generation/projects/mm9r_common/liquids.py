#!/usr/bin/env python3
"""
MM9's remaining water textures drawn by the engine's liquid shader in the rebuilt dungeons, see-through where MM9's
are. Each map with such water calls `apply(build, scene)` last in its `scene` hook:

- its visible horizontal faces drawn with Water115 (the .spr or its first frame), water125's first frame or water123
  (the water surfaces: tops of pools, channels and flooded rooms) take a liquid texture name of their own through the
  scene's `face_attribute_overrides` (`texture_name`): `lqw115mm9`, `lqw125mm9`, `lqw123mm9` (opaque);
- a water surface that MM9 draws translucent and that has a bed under it takes a see-through name instead (`SEE_THROUGH`
  below): its DAT object's opacity, the faces of the maps' own MM9 liquids (water125.spr, slime, Ocean3/4) too;
- those names are liquids of the review root's liquid table (`engine/liquids/liquids.yml`, this world only,
  `depth: shallow`, the see-through ones with `opacity`), installed here under the tables lock;
- every liquid face (these and the faces of the maps' own MM9 liquids) leaves the scene's `translucent_faces`: the
  shader draws it (blended when its liquid is see-through), and a translucent entry would draw the liquid's flat colour
  over it.

    python3 level_generation/projects/mm9r_common/liquids.py                    # install the entries
    python3 level_generation/projects/mm9r_common/liquids.py --scenes <map>...  # and apply them to installed maps

**See-through (2026-10-31, the user: "if MM9 water was see-through partially, we need to keep this, and lighter blue
to fit").** MM9's translucency is texture alpha x brush alpha (devdocs/mm9_rework/MM9_VISUAL_PROPERTIES.md, finding 3).
A face's MM9 surface is found in the DAT: the water volume (`BlueWater`, `ClearWater`, `DirtyWater`, `CorrosiveFluid`
with `ShowSurface 1`) whose top it is (its box holds the face's centre, within 48 units of its top or inside the box;
`MOVED_SURFACES`: a scripted surface stored at the end of its travel, Verhoffin's rising trap water), drawn with
`SpriteSurfaceName` at `SurfaceAlpha`; or the brush polygon it came from (`WorldObject` and the like), which blends
only with its Translucent bit (0x8), at the brush's `Alpha`. Its opacity is that alpha x the sprite's or texture's
mean alpha (`TEXTURE_ALPHA`: the first frames' DTX alpha; Water115 0.42, water125 0.25; Water115flowing, water123,
slime and the oceans carry none, 1). An object's faces are see-through together, when that is below 1 and at least
half of them have a floor of their room (or of a room a portal joins to it) under them (`has_bed`): wading floors over
sealed or unbuilt water (Dook's Castle's lake, Inventa Storca's cavern, the Bathhouse wading floors, Dark Passageway's
tube room and ocean) stay opaque, since nothing would show through them. The name is `lq<family>o<percent>`
(`lqw115o21`: Water115 at 0.21), one liquid entry per family and opacity (`SEE_THROUGH`; a new product fails the
build until it is added there). The colours (`COLORS`) are saturated, lighter tints: the shader lights a thin body at
least as much as it is clear, as MM9 draws its water sprites unlit (Dungeon of Secrets' real capture: Water115's
27,83,212 at 0.125 over its dark floor measures 3,8,40), and lightens its ripples. Training Hall's pole room is drawn
with water123 but MM9 shows Ocean.spr there, so `w123` takes Ocean's dark teal.

Why names of their own, not the MM9 aliases: the aliases are shared by every MM9 map, and outdoor maps draw the same
textures on things that are no water surface (Wizard's Lab's coloured puzzle blocks and Boot Camp's orbs in water123,
the sides of Arslegard's water boxes and the gate sheets of Arslegard and Yorwick in Water115). Vertical faces (the
exit gates' shimmering sheets in Yanmir's Fort and Hall of the Gods) and beds (Beethoven's slime_0000) keep their
bitmaps; invisible faces (water volumes' sides) are left alone. The override is per face and per build (face ids come
from the compiled BLV the hook sees), so a rebuild keeps it; no converter change.

The game draws a liquid face from its liquid entry and loads no art for it, but the lighting bake
(tools/lighting/bake_indoor.py) needs a bitmap for every visible face's texture (its mean colour is the bounce albedo).
`install` therefore places `worlds/mm9/textures/LQW115MM9.bmp` (and 125, 123): byte copies of the native first frames
(WATEQOBX0Z, WATENZD35K, WATE1XKSQP), so the bake sees the same albedo as before; and one per see-through name, the
family's native frame with its alpha made opaque: the bake export gives a see-through liquid face the liquid's opacity
as its translucency, so light reaches the bed through it, and the bitmap's own alpha must not count twice. No existing
texture is changed. The same bitmaps go to assets_source/worlds/mm9/textures, where the bake of the promoted maps finds
them; assets_dev holds only cooked MM9 surfaces, and liquids are never cooked.

Ids are distinct from the maps' own entries (Beethoven's `slime_mm9`/`water_mm9`, `ocean_mm9_inventastorca`,
`ocean_mm9_dookscastle`), whose installers rewrite only their own blocks. Move these with the maps to `assets_dev`.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from collections import Counter
from pathlib import Path

import numpy as np

COMMON = Path(__file__).resolve().parent
sys.path.insert(0, str(COMMON))
import review_root  # noqa: E402
from dungeon import tables  # noqa: E402
from dungeon.geometry import poly_ring  # noqa: E402

ROOT = COMMON.parents[2]
TABLE = "engine/liquids/liquids.yml"
INVISIBLE = 0x2000
LT_INVISIBLE, LT_TRANSLUCENT = 0x4, 0x8
# The old import's alias of an MM9 water texture -> the liquid texture name its opaque surfaces take.
SURFACES = {"wateqobx0z": "lqw115mm9",      # SpriteTextures\Water\water115\water115_0000.dtx
            "watezwecun": "lqw115mm9",      # Sprites\Water\Water115.spr
            "watenzd35k": "lqw125mm9",      # SpriteTextures\Water\water125\water125_0000.dtx
            "wate1xksqp": "lqw123mm9"}      # Sprites\Water\water123.spr
# The alias -> the family its see-through surfaces take a name in (the maps' own liquids too: water_mm9's water125.spr,
# slime_mm9, ocean_mm9_inventastorca's Ocean3, ocean_mm9_dookscastle's Ocean4).
FAMILIES = {"wateqobx0z": "w115", "watezwecun": "w115", "watenzd35k": "w125", "wate27jpcx": "w125",
            "wate1xksqp": "w123", "slim91p4yn": "slm", "ocea8lh6ka": "oc3", "oceabym7ai": "oc4"}
# A family's liquid id prefix, its native first frame (the bake's bitmap) and its see-through colour.
FAMILY_IDS = {"w115": "water115", "w125": "water125", "w123": "water123", "slm": "slime", "oc3": "ocean3",
              "oc4": "ocean4"}
NATIVE_FRAMES = {"w115": "WATEQOBX0Z", "w125": "WATENZD35K", "w123": "WATE1XKSQP", "slm": "SLIM91P4YN",
                 "oc3": "OCEA8LH6KA", "oc4": "OCEABYM7AI"}
COLORS = {"w115": [14, 62, 210], "w125": [30, 74, 86], "w123": [36, 64, 84], "slm": [112, 132, 56],
          "oc3": [30, 50, 50], "oc4": [28, 64, 128]}
# The mean alpha of MM9's water sprites and textures (first frame, DTX alpha; 1 where the file carries none).
TEXTURE_ALPHA = {"water115.spr": 0.416, "water115_0000.dtx": 0.419, "water115flowing.spr": 1.0,
                 "water125.spr": 0.248, "water125_0000.dtx": 0.248, "water123.spr": 1.0, "ocean.spr": 1.0,
                 "ocean3.spr": 1.0, "ocean4.spr": 1.0, "slime.spr": 1.0, "slime_0000.dtx": 1.0}
# The see-through liquids: family -> the opacities (MM9's products, two decimals) the maps use.
# Verhoffin Ruins with swimming (2026-11-02): the pit's water125 (0.25) and the crevasse's Ocean3 (0.9) have their beds
# under them in the same room, so they are see-through.
SEE_THROUGH = {"w115": (0.12, 0.17, 0.21, 0.29, 0.37, 0.42, 0.7), "w125": (0.17, 0.2, 0.25), "w123": (0.4, 0.9),
               "slm": (0.7, 0.8), "oc3": (0.9,), "oc4": (0.5, 0.7, 0.8, 0.85, 0.95)}
# The outdoor regions as BLVs (2026-11-04, a scan of their DATs' translucent water): Ocean4 at 0.95 (Thjorgard's
# WorldObject1), 0.85 (Thronheim's WorldObject0), 0.8 (the Ocean of Frosgard, Lindisfarne, Bootcamp); water123 at 0.4
# (Bootcamp's WorldObject85 and 87).
# Ocean4 at 0.7: the Drangheim region's well water (face 25823, 2026-11-07).
# A DAT surface matches a face within this height (native units) of its top; a surface a script moves, within its
# travel above it: Verhoffin Ruins' WaterTrap (DrainWater.scr) rises from its DAT top (-492) to -77, where its face is.
MATCH_HEIGHT = 48.0
MOVED_SURFACES = {"WaterTrap": 512.0}
# Colours of the opaque entries: from the native frame's mean (Water115 27,83,212; water123 110,122,158), darkened and
# desaturated until the water read as water both in dark rooms (Chasm, Dark Passageway) and lit ones (Bathhouse, Temple
# of Honk): the shader lights it by the sector ambient, not the lightmap. water125's as Beethoven's water_mm9 (the .spr).
ENTRIES = """
  - id: water115_mm9
    # MM9's Water115: the water surfaces of the rebuilt dungeons (level_generation/projects/mm9r_common/liquids.py
    # retextures them to these names in each map's scene, as the two entries below).
    kind: water
    color: [22, 60, 140]
    applies_to: [face]
    worlds: [mm9]
    depth: shallow
    match:
      texture_names: [lqw115mm9]

  - id: water125_frame_mm9
    # water125's first frame (Verhoffin Ruins' electrified pit); the .spr is Beethoven's water_mm9.
    kind: water
    color: [44, 92, 102]
    applies_to: [face]
    worlds: [mm9]
    depth: shallow
    match:
      texture_names: [lqw125mm9]

  - id: water123_mm9
    # water123 (Training Hall's pole room).
    kind: water
    color: [48, 64, 104]
    applies_to: [face]
    worlds: [mm9]
    depth: shallow
    match:
      texture_names: [lqw123mm9]

  - id: sea_mm9
    # The open sea of an MM9 outdoor map built as a BLV (outdoor_blv.py retextures its Ocean faces to this name):
    # deep water in the MM6-MM8 outdoor seas' colour (water_mm8), not the indoor oceans' bright tint.
    kind: water
    color: [28, 58, 68]
    applies_to: [face]
    worlds: [mm9]
    match:
      texture_names: [lqseamm9]
"""
OPAQUE_IDS = ("water115_mm9", "water125_frame_mm9", "water123_mm9", "sea_mm9")
SEA_TEXTURE = "lqseamm9"            # the outdoor sea's liquid name (sea_mm9)


def see_through_name(family: str, opacity: float) -> str:
    return f"lq{family}o{int(round(opacity * 100)):02d}"


def see_through_entries() -> str:
    """The see-through liquids' entries (`SEE_THROUGH`), after the opaque ones."""
    blocks = []
    for family, opacities in SEE_THROUGH.items():
        for opacity in opacities:
            name = see_through_name(family, opacity)
            blocks.append(f"""
  - id: {FAMILY_IDS[family]}_o{name[-2:]}_mm9
    # See-through: MM9 draws these surfaces at {opacity} (texture alpha x brush alpha; liquids.py).
    kind: water
    color: {COLORS[family]}
    opacity: {opacity}
    applies_to: [face]
    worlds: [mm9]
    depth: shallow
    match:
      texture_names: [{name}]
""")
    return "".join(blocks)


def opaque_alpha_bitmap(data: bytes) -> bytes:
    """A 32-bit BMP with every pixel's alpha 255."""
    offset = struct.unpack("<I", data[10:14])[0]
    width, height = struct.unpack("<ii", data[18:26])
    if struct.unpack("<H", data[28:30])[0] != 32:
        raise SystemExit("liquids: the native water frames are 32-bit BMPs")
    pixels = bytearray(data[offset:offset + abs(width * height) * 4])
    pixels[3::4] = b"\xff" * (len(pixels) // 4)
    return data[:offset] + bytes(pixels) + data[offset + len(pixels):]


def install() -> None:
    """The entries in the review root's liquid table (shared: under the tables lock; replaced, never duplicated) and
    the bake's bitmaps of the liquid names."""
    with tables.locked("review_tables.lock"):
        path = review_root.mirror_path(TABLE)
        text = path.read_text()
        blocks = re.split(r"(?m)^(?=  - id: )", text)
        # This helper's blocks: the opaque ids and every see-through id (also of opacities no longer used).
        ours = r"  - id: (%s|(%s)_o\d\d_mm9)\n" % ("|".join(OPAQUE_IDS), "|".join(FAMILY_IDS.values()))
        kept = "".join(b for b in blocks if not re.match(ours, b))
        kept = kept.rstrip("\n") + "\n"
        new = kept + ENTRIES + see_through_entries()
        if new != text:
            review_root.install(TABLE, new.encode())
        bitmaps = {name.upper(): review_root.mirror_path(f"worlds/mm9/textures/{native}.bmp").read_bytes()
                   for name, native in (("lqw115mm9", "WATEQOBX0Z"), ("lqw125mm9", "WATENZD35K"),
                                        ("lqw123mm9", "WATE1XKSQP"), (SEA_TEXTURE, "OCEABYM7AI"))}
        for family, opacities in SEE_THROUGH.items():
            native = review_root.mirror_path(f"worlds/mm9/textures/{NATIVE_FRAMES[family]}.bmp").read_bytes()
            for opacity in opacities:
                bitmaps[see_through_name(family, opacity).upper()] = opaque_alpha_bitmap(native)
        for name, data in bitmaps.items():
            relative = f"worlds/mm9/textures/{name}.bmp"
            target = review_root.mirror_path(relative)
            if not target.exists() or target.read_bytes() != data:
                review_root.install(relative, data)
            source = ROOT / "assets_source" / relative
            if not source.exists() or source.read_bytes() != data:
                temporary = source.with_name(source.name + ".tmp")
                temporary.write_bytes(data)
                temporary.replace(source)


def mm9_liquid_textures() -> set[str]:
    """The texture names of every MM9 liquid: this helper's and the maps' own entries in the review root's table."""
    import yaml
    table = yaml.safe_load(review_root.mirror_path(TABLE).read_text())
    names = {name.lower() for liquid in table["liquids"] if "mm9" in (liquid.get("worlds") or [])
             for name in liquid.get("match", {}).get("texture_names", [])}
    return names | set(SURFACES.values()) | {see_through_name(f, o) for f, os in SEE_THROUGH.items() for o in os}


def _normal(points: np.ndarray) -> np.ndarray:
    """Newell-style sum of corner cross products: robust to collinear corners."""
    normal = np.zeros(3)
    for k in range(1, len(points) - 1):
        normal += np.cross(points[k] - points[0], points[k + 1] - points[0])
    return normal


def _inside(point, ring: np.ndarray) -> bool:
    x, y = point
    hit = False
    for (x1, y1), (x2, y2) in zip(ring, np.roll(ring, -1, axis=0)):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def _texture(path: str) -> str:
    return Path(str(path).replace("\\", "/")).name.lower()


def mm9_surfaces(source) -> list[tuple]:
    """MM9's drawn water tops: (object name, opacity, xy ring, top height, bottom height) in native units (a brush
    polygon's bottom is its top)."""
    found = []
    for model in source.world.world_models:
        found_object = source.by_name.get(model.name.lower())
        properties = found_object["properties"] if found_object else {}
        points = source.project.native(np.array(model.points, float))
        if "SurfaceAlpha" in properties:
            if not properties.get("ShowSurface"):
                continue
            sprite = _texture(properties.get("SpriteSurfaceName", ""))
            if sprite not in TEXTURE_ALPHA:
                continue                      # Water2.spr (Bathhouse's never-built tunnels): not in the extract
            low, high = points.min(0), points.max(0)
            ring = np.array([[low[0], low[1]], [high[0], low[1]], [high[0], high[1]], [low[0], high[1]]])
            found.append((model.name, float(properties["SurfaceAlpha"]) * TEXTURE_ALPHA[sprite], ring, high[2],
                          low[2]))
            continue
        alpha = properties.get("Alpha")
        alpha = 1.0 if alpha is None else float(alpha)
        for poly in model.polies:
            surface = model.surfaces[poly.surface_index]
            texture = _texture(model.textures[surface.texture_index])
            if texture not in TEXTURE_ALPHA or surface.flags & LT_INVISIBLE:
                continue
            ring = points[poly_ring(poly)]
            normal = _normal(ring)
            if abs(normal[2]) < 0.7 * np.linalg.norm(normal):
                continue
            opacity = alpha * TEXTURE_ALPHA[texture] if surface.flags & LT_TRANSLUCENT else 1.0
            height = ring[:, 2].mean()
            found.append((model.name, opacity, ring[:, :2], height, height))
    return found


class _BedFloors:
    """has_bed's candidate floors (faces of `geometry` with normal z >= 0.3) as arrays: room, index and a plan box a
    unit wider than the face, so a sample tests only the floors whose box holds it (the scan of every face for every
    sample of every water face took four minutes of Frosgard's build)."""
    def __init__(self, geometry: dict, faces: list):
        self.entries = [(face["index"],) + geometry[face["index"]] for face in faces
                        if face["index"] in geometry and not geometry[face["index"]][1][2] < 0.3]
        self.rooms = np.array([face["room_number"] for face in faces if face["index"] in geometry
                               and not geometry[face["index"]][1][2] < 0.3], dtype=np.int64)
        self.index = np.array([entry[0] for entry in self.entries], dtype=np.int64)
        self.low = np.array([entry[1][:, :2].min(0) - 1.0 for entry in self.entries]).reshape(-1, 2)
        self.high = np.array([entry[1][:, :2].max(0) + 1.0 for entry in self.entries]).reshape(-1, 2)

    def under(self, sample, face_index: int, rooms: set) -> bool:
        near = np.flatnonzero((self.index != face_index) & np.isin(self.rooms, list(rooms))
                              & (self.low[:, 0] <= sample[0]) & (sample[0] <= self.high[:, 0])
                              & (self.low[:, 1] <= sample[1]) & (sample[1] <= self.high[:, 1]))
        for k in near:
            _, other_points, normal = self.entries[k]
            if not _inside(sample[:2], other_points[:, :2]):
                continue
            height = other_points[0][2] - (normal[0] * (sample[0] - other_points[0][0])
                                           + normal[1] * (sample[1] - other_points[0][1])) / normal[2]
            if height < sample[2] - 1.0:
                return True
        return False


def has_bed(face: dict, geometry: dict, faces: list, neighbours: dict, floors: _BedFloors | None = None) -> bool:
    """A floor of the face's room or a room a portal joins to it under at least half of five points of it (its centre
    and its corners pulled in). A sealed room under a wading floor is joined to nothing, so it is no bed. floors: the
    candidate floors of these faces, built once by a caller asking for many faces."""
    floors = floors if floors is not None else _BedFloors(geometry, faces)
    points, _ = geometry[face["index"]]
    centre = points.mean(0)
    samples = [centre] + [centre + 0.7 * (point - centre) for point in points[:4]]
    rooms = {face["room_number"], face["room_behind_number"]}
    rooms |= set().union(*(neighbours.get(room, set()) for room in list(rooms)))
    under = sum(1 for sample in samples if floors.under(sample, face["index"], rooms))
    return under * 2 >= len(samples)


def surfaces(blv: dict, source=None, not_water=()) -> tuple[dict[int, str], list[tuple]]:
    """Face index -> liquid texture name for the visible, horizontal water faces, and a report row per face
    (index, family, MM9 object, opacity, see-through, name). A face's MM9 object is the drawn water top whose box holds
    its centre with the face no more than `MATCH_HEIGHT` above its top or below its bottom (a volume's mover surface is
    stored inside it), the nearest top first. An object's faces are see-through together, when it is translucent and
    at least half of them have a bed (`has_bed`): no patchwork of opaque tiles in a see-through pool. Without a DAT
    source every surface is opaque. A face whose object is in `not_water` (overrides.yml `liquids: {not_water: [...]}`:
    a solid drawn with a water sprite, Bootcamp's orbs) is no liquid face: it keeps its texture."""
    vertices = np.array([[v["x"], v["y"], v["z"]] if isinstance(v, dict) else v for v in blv["vertices"]], float)
    geometry, neighbours = {}, {}
    for face in blv["faces"]:
        if face["is_portal"]:
            neighbours.setdefault(face["room_number"], set()).add(face["room_behind_number"])
            neighbours.setdefault(face["room_behind_number"], set()).add(face["room_number"])
        if face["is_portal"] or face["attributes"] & INVISIBLE or len(face["vertex_indices"]) < 3:
            continue
        points = vertices[face["vertex_indices"]]
        normal = _normal(points)
        if np.linalg.norm(normal) > 1e-6:
            geometry[face["index"]] = (points, normal / np.linalg.norm(normal))
    tops = mm9_surfaces(source) if source is not None else []
    floors = _BedFloors(geometry, blv["faces"])
    rows = []
    for face in blv["faces"]:
        alias = face["texture_name"].lower()
        family = FAMILIES.get(alias)
        if family is None or face["index"] not in geometry:
            continue
        points, normal = geometry[face["index"]]
        if abs(normal[2]) <= 0.5:
            continue
        centre = points.mean(0)
        best = None
        for name, opacity, ring, top, bottom in tops:
            reach = MATCH_HEIGHT + MOVED_SURFACES.get(name, 0.0)
            if bottom - MATCH_HEIGHT <= centre[2] <= top + reach and _inside(centre[:2], ring):
                distance = abs(top - centre[2])
                if best is None or distance < best[0]:
                    best = (distance, name, round(opacity, 2))
        if best is not None and best[1] in not_water:
            continue
        opacity = best[2] if best else 1.0
        bed = opacity < 1.0 and has_bed(face, geometry, blv["faces"], neighbours, floors)
        rows.append([face, alias, family, best[1] if best else None, opacity, bed])
    beds = Counter()
    for _, _, _, name, _, bed in rows:
        beds[(name, bed)] += 1
    found, report = {}, []
    for face, alias, family, name, opacity, _ in rows:
        see_through = opacity < 1.0 and beds[(name, True)] * 2 >= beds[(name, True)] + beds[(name, False)]
        if see_through:
            if opacity not in SEE_THROUGH.get(family, ()):
                raise SystemExit(f"liquids: face {face['index']} ({name}) is {family} at {opacity}: add it to "
                                 f"SEE_THROUGH")
            texture = see_through_name(family, opacity)
        else:
            texture = SURFACES.get(alias)
        if texture is not None:
            found[face["index"]] = texture
        report.append((face["index"], family, name, opacity, see_through, texture or alias))
    return found, report


def apply_to(blv_path: Path, scene: dict, source=None) -> dict:
    """Retexture the surfaces and keep every liquid face out of the translucent faces; returns the counts."""
    sys.path.insert(0, str(ROOT))
    from util.map_export import parse_blv_file
    blv = parse_blv_file(blv_path)["payload"]
    not_water = set((source.project.overrides.get("liquids") or {}).get("not_water") or []) if source else set()
    retexture, report = surfaces(blv, source, not_water)
    overrides = scene.setdefault("initial_state", {}).setdefault("face_attribute_overrides", [])
    by_face = {entry["face_index"]: entry for entry in overrides}
    for index, name in sorted(retexture.items()):
        if index in by_face:
            by_face[index]["texture_name"] = name
        else:
            overrides.append({"face_index": index, "texture_name": name})
    # An empty list stays: the game refuses an initial_state without the key (Afterworld, no overrides at all).
    liquids = mm9_liquid_textures()
    liquid_faces = set(retexture) | {f["index"] for f in blv["faces"] if f["texture_name"].lower() in liquids}
    removed, kept = 0, []
    for entry in scene.get("translucent_faces", []):
        faces = [f for f in entry["faces"] if f not in liquid_faces]
        removed += len(entry["faces"]) - len(faces)
        if faces:
            kept.append(dict(entry, faces=faces))
    if "translucent_faces" in scene:
        if kept:
            scene["translucent_faces"] = kept
        else:
            del scene["translucent_faces"]
    see_through = Counter(row[5] for row in report if row[4])
    return {"liquid_surfaces": len(retexture), "liquid_see_through": sum(see_through.values()),
            "liquid_faces_untranslucent": removed, "see_through_names": dict(sorted(see_through.items())),
            "report": report}


def apply(build, scene: dict) -> None:
    """A map's `scene` hook, last: install the entries (installing builds), retexture the surfaces, keep liquids out of
    the translucent faces."""
    if build.project.install:
        install()
    counts = apply_to(build.runtime / build.project.map, scene, build.source)
    build.stats.update({key: value for key, value in counts.items() if isinstance(value, int)})
    if "translucent_faces" in build.stats:
        build.stats["translucent_faces"] = sum(len(e["faces"]) for e in scene.get("translucent_faces", []))


def apply_installed(stem: str) -> dict:
    """The same for a map already installed in the review root (its BLV and scene as they are there)."""
    from dungeon.source import Project, Source
    relative = f"worlds/mm9/maps/{stem}.scene.yml"
    path = review_root.mirror_path(relative)
    text = path.read_text()
    scene = json.loads(text)
    source = Source(Project.load(COMMON.parent / f"mm9r_{stem}"))
    counts = apply_to(review_root.mirror_path(f"worlds/mm9/maps/{stem}.blv"), scene, source)
    new = json.dumps(scene, indent=1) + "\n"
    if new != text:
        review_root.install(relative, new.encode())
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--scenes", nargs="*", default=[], help="installed maps to apply them to (stems)")
    parser.add_argument("--report", action="store_true", help="print every water face's MM9 surface and name")
    args = parser.parse_args()
    install()
    for stem in args.scenes:
        counts = apply_installed(stem)
        report = counts.pop("report")
        print(stem, counts)
        rows = Counter((row[1], row[2], row[3], row[4], row[5]) for row in report)
        for (family, name, opacity, bed, texture), count in sorted(rows.items(), key=str):
            print(f"  {count:4d} x {family} {name or '-'} opacity {opacity} bed {bed} -> {texture}")
            if args.report:
                print("       faces", [row[0] for row in report if (row[1], row[2], row[3], row[4], row[5])
                                       == (family, name, opacity, bed, texture)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
