#!/usr/bin/env python3
"""
MM9's sprite surfaces that are no liquid, animated and translucent as MM9 draws them (devdocs/mm9_rework/
MM9_VISUAL_PROPERTIES.md "Bit 0x4000", "Translucent 0x8", "Brush Alpha"; the user, 2026-11-10: Wizard's Lab's portal
and crystal buttons were static and opaque, MM9's are translucent and animated). A surface with bit 0x4000 draws a
.spr: a frame list with its rate (`uint32 frames, fps, 0, 0, 0`, then the frame names).

A map opts in with overrides.yml `spr_surfaces` ({} for the defaults); Build.run calls apply() after the map's own scene
hook, so after liquids.apply:

- Frames: every .spr that a face of the compiled BLV still draws (a face not retextured to a liquid, whose texture is
  no liquid) gets its frame sequence in the texture frame table (`install_frames`: the review root's copy, as the
  perception hints' and the dungeons' own; a frame lasts MM9's rate rounded to the table's 1/16 s).
- Translucency: a face whose MM9 polygon (of the same texture, the one whose plane and outline hold the face's centre)
  has the Translucent flag is drawn translucent at its brush's `Alpha` (1 for the main world): MM9 blends at the
  texture's alpha times the brush's, and the shader multiplies the texture's alpha in. A face at Alpha 1 whose texture
  has no alpha stays opaque (it would blend nothing). Two-sided when the brush's polygons of that texture lie in one
  plane (a sheet: a gate's shimmer), one-sided on a solid (an orb), as MM9 culls the back of a solid.
- A face the map's hooks already made translucent keeps its entry (Yanmir's Fort's gate sheets, Wizard's Lab's
  stations, Dark Passageway's flame cage through `glass`); `skip` lists DAT models whose faces stay as they are.

    spr_surfaces:
      skip: [spheres]          # optional: DAT models (world models) left opaque, with the reason in a comment
      translucent: false       # optional: frames only, the scene unchanged

Only the scene's `translucent_faces` and the frame table change: the BLV is the same, so the saved map identity stays
valid. The indoor lighting bake records the scene file among its sources (tools/lighting/stale_bakes.py), so a map
whose translucent faces change lists as stale until it is baked again; frames alone change no map file.

    cd level_generation/projects/mm9r_common
    python3 -m dungeon.spr_surfaces --frames ../mm9r_<map>... [--root isleofashes_blv_root]
        # the frames of maps already installed in a review root (their BLV and scene as they are there)
"""

from __future__ import annotations

import struct
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from .source import ROOT, SKIPPED_MODELS

LT_TRANSLUCENT = 0x8
FRAME_FLAGS = {(True, True): "0x3\tHasMore,First", (False, True): "0x1\tHasMore", (False, False): "0x0\t"}
FRAME_TABLE = "engine/data_tables/texture_frame_data.txt"
SPRITES = ROOT / "mm9/extracted/SPRITES/SPRITES"
TABLE_TICKS_PER_SECOND = 16         # the frame table's lengths count 1/16 s (TextureFrameTable: x 8 of 128 ticks/s)
PLANE_REACH = 2.0                   # native units: a face lies on its MM9 polygon's plane within this
INSIDE_REACH = 2.0                  # and its centre inside the polygon's outline within this


def sprite_rate(texture: str) -> int | None:
    """The frames per second a .spr file names (its second word), or None when the extract lacks it."""
    relative = texture.replace("\\", "/").split("/", 1)[-1] if texture.lower().startswith("sprites") else texture
    wanted = relative.replace("\\", "/").lower()
    for path in SPRITES.rglob("*"):
        if path.is_file() and path.relative_to(SPRITES).as_posix().lower() == wanted:
            return struct.unpack("<II", path.read_bytes()[:8])[1]
    return None


def frame_rows(entry: dict, fps: int | None) -> list[str]:
    """The frame table rows of an alias entry with animation frames (the .spr alias draws the first frame)."""
    frames = [entry["alias"]] + [frame["alias"] for frame in entry["animation_frames"][1:]]
    length = max(1, round(TABLE_TICKS_PER_SECOND / fps)) if fps else 1
    return [f"{name}\t0\t{length}\t{len(frames) * length if i == 0 else 0}\t{FRAME_FLAGS[i == 0, i < len(frames) - 1]}"
            for i, name in enumerate(frames)]


def install_frames(build, texture: str) -> bool:
    """An MM9 .spr as a texture frame sequence in the review root's frame table (unless it is there already); returns
    whether rows were added."""
    import review_root
    from . import tables
    entry = build.source.aliases.get(texture.lower())
    if entry is None or not entry.get("animation_frames"):
        return False
    rows = frame_rows(entry, sprite_rate(texture))
    with tables.locked("review_tables.lock"):
        text = review_root.mirror_path(FRAME_TABLE).read_text()
        if f"\n{entry['alias']}\t" in text:
            return False
        review_root.install(FRAME_TABLE, (text.rstrip("\n") + "\n" + "\n".join(rows) + "\n").encode())
    return True


def _liquid_names() -> set[str]:
    import liquids
    return liquids.mm9_liquid_textures()


def _sprite_faces(build, blv: dict, scene: dict) -> dict[str, list[dict]]:
    """.spr source texture (lower case) -> the BLV faces that draw it and are no liquid (perception hints excluded:
    perception.py)."""
    by_alias = {}
    for texture, entry in build.source.aliases.items():
        if texture.endswith(".spr") and "perception" not in texture and entry.get("animation_frames"):
            by_alias.setdefault(entry["alias"].lower(), texture)
    overrides = {e["face_index"]: e["texture_name"].lower()
                 for e in scene.get("initial_state", {}).get("face_attribute_overrides", []) if e.get("texture_name")}
    liquid = _liquid_names()
    found = defaultdict(list)
    for face in blv["faces"]:
        texture = by_alias.get(str(face.get("texture_name", "")).lower())
        if texture is None or face["is_portal"]:
            continue
        if overrides.get(face["index"], face["texture_name"].lower()) in liquid:
            continue
        found[texture].append(face)
    return found


def _mm9_polygons(build, texture: str, skip: set) -> list[dict]:
    """The DAT's visible polygons of a texture: native ring, plane, Translucent flag, brush Alpha and whether their
    brush's polygons of the texture form one plane (a sheet)."""
    source, native = build.source, build.project.native
    out, per_model = [], defaultdict(list)
    for name in source.models:
        if name.startswith(SKIPPED_MODELS) or name.lower() in skip:
            continue
        try:
            polygons = source.polygons(name)
        except KeyError:                    # a texture without alias (TOD_Sky's starfield): no .spr of ours
            continue
        found = source.by_name.get(name.lower())
        alpha = float(found["properties"].get("Alpha", 1.0)) if found else 1.0
        for polygon in polygons:
            if polygon.texture.lower() != texture or polygon.role == "invisible":
                continue
            ring = native(polygon.points)
            normal = np.cross(ring[1] - ring[0], ring[2] - ring[0])
            for k in range(2, len(ring) - 1):
                normal = normal + np.cross(ring[k] - ring[0], ring[k + 1] - ring[0])
            normal = normal / max(np.linalg.norm(normal), 1e-9)
            record = {"model": name, "ring": ring, "normal": normal, "offset": float(normal @ ring[0]),
                      "translucent": bool(polygon.flags & LT_TRANSLUCENT), "alpha": round(alpha, 3)}
            out.append(record)
            per_model[name].append(record)
    for records in per_model.values():
        first = records[0]
        sheet = all(abs(float(r["normal"] @ first["normal"])) > 0.999
                    and abs(float(first["normal"] @ r["ring"][0]) - first["offset"]) < 1.0 for r in records)
        for r in records:
            r["sheet"] = sheet
    return out


def _inside(point: np.ndarray, record: dict) -> bool:
    """The point (on the polygon's plane) inside its convex outline within INSIDE_REACH."""
    ring, normal = record["ring"], record["normal"]
    sign = 0.0
    for a, b in zip(ring, np.roll(ring, -1, axis=0)):
        edge = b - a
        length = np.linalg.norm(edge)
        if length < 1e-6:
            continue
        side = float(np.cross(edge, point - a) @ normal) / length
        if side < -INSIDE_REACH:
            if sign > 0:
                return False
            sign = -1.0
        elif side > INSIDE_REACH:
            if sign < 0:
                return False
            sign = 1.0
    return True


def _match(face_points: np.ndarray, records: list[dict]) -> dict | None:
    centre = face_points.mean(0)
    best = None
    for record in records:
        distance = abs(float(record["normal"] @ centre) - record["offset"])
        if distance > PLANE_REACH or not _inside(centre, record):
            continue
        if best is None or distance < best[0]:
            best = (distance, record)
    return best[1] if best else None


def apply(build, scene: dict) -> None:
    """The map's .spr faces: frames installed (installing builds) and the translucent ones as `translucent_faces`
    entries (module note). Stats: `spr_<alias>` faces per .spr, `spr_translucent`, `spr_unmatched`."""
    settings = build.project.overrides.get("spr_surfaces")
    if settings is None:
        return
    settings = settings or {}
    skip = {name.lower() for name in settings.get("skip") or []}
    translucent = settings.get("translucent", True)
    sys.path.insert(0, str(ROOT))
    from util.map_export import parse_blv_file
    from .rooms import native_has_alpha
    blv = parse_blv_file(build.runtime / build.project.map)["payload"]
    vertices = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], float)
    taken = {face for entry in scene.get("translucent_faces", []) for face in entry["faces"]}
    groups = defaultdict(list)
    unmatched = 0
    for texture, faces in sorted(_sprite_faces(build, blv, scene).items()):
        alias = build.source.aliases[texture]["alias"]
        build.stats[f"spr_{alias.lower()}"] = len(faces)
        if build.project.install:
            install_frames(build, texture)
        records = _mm9_polygons(build, texture, skip)
        has_alpha = native_has_alpha(alias)
        for face in faces:
            if face["index"] in taken or not translucent:
                continue
            record = _match(vertices[face["vertex_indices"]], records)
            if record is None:
                unmatched += 1              # a volume's surface (water.py) or a skipped model: frames only
                continue
            if not record["translucent"] or (record["alpha"] >= 1.0 and not has_alpha):
                continue
            groups[(min(record["alpha"], 1.0), record["sheet"])].append(face["index"])
    entries = scene.setdefault("translucent_faces", [])
    for (opacity, two_sided), faces in sorted(groups.items()):
        entries.append({"faces": sorted(faces), "opacity": opacity, "tint": [1.0, 1.0, 1.0], "two_sided": two_sided})
    if not entries:
        del scene["translucent_faces"]
    build.stats["spr_translucent"] = sum(len(faces) for faces in groups.values())
    build.stats["spr_unmatched"] = unmatched


def install_installed(project_dir: Path) -> list[str]:
    """The frames of a map already installed in the review root: the .spr faces of its BLV and scene there."""
    import json
    import review_root
    from types import SimpleNamespace
    from util.map_export import parse_blv_file
    from .source import Project, Source
    project = Project.load(project_dir)
    build = SimpleNamespace(project=project, source=Source(project))
    maps = review_root.mirror_path("worlds/mm9/maps")
    blv = parse_blv_file(maps / project.map)["payload"]
    scene = json.loads((maps / f"{project.stem}.scene.yml").read_text())
    return [texture for texture in sorted(_sprite_faces(build, blv, scene)) if install_frames(build, texture)]


if __name__ == "__main__":
    import argparse
    sys.path.insert(0, str(ROOT))
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--frames", nargs="+", type=Path, required=True, metavar="PROJECT")
    parser.add_argument("--root", choices=["assets_dev", "isleofashes_blv_root"], default="assets_dev",
                        help="the review root under output/mm9_rework: isleofashes_blv_root for the regions, Bootcamp "
                             "and the Afterworld")
    arguments = parser.parse_args()
    import review_root as _review_root
    if arguments.root == "isleofashes_blv_root":         # as the region projects' convert.py redirect it
        _review_root.ASSETS = _review_root.REVIEW / "isleofashes_blv_root"
        _review_root.OWNED = _review_root.REVIEW / "isleofashes_blv_owned.txt"
    for directory in arguments.frames:
        print(directory.name, install_installed(directory))
