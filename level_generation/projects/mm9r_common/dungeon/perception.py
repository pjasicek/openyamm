"""
MM9's PerceptionBrushes as hint faces on every converted map (FINAL_REBUILD_WORK.md C3; generalised from Anskram Keep's,
Drangheim Prison's and the Training Hall's own helpers). A PerceptionBrush is a world model whose one textured polygon
(Sprites\\Perception.spr or Perception2.spr: the red glow; the rest is Invisible.dtx) MM9 shows to a party whose
Perception reaches the brush's PerceptionValue (PerceptionBrush.cpp in object.lto, perception_difficulties_by_model_name).

Each glow polygon becomes an untouchable face (node TRIGGER_hint_<brush>_<i>, in the room of the air beside it: on
the side away from the surface it lies over, whichever way MM9 turned its polygon, 2026-11-11) with the cog HINT_COG_BASE + the brush's DAT index; the scene draws them translucent from both sides (`scene_faces`), the
.spr's frames animate them (`install_frames`), and the map Lua (objects.shared_lines) hides each one from a party
without the Perception for it (evt.CheckSkill, every 3 s and on load) or for good once the map sets HintOff<cog>.

A map whose own hooks place hints (any TRIGGER_perception_ node: the eleven dungeons that did it by hand) keeps its own;
overrides.yml `map: {perception_hints: false}` turns the shared ones off.
"""

from __future__ import annotations

import numpy as np

from . import source as _source  # noqa: F401 (puts the MM9 import tools on sys.path)
from .package import room_id
from .rooms import _side_room
from transcode_mm9_dat_to_odm import perception_difficulties_by_model_name  # noqa: E402

HINT_COG_BASE = 23000               # a brush's faces: cog 23000 + its DAT index (destructibles use 20000 + index)
HINT_POLL_EVENT = 901               # the hints' 3 s check (lua.TOUCH_POLL_EVENT is 900)
PERCEPTION_SKILL = 29               # evt.CheckSkill's id: the party's best Perception value (mastery counted)
HINT_OPACITY = 0.5                  # the brushes' Alpha (0.5-0.75 in MM9; the dungeons draw them at 0.5)
OVERLAY_REACH = 4.0                 # LT: how far off a surface a hint lies over it (MM9's sit 1-2 LT off)
OVERLAY_SLACK = 1.0                 # LT: a hint's centre over a face's box, with this much to spare
FRAME_FLAGS = {(True, True): "0x3\tHasMore,First", (False, True): "0x1\tHasMore", (False, False): "0x0\t"}


class Surfaces:
    """The solid, visible faces a hint may lie over (static and glass faces, destructible brushes), with their planes
    and boxes for a quick search."""
    def __init__(self, polygons: list):
        self.polygons = [p for p in polygons if p.role in ("static", "glass")]
        self.normals = np.array([p.normal for p in self.polygons]).reshape(-1, 3)
        self.offsets = np.array([p.normal @ p.points[0] for p in self.polygons])
        self.low = np.array([p.points.min(0) for p in self.polygons]).reshape(-1, 3)
        self.high = np.array([p.points.max(0) for p in self.polygons]).reshape(-1, 3)


def _overlaid_side(polygon, surfaces: Surfaces) -> float:
    """+1 or -1: the side of the hint's normal on which the surface it lies over is (a parallel solid face within
    OVERLAY_REACH of its plane, under its centre); 0 when it lies over none."""
    if not surfaces.polygons:
        return 0.0
    centre = polygon.points.mean(0)
    normal = polygon.normal
    parallel = np.abs(surfaces.normals @ normal) > 0.95
    distance = surfaces.normals @ centre - surfaces.offsets           # the centre's height over each face's plane
    near = parallel & (np.abs(distance) <= OVERLAY_REACH)
    # the centre dropped onto each face's plane, inside that face's box
    foot = centre[None, :] - distance[:, None] * surfaces.normals
    inside = np.all((foot >= surfaces.low - OVERLAY_SLACK) & (foot <= surfaces.high + OVERLAY_SLACK), axis=1)
    candidates = np.flatnonzero(near & inside)
    if candidates.size == 0:
        return 0.0
    nearest = candidates[np.argmin(np.abs(distance[candidates]))]
    along = float(normal @ (foot[nearest] - centre))
    return 1.0 if along > 0.0 else -1.0 if along < 0.0 else 0.0


def own_hints(build) -> bool:
    return any(node.startswith("TRIGGER_perception_") for node in build.package.nodes)


def place(build) -> dict:
    """The hint faces of every PerceptionBrush; returns {cog: PerceptionValue} (build.shared['hints'])."""
    if build.project.overrides["map"].get("perception_hints", True) is False or own_hints(build):
        return {}
    source, package, rooms = build.source, build.package, build.content.rooms
    difficulties = perception_difficulties_by_model_name(source.world)
    models = {name.lower(): name for name in source.models}
    hints, textures = {}, set()
    build.hint_nodes = []
    surfaces = Surfaces(build.polygons + [p for polygons in getattr(build, "destructible_brushes", {}).values()
                                          for p in polygons])
    for o in source.objects:
        if o["class"] != "PerceptionBrush" or o["name"].lower() not in difficulties or o["name"].lower() not in models:
            continue
        name = models[o["name"].lower()]
        parts = [p for p in source.polygons(name) if "perception" in p.texture.lower()]
        missing = sorted({p.texture for p in parts if p.texture.lower() not in source.aliases})
        if missing:
            raise SystemExit(f"{name}: hint texture {missing} has no alias in the map's material aliases")
        cog = HINT_COG_BASE + o["index"]
        for i, polygon in enumerate(parts):
            # A hint lies over a surface: its room is the air on the other side of it. Probing its own normal side
            # first crossed a wall thinner than the probe (Thjorgard's training hall bricks, 20 units, voxels 82):
            # the glow went to the hut behind them, a room never drawn from the roof where the party stands.
            first = -_overlaid_side(polygon, surfaces) or 1.0
            room = room_id(_side_room(rooms, polygon, first) or _side_room(rooms, polygon, -first)
                           or rooms.owner(polygon.points.mean(0)))
            node = f"TRIGGER_hint_{name}_{i}"
            package.add_polygon(node, polygon, build.stats)
            package.room_nodes[room].append(node)
            package.metadata["surfaces"].append({"id": node[8:], "source_node": node, "flags": ["untouchable"],
                                                 "cog_number": cog})
            build.hint_nodes.append(node)
            textures.add(polygon.texture.lower())
        if parts:
            hints[cog] = difficulties[o["name"].lower()]
    build.hint_textures = textures
    build.stats["perception_hints"] = len(hints)
    return hints


def scene_faces(build, scene: dict) -> None:
    """The hint faces (faces.yml groups of the TRIGGER_hint_ nodes) drawn translucent, two-sided; the .spr frames."""
    import yaml
    nodes = set(getattr(build, "hint_nodes", []))
    if not nodes:
        return
    groups = yaml.safe_load((build.runtime / f"{build.project.stem}.faces.yml").read_text()) or []
    faces = sorted(face for group in groups if group["source_node"] in nodes for face in group["face_ids"])
    if not faces:
        return
    scene.setdefault("translucent_faces", []).append({"faces": faces, "opacity": HINT_OPACITY,
                                                      "tint": [1.0, 1.0, 1.0], "two_sided": True})
    if build.project.install:
        for texture in sorted(build.hint_textures):
            install_frames(build, texture)


def install_frames(build, texture: str) -> None:
    """An MM9 .spr as a texture frame sequence. The table is the engine's and only the review root's copy changes (as
    the dungeons' own: a world contribution would take it at integration)."""
    import review_root
    from . import tables
    entry = build.source.aliases.get(texture)
    if entry is None or not entry.get("animation_frames"):
        return
    frames = [entry["alias"]] + [frame["alias"] for frame in entry["animation_frames"][1:]]
    relative = "engine/data_tables/texture_frame_data.txt"
    with tables.locked("review_tables.lock"):
        text = review_root.mirror_path(relative).read_text()
        if f"\n{frames[0]}\t" in text:
            return
        rows = [f"{name}\t0\t1\t{len(frames) if i == 0 else 0}\t{FRAME_FLAGS[i == 0, i < len(frames) - 1]}"
                for i, name in enumerate(frames)]
        review_root.install(relative, (text.rstrip("\n") + "\n" + "\n".join(rows) + "\n").encode())

