"""
Rooms and portals: the doorway portals (MM9's UserPortals and door leaves), the air voxels of the map, the archway
cuts of overrides.yml, the partition of the air into rooms, and the assignment of every face to the room in front
of it (split at portal planes or where the rooms' samples separate). The method is the Anskram Keep pilot's; see
../DUNGEON_PLAYBOOK.md.
"""

from __future__ import annotations

import colorsys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from .geometry import (SIX, Polygon, VoxelGrid, air_regions, clip, corner_ring, mark, mark_polygons,
                       rectangle_points, sample_polygon)


def leaf_rectangle(points: np.ndarray):
    """The doorway rectangle of a door leaf set (closed pose): its mid-plane, a vertical and a horizontal axis. A flat
    leaf (a ceiling slab or a hatch: less than half as tall as it is thick across) gets a horizontal rectangle, normal
    up: Verhoffin's and Inventastorca's ceiling slabs the busts fall through (KingKong.scr ForceFall)."""
    flat = points - points.mean(0)
    horizontal = flat[:, [0, 2]]
    _, _, vt = np.linalg.svd(horizontal - horizontal.mean(0), full_matrices=False)
    along = np.array([vt[0][0], 0.0, vt[0][1]])
    normal = np.array([vt[1][0], 0.0, vt[1][1]])
    up = np.array([0.0, 1.0, 0.0])
    a = flat @ along
    thickness = float((flat @ normal).max() - (flat @ normal).min())
    if float(np.ptp(points[:, 1])) < 0.5 * thickness:
        b = flat @ normal
        centre = points.mean(0) + along * (a.max() + a.min()) / 2 + normal * (b.max() + b.min()) / 2
        centre[1] = (points[:, 1].max() + points[:, 1].min()) / 2
        return {"centre": centre, "normal": up, "axis_a": along, "half_a": (a.max() - a.min()) / 2,
                "axis_b": normal, "half_b": (b.max() - b.min()) / 2}
    centre = points.mean(0) + along * (a.max() + a.min()) / 2
    y = points[:, 1]
    centre[1] = (y.max() + y.min()) / 2
    plane = normal @ points.mean(0)
    centre = centre - normal * (normal @ centre - plane)
    return {"centre": centre, "normal": normal, "axis_a": along, "half_a": (a.max() - a.min()) / 2,
            "axis_b": up, "half_b": (y.max() - y.min()) / 2}


def leaf_points(source, model: str, rule: dict) -> np.ndarray:
    """A door leaf's points in its shut pose: as authored, or moved by MoveDir x MoveDist for `authored_open` leaves
    (MM9 authors them open and its open shuts them; movers.py builds them shut), or swung back by its angle for an
    `authored_open` `rotate` leaf, so the doorway rectangle covers the opening the shut leaves close."""
    points = np.array(source.models[model].points, float)
    if rule.get("authored_open") and rule.get("motion") == "rotate":
        from .rotation import authored_open_points
        points = authored_open_points(points, source.properties(model))
    elif rule.get("authored_open"):
        properties = source.properties(model)
        shift = np.asarray(properties["MoveDir"], float)
        points = points + shift / np.linalg.norm(shift) * float(properties["MoveDist"])
    return points


def mover_groups(plan: dict) -> dict:
    groups = defaultdict(list)
    for name, rule in plan["movers"].items():
        groups[rule["group"]].append(name)
    return dict(sorted(groups.items()))


def door_portals(source, plan: dict) -> list[dict]:
    """One portal per doorway: MM9's UserPortals, and the leaves' rectangle for doors without one (or with a
    diagonal one). Each doorway portal then moves to its leaves' face on the side of its normal's negative side."""
    portals = []
    skip = {name.lower() for name in (source.project.overrides.get("skip_user_portals") or [])}
    for user_portal in source.models["VisBSP"].user_portals:
        if user_portal.name.lower() in skip:
            continue
        centre, dims = np.array(user_portal.center), np.array(user_portal.dims)
        thin = int(np.argmin(dims))
        normal = np.zeros(3); normal[thin] = 1.0
        if dims[0] > 1 and dims[2] > 1:                    # a diagonal doorway: take the plane from its door leaves
            continue
        in_plane = [axis for axis in (0, 2) if axis != thin]
        axis_a = np.zeros(3); axis_a[in_plane[0]] = 1.0
        portals.append({"name": user_portal.name, "kind": "user_portal", "centre": centre, "normal": normal,
                        "axis_a": axis_a, "half_a": float(dims[in_plane[0]]), "axis_b": np.array([0.0, 1.0, 0.0]),
                        "half_b": float(dims[1])})
    named = {p["name"].lower() for p in portals}
    for group, members in mover_groups(plan).items():
        rule = plan["movers"][members[0]]
        if not rule.get("doorway"):
            continue
        portal_name = rule.get("portal") or group
        if portal_name.lower() in named:
            continue
        points = np.concatenate([leaf_points(source, m, rule) for m in members])
        rectangle = leaf_rectangle(points)
        rectangle.update({"name": portal_name, "kind": "door_leaves"})
        portals.append(rectangle)
        named.add(portal_name.lower())
    # Each doorway portal moves from the middle of its leaves to their face on its normal's negative side, so the
    # leaves stand wholly in the room on the other side. The engine collides a party with door faces of the next
    # room only once its sphere reaches the portal: with the portal through the middle of thick leaves (Anskram's
    # gates: 82 units) the party got half way into a closed leaf from the other room before meeting it.
    leaves = {}
    for group, members in mover_groups(plan).items():
        rule = plan["movers"][members[0]]
        if rule.get("doorway"):
            leaves[(rule.get("portal") or group).lower()] = np.concatenate(
                [leaf_points(source, m, rule) for m in members])
    for portal in portals:
        points = leaves.get(portal["name"].lower())
        if points is None:
            continue
        normal = portal["normal"]
        face = float((points @ normal).min()) - 0.5
        portal["centre"] = portal["centre"] + normal * (face - float(normal @ portal["centre"]))
        portal["shifted_to_leaf_face"] = True
    return portals


def build_voxels(polygons: list[Polygon], source, extra_seeds=()):
    """The voxel grid over the map, its solid voxels (static faces) and the air reachable from the seeds: starts,
    lights, chests, triggers, monsters (and any extra seed points of overrides.yml `seeds`; minus the objects named in
    `seed_exclude`)."""
    voxel = source.project.voxel
    points = np.concatenate([p.points for p in polygons])
    grid = VoxelGrid(points.min(0), points.max(0), voxel)
    solid = np.zeros(grid.shape, bool)
    mark_polygons(grid, solid, [polygon.points for polygon in polygons if polygon.role == "static"], voxel / 4)
    seeds = []
    classes = source.project.seed_classes | source.project.monster_classes
    # overrides.yml `seed_exclude`: objects of a seed class that stand outside the map (relay triggers, script
    # holders), which would flood the outside air
    excluded = {name.lower() for name in (source.project.overrides.get("seed_exclude") or [])}
    for o in source.objects:
        if o["class"] in classes and o["name"].lower() not in excluded:
            seeds.append(o["properties"]["Pos"])
    seeds += [list(s) for s in extra_seeds]
    air, stats = air_regions(grid, solid, np.array(seeds, float))
    return grid, solid, air, stats


def portal_barrier(grid: VoxelGrid, portal: dict) -> np.ndarray:
    points = rectangle_points(portal["centre"], portal["axis_a"], portal["half_a"] + grid.size, portal["axis_b"],
                              portal["half_b"] + grid.size, grid.size / 4)
    return grid.index(points)


def face_halves(portal: dict) -> tuple[float, float]:
    """The half sizes of a rectangle portal's face: its rectangle grown by `face_grow` (one voxel, set when the rooms
    are labelled, build.geometry). The rectangle stops at the last air voxel, but the jambs, sill and lintel stand up to
    a voxel beyond it (a voxel a wall touches is solid): with the face at the rectangle, a strip of real air up to a
    voxel wide beside the opening had no portal face, so neither room was seen through it, and a floor in it took either
    room, putting a party standing there in the room across the portal (MM9 portal sweep 2026-11-08: Thjora Mine's
    archway, 41 units short of its jamb). A face running on into the wall only widens the aperture. A city's street cuts
    are grown by city/structure.py grow_cut_faces and its top portals have their own rings: no `face_grow`."""
    grow = float(portal.get("face_grow", 0.0))
    return portal["half_a"] + grow, portal["half_b"] + grow


def portal_corners(portal: dict) -> np.ndarray:
    """A rectangle portal's face corners (face_halves)."""
    half_a, half_b = face_halves(portal)
    return np.array([portal["centre"] + sa * portal["axis_a"] * half_a + sb * portal["axis_b"] * half_b
                     for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))])


def label_rooms(grid: VoxelGrid, air: np.ndarray, portals: list[dict]):
    barrier = np.zeros(grid.shape, bool)
    for portal in portals:
        cells = portal["cells"] if "cells" in portal else portal_barrier(grid, portal)
        barrier[cells[:, 0], cells[:, 1], cells[:, 2]] = True
    labels, count = ndimage.label(air & ~barrier, structure=SIX)
    # Pockets smaller than a cube of 4 voxels join the neighbour they touch most.
    sizes = np.bincount(labels.ravel(), minlength=count + 1)       # (ndimage.sum of ones: 7 s on a city)
    small = [index for index in range(1, count + 1) if sizes[index] < 64]
    boxes = ndimage.find_objects(labels)
    for index in small:
        # within the pocket's box grown by a voxel (a dilation reaches no further; the whole grid took 0.4 s a pocket)
        box = tuple(slice(max(part.start - 1, 0), part.stop + 1) for part in boxes[index - 1])
        window = labels[box]
        region = window == index
        ring = ndimage.binary_dilation(region, structure=SIX) & ~region
        neighbours = Counter(int(v) for v in window[ring] if v and v != index and sizes[v] >= 64)
        if neighbours:
            window[region] = neighbours.most_common(1)[0][0]
    # Barrier voxels in the air take the label of a neighbour (so faces in a doorway find a room).
    for _ in range(3):
        missing = air & (labels == 0)
        if not missing.any():
            break
        grown = ndimage.grey_dilation(labels, footprint=SIX)
        labels[missing] = grown[missing]
    # Renumber densely, ordered by position (south to north, west to east).
    present = sorted(set(np.unique(labels)) - {0})
    # each room's centre: sums of whole voxel indices, exact in float64 (as ndimage.center_of_mass, 8 s on a city)
    size = labels.max() + 1
    counts = np.bincount(labels.ravel(), minlength=size).astype(float)
    sums = []
    for axis in range(3):
        total = np.zeros(size)
        for coordinate in range(labels.shape[axis]):
            total += coordinate * np.bincount(np.take(labels, coordinate, axis=axis).ravel(), minlength=size)
        sums.append(total)
    centres = [tuple(float(total[label] / counts[label]) for total in sums) for label in present]
    order = sorted(range(len(present)), key=lambda i: (round(centres[i][2] / 8), centres[i][0]))
    remap = np.zeros(labels.max() + 1, np.int32)
    for new, i in enumerate(order, start=1):
        remap[present[i]] = new
    return remap[labels], len(present)


def portal_sides(grid: VoxelGrid, labels: np.ndarray, portal: dict) -> tuple[int, int]:
    """The rooms on the two sides of a portal: the most common label over its rectangle (or its `side_points`, for a
    portal whose face is not its rectangle: a city's merged top portals), one voxel and a half off."""
    # a city's merged top portal's barrier is exactly one layer of voxels (city/structure.py): its sides are read on
    # the layers next to it and a voxel and a half off (a pocket of air under eaves may be one voxel high; a thin slab
    # may lie on the barrier's layer + 1 with the room's air over it)
    reaches = (1.0, 1.5) if "side_points" in portal else (1.5,)
    if "side_points" in portal:
        points = portal["side_points"]
    else:
        points = rectangle_points(portal["centre"], portal["axis_a"], portal["half_a"] * 0.8, portal["axis_b"],
                                  portal["half_b"] * 0.8, grid.size / 2)
    sides = []
    for sign in (1, -1):
        found = Counter()
        for reach in reaches:
            cells = grid.index(points + portal["normal"] * sign * grid.size * reach)
            found.update(int(v) for v in labels[cells[:, 0], cells[:, 1], cells[:, 2]] if v)
        sides.append(found.most_common(1)[0][0] if found else 0)
    return tuple(sides)


class NearestRoom:
    """For every voxel, the nearest voxel of labelled air (the voxels a surface touches are not air)."""
    def __init__(self, grid: VoxelGrid, labels: np.ndarray):
        self.grid, self.labels = grid, labels
        self.distance, self.nearest = ndimage.distance_transform_edt(labels == 0, return_indices=True)
        self.thin_walls = False         # map setting `thin_walls`: front() also looks straight ahead (see there)
        self.corner_samples = False     # map setting `corner_samples`: front() samples over the corners (see there)

    def front(self, polygon: Polygon, spacing: float = 24.0, with_samples: bool = False):
        """The room in front of each sample of the polygon (0: none; air behind the face does not count)."""
        found, samples = self._front(polygon, polygon.points, spacing)
        if self.corner_samples:
            # The fan from the first vertex makes a zero-area triangle for every pair of vertices on an edge through
            # it, and each is sampled like a whole triangle, so a merged polygon's T-junction vertices put most of its
            # votes on its edges (Sturmford City's magic shop ceiling, running over the walls to the street: 226
            # samples in the street, 124 in the shop). Over its corners the polygon is sampled evenly. A face that
            # only the plain samples see air in front of keeps them (a shelf board's top a voxel under the next board
            # sees the room only from its front edge), so the even samples drop no face the plain ones keep.
            ring = corner_ring(polygon.points)
            if len(ring) < len(polygon.points) and found.any():
                even, even_samples = self._front(polygon, ring, spacing)
                if even.any():
                    found, samples = even, even_samples
        return (found, samples) if with_samples else found

    def _front(self, polygon: Polygon, ring: np.ndarray, spacing: float):
        samples = sample_polygon(ring, spacing)
        if len(samples) > 400:
            samples = samples[np.linspace(0, len(samples) - 1, 400).astype(int)]
        normal = polygon.normal
        points = samples + normal * 6.0
        cells = self.grid.index(points)
        i, j, k = cells[:, 0], cells[:, 1], cells[:, 2]
        near = np.stack([self.nearest[axis][i, j, k] for axis in range(3)], axis=1)
        offset = self.grid.centre(near) - points
        length = np.linalg.norm(offset, axis=1)
        facing = (offset @ normal) >= -0.25 * np.maximum(length, 1e-6)
        found = self.labels[near[:, 0], near[:, 1], near[:, 2]]
        distance = self.distance[i, j, k]
        found[(distance > 2.5) | ~facing] = 0
        if self.thin_walls:
            # A wall thinner than a voxel has air one voxel away on both sides, and the nearest-voxel tie can go to the
            # air behind it: the face then looks as if it had no air in front and is dropped. Look straight ahead.
            for reach in (1.0, 1.5):
                ahead = self.grid.index(samples + normal * self.grid.size * reach)
                labels = self.labels[ahead[:, 0], ahead[:, 1], ahead[:, 2]]
                found = np.where(found == 0, labels, found)
        # Samples right at open air decide which rooms a face sees; those under a wall standing on it go either way.
        confident = found.copy()
        confident[distance > 1.5] = 0
        if confident.any():
            found = confident
        return found, samples

    def owner(self, point_lt) -> int:
        """The room label of the labelled air nearest to a point."""
        cell = self.grid.index(np.asarray(point_lt, float)[None])[0]
        near = [self.nearest[axis][cell[0], cell[1], cell[2]] for axis in range(3)]
        return int(self.labels[near[0], near[1], near[2]])


FLOOR_AIR_REACH = (1.0, 1.5, 2.0)    # voxels straight over a floor's samples, nearest first (air_over)
FLOOR_AIR_SHARE = 0.1                # the least share of a floor's samples with air over them for those to vote


def air_over(rooms: NearestRoom, samples: np.ndarray) -> np.ndarray:
    """Per sample of an upward polygon, the room of the first labelled voxel FLOOR_AIR_REACH voxels straight over it
    (0: none). A floor belongs to the air over it, and the air nearest to it (NearestRoom.front) can be a room behind
    a wall whose voxels cover it: shelf boards built into a tavern's wall and a sill running under a row of wall niches
    saw the street through the wall's voxels and went to the street's sector, and the engine puts the props on a floor
    in that floor's sector, so loaves and display figures vanished whenever the street was not drawn (Ravensford,
    2026-11-07). The voxel over a shelf board in a wall's voxels can be solid too, up to the air over the shelf above."""
    labels = np.zeros(len(samples), dtype=rooms.labels.dtype)
    up = np.array([0.0, 1.0, 0.0]) * rooms.grid.size         # LithTech y is up
    for reach in FLOOR_AIR_REACH:
        cells = rooms.grid.index(samples + up * reach)
        labels = np.where(labels == 0, rooms.labels[cells[:, 0], cells[:, 1], cells[:, 2]], labels)
    return labels


def _side_room(rooms: NearestRoom, polygon: Polygon, sign: float) -> int:
    """The room of the labelled air one voxel and a half off a face on one side (0: none)."""
    samples = sample_polygon(polygon.points, rooms.grid.size)
    cells = rooms.grid.index(samples + polygon.normal * sign * rooms.grid.size * 1.5)
    found = Counter(int(v) for v in rooms.labels[cells[:, 0], cells[:, 1], cells[:, 2]] if v)
    return found.most_common(1)[0][0] if found and found.most_common(1)[0][1] >= 0.3 * len(samples) else 0


# MM9's glass, per face (the user's decision, 2026-11-07: windows exactly as MM9 has them). A face is see-through only
# where MM9 draws it translucent: its surface has the Translucent flag (0x8) and its texture a graded alpha. MM9 blends
# it at the texture's alpha (Lichwindow: 43-138 of 255) times its brush's `Alpha` (0.5-1;
# devdocs/mm9_rework/MM9_VISUAL_PROPERTIES.md "Translucent 0x8", "Brush Alpha"), so a face's opacity is the texture
# setting (default 1) times its brush Alpha; white tint (the texture is the colour). A window surface without the flag
# is opaque in MM9, and so in ours: no glass face, no portal, and its texture's alpha is no cut-out (the scene's
# `opaque_faces`: Bootcamp's stained glass, drangheimcityglass, showed its alpha-0 texels as holes to the sky; the
# see-through panes of Sturmford City's locked houses showed their empty interiors).
GLASS_DEFAULTS = {"opacity": 1.0, "tint": [1.0, 1.0, 1.0], "two_sided": False}
# How far behind a pane with air on its front only the converter looks for a face that it would show (LT).
GLASS_BACKING_REACH = 1024.0
GLASS_GRADED_SHARE = 0.2        # texels with alpha in 8-247: alpha meant as translucency, not a cut-out
LT_TRANSLUCENT = 0x8
OPAQUE_WORDS = ("window", "glass", "ice", "fleur", "arch", "cloud")   # Glass.opaque: MM9's glass, ice, cloud textures


def graded_textures(source) -> dict:
    """MM9 source texture (lower case) -> the opacity its translucent faces take, for every texture of the map's visible
    solid surfaces whose DTX alpha is graded (GLASS_GRADED_SHARE of its texels between 8 and 247; bars, fences, chain
    links and ladders are cut-outs and stay ordinary faces): 1, or, when its runtime image has no alpha (the legacy BMP
    only: Clouds1, alpha 30 % in MM9), the DTX's mean alpha."""
    from transcode_mm9_dat_to_odm import decode_dtx_pixels
    from .source import HELPER_TEXTURES, LT_INVISIBLE, LT_SOLID, ROOT
    textures = set()
    for model in source.world.world_models:
        if model.name.startswith(("AITrk", "VisBSP", "PerceptionBrush", "Ladder")):
            continue
        for poly in model.polies:
            surface = model.surfaces[poly.surface_index]
            texture = model.textures[surface.texture_index]
            stem = Path(texture.replace("\\", "/")).stem.lower()
            if surface.flags & LT_INVISIBLE or not surface.flags & LT_SOLID or stem in HELPER_TEXTURES \
                    or texture.lower().endswith(".spr") or stem == "skymarker":
                continue
            textures.add(texture.lower())
    graded = {}
    for texture in sorted(textures):
        alias = source.aliases.get(texture)
        if alias is None:
            continue
        path = ROOT / alias["physical_path"] if alias.get("physical_path") else \
            ROOT / "mm9/extracted/TEXTURES" / texture.replace("\\", "/").upper().replace(".DTX", ".dtx")
        if not path.exists():
            continue
        try:
            width, height, pixels, _ = decode_dtx_pixels(path, alias["alias"])
        except Exception:                   # a format the decoder does not read: no alpha to honour
            continue
        alpha = np.frombuffer(bytes(pixels), np.uint8).reshape(height, width, 4)[..., 3]
        if ((alpha > 8) & (alpha < 247)).mean() < GLASS_GRADED_SHARE:
            continue
        images = ROOT / "assets_dev/worlds/mm9"
        x2 = images / "textures_x2" / f"{alias['alias'].lower()}.png"
        has_alpha = (images / "textures_x4" / f"{alias['alias'].lower()}.oytex").exists() or \
            (x2.exists() and Image.open(x2).mode in ("RGBA", "LA", "PA")) or native_has_alpha(alias["alias"])
        graded[texture] = 1.0 if has_alpha else round(float(alpha.mean()) / 255.0, 2)
    return graded


def native_has_alpha(alias: str) -> bool:
    """Whether the decoded native (worlds/mm9/textures/<alias>.bmp) carries alpha: a 32-bit BMP whose fourth byte is
    not all zero, as SDL loads it (PIL reads it as RGB; Clouds1's native holds its 30 % alpha so)."""
    from .source import ROOT
    for folder in ("assets_source/worlds/mm9/textures", "assets_dev/worlds/mm9/textures"):
        path = ROOT / folder / f"{alias}.bmp"
        if not path.exists():
            continue
        data = path.read_bytes()
        if int.from_bytes(data[28:30], "little") != 32:
            return False
        start, width, height = (int.from_bytes(data[10:14], "little"), int.from_bytes(data[18:22], "little"),
                                abs(int.from_bytes(data[22:26], "little", signed=True)))
        pixels = np.frombuffer(data[start:start + width * height * 4], np.uint8)
        return bool(pixels[3::4].any())
    return False


class Glass:
    """MM9's glass per face (module note above): `texture(polygon)` gives the settings of a translucent face (Translucent
    flag, graded alpha), `opaque(polygon)` tells a face drawn opaque whatever its texture's alpha (graded alpha, no
    flag). overrides.yml `glass` ({texture: {opacity, tint, two_sided}}, or a list) only tunes the translucent faces of
    those textures; it makes no face glass. Each distinct (texture, settings, brush Alpha) is a kind: one
    `translucent_faces` entry, STATIC_glass<kind>_<room> nodes, mover parts `<node>_GLASS<kind>`."""
    def __init__(self, overrides: dict, source):
        tuned = overrides.get("glass") or {}
        if isinstance(tuned, list):
            tuned = {name: {} for name in tuned}
        tuned = {name.lower(): settings or {} for name, settings in tuned.items()}
        self.graded = graded_textures(source)
        self.tuned = {name: {key: value for key, value in settings.items() if key != "boxes"}
                      for name, settings in tuned.items()}
        self.textures = {}
        for texture, opacity in self.graded.items():
            merged = dict(GLASS_DEFAULTS, **self.tuned.get(texture.replace("\\", "/").split("/")[-1], {}))
            self.textures[texture] = dict(merged, opacity=round(merged["opacity"] * opacity, 3))
        self.source = source
        self.kinds = []
        self._kind_of = {}

    def brush_alpha(self, polygon: Polygon) -> float:
        found = self.source.by_name.get(polygon.model.lower())
        return float(found["properties"].get("Alpha", 1.0)) if found else 1.0

    def texture(self, polygon: Polygon) -> dict | None:
        """The settings of a translucent face, else None: MM9's Translucent flag on a graded-alpha texture, on a brush
        whose Alpha is below 1 (the Wizard's Lab super eye's force field, Perception.spr at 0.35), or on a texture
        the map's `glass` names (an animated .spr the DTX check cannot read). The brush Alpha only matters with the
        flag: MM9 blends only Translucent surfaces (devdocs/mm9_rework/MM9_VISUAL_PROPERTIES.md "Brush Alpha")."""
        if not polygon.flags & LT_TRANSLUCENT:
            return None
        texture = polygon.texture.lower()
        if texture in self.textures:
            return self.textures[texture]
        name = texture.replace("\\", "/").split("/")[-1]
        # animated .spr surfaces (water, slime) are liquids (liquids.py) unless the map names them
        if name in self.tuned or (self.brush_alpha(polygon) < 1.0 and not name.endswith(".spr")):
            self.textures[texture] = dict(GLASS_DEFAULTS, **self.tuned.get(name, {}))
            return self.textures[texture]
        return None

    def opaque(self, polygon: Polygon) -> bool:
        """A window, ice or cloud face MM9 draws opaque (no Translucent flag) whose texture has a graded alpha: drawn
        opaque, its alpha no cut-out (MM9 window glass showed its alpha-0 texels as holes to the sky). Other unflagged
        textures with alpha keep their cut-out: bars, grilles, blood splashes, worn trims, awnings, crowd cards."""
        texture = polygon.texture.lower()
        name = texture.replace("\\", "/").split("/")[-1]
        return not polygon.flags & LT_TRANSLUCENT and texture in self.graded \
            and any(word in name for word in OPAQUE_WORDS)

    def kind(self, polygon: Polygon) -> int | None:
        """The polygon's glass kind (index into kinds), or None."""
        settings = self.texture(polygon)
        if settings is None:
            return None
        alpha = self.brush_alpha(polygon)
        key = (polygon.texture.lower(), round(alpha, 3))
        if key not in self._kind_of:
            self._kind_of[key] = len(self.kinds)
            self.kinds.append(dict(settings, opacity=round(settings["opacity"] * alpha, 3)))
        return self._kind_of[key]


def glass_portals(rooms: NearestRoom, polygons: list[Polygon], glass: Glass, stats: Counter) -> list[dict]:
    """Glass (overrides.yml `glass`: the MM9 textures MM9 draws translucent). A glass face with one room's air on one
    side and another room's on the other becomes a portal between them, shaped as the face, and stays as a solid glass
    face (role `glass`: drawn translucent, colliding and blocking sight and missiles as MM9's solid glass does); with
    the same room on both sides it is only the glass face; with air on its front only it is a candidate
    (`notes["glass_backed"]`) that glass_backed() makes glass when a face stands behind it to be seen through, and
    otherwise stays an opaque textured face (the void behind would draw black). A glass face belongs to the room on
    its front (`notes["glass_room"]`): MM9's panes are often single quads whose front air the face sampling of
    assign_faces misses."""
    portals = []
    for polygon in polygons:
        if polygon.role != "static" or glass.texture(polygon) is None:
            continue
        front, back = (_side_room(rooms, polygon, sign) for sign in (1.0, -1.0))
        if not front or not back:
            polygon.notes["glass_backed"] = True
            continue
        polygon.role = "glass"
        polygon.notes["glass_room"] = front
        if front == back:
            stats["glass_clear"] += 1
            continue
        normal = polygon.normal
        axis_b = np.array([0.0, 1.0, 0.0]) if abs(normal[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
        axis_b = axis_b - normal * (axis_b @ normal)
        axis_b /= np.linalg.norm(axis_b)
        axis_a = np.cross(axis_b, normal)
        a, b = polygon.points @ axis_a, polygon.points @ axis_b
        centre = polygon.points.mean(0)
        centre = centre + axis_a * ((a.max() + a.min()) / 2 - centre @ axis_a) \
            + axis_b * ((b.max() + b.min()) / 2 - centre @ axis_b)
        portals.append({"name": f"glass_{polygon.model}_{len(portals) + 1}", "kind": "glass", "centre": centre,
                        "normal": normal, "axis_a": axis_a, "half_a": float(np.ptp(a)) / 2, "axis_b": axis_b,
                        "half_b": float(np.ptp(b)) / 2, "ring": polygon.points.copy(), "rooms": (front, back)})
        stats["glass_portals"] += 1
    return portals


def glass_backed(polygons: list[Polygon], stats: Counter) -> None:
    """The glass candidates with air on their front only (glass_portals): glass where the ray from the pane's centre
    out of its back meets, within GLASS_BACKING_REACH, the front of a built face (a wall right behind the pane, the far
    side of a sealed case), so the pane shows it; opaque where it meets nothing or a face's back (the void outside the
    map, a sealed pod whose inside is not built)."""
    candidates = [p for p in polygons if p.notes.get("glass_backed") and p.role == "static"]
    if not candidates:
        return
    # The ray looks through glass and the invisible collision shells round it (Bootcamp's museum cases: panes behind
    # panes in Invisible.dtx boxes, 2026-11-07), and the sky shell counts at any distance (a window to the outdoors).
    targets = [p for p in polygons if not p.notes.get("glass_backed") and p.role not in ("glass", "invisible", "barrier")]
    sky = np.array([p.texture.lower().endswith("skymarker.dtx") for p in targets])
    normals = np.array([p.normal for p in targets])
    offsets = np.array([float(p.normal @ p.points[0]) for p in targets])
    for pane in candidates:
        origin, direction = pane.points.mean(0) - pane.normal * 0.5, -pane.normal
        along = normals @ direction
        with np.errstate(divide="ignore", invalid="ignore"):
            t = (offsets - normals @ origin) / along
        order = np.argsort(np.where((along < -1e-6) | (along > 1e-6), t, np.inf))
        best = None
        for index in order:
            if not 0.0 < t[index] <= (np.inf if sky[index] else GLASS_BACKING_REACH):
                if not np.isfinite(t[index]):
                    break
                continue
            hit, target = origin + direction * t[index], targets[index]
            ring = target.points
            edges = np.cross(np.roll(ring, -1, axis=0) - ring, hit - ring) @ target.normal
            if (edges >= -1e-3).all() or (edges <= 1e-3).all():
                best = target
                break
        if best is not None and float(best.normal @ direction) < 0:
            pane.role = "glass"
            pane.notes["glass_room"] = pane.label
            stats["glass_backed"] += 1
        else:
            stats["glass_opaque"] += 1


SPLIT_AXES = [np.array(a, float) / np.linalg.norm(a) for a in ((1, 0, 0), (0, 0, 1), (1, 0, 1), (1, 0, -1), (0, 1, 0))]


def separating_plane(samples: np.ndarray, found: np.ndarray, counts: Counter, corners: np.ndarray,
                     every_candidate: bool = False):
    """A plane (normal, distance) that puts one room's samples on one side and the other rooms' on the other, for at
    least 88 % of the samples (samples under a wall that stands on the face go either way), at the middle of the gap
    between them (the widest gap over rooms and axes); None if no axis separates any room from the rest.
    every_candidate (map setting `split_retry`): when the widest gap's split fails the purity test below, try the
    next widest: a floor under a row of three cells otherwise stays whole (Drangheim Prison)."""
    valid = found > 0
    points = samples[valid]
    candidates = []
    for main in counts:
        inside = found[valid] == main
        total_main, total = int(inside.sum()), len(inside)
        for axis in SPLIT_AXES:
            values = points @ axis
            order = np.argsort(values, kind="stable")
            sorted_inside = inside[order]
            main_below = np.concatenate([[0], np.cumsum(sorted_inside)])
            others_below = np.arange(total + 1) - main_below
            correct_low = main_below + (total - total_main - others_below)        # the room below the split
            correct_high = others_below + (total_main - main_below)               # the room above it
            for correct in (correct_low, correct_high):
                k = int(np.argmax(correct))
                if 0 < k < total and correct[k] >= 0.88 * total:
                    gap = values[order[k]] - values[order[k - 1]]
                    split = (values[order[k]] + values[order[k - 1]]) / 2
                    extent = corners @ axis
                    if min(split - extent.min(), extent.max() - split) < 12.0:      # no slivers
                        continue
                    candidates.append((gap, len(candidates), axis, split, main))
    candidates.sort(key=lambda c: (-c[0], c[1]))
    for _, _, axis, split, main in candidates if every_candidate else candidates[:1]:
        # Only a split that leaves the separated room's part seeing (nearly) only that room; noise along a doorway
        # edge is no reason. The other part may see several rooms and is split again.
        side = points @ axis > split
        fractions = [(found[valid][part] == main).mean() for part in (side, ~side) if part.any()]
        if not any(0.5 <= fraction < 0.9 for fraction in fractions):
            return axis, float(split)
    return None


_PORTAL_BOXES = {}       # (id(portals), voxel) -> (portals, their objects, box entries, box lows, box highs)


def _portal_boxes(portals: list[dict], voxel: float):
    """crossing_portals' boxes of a portal list, computed once while the list holds the same portal objects (the
    rectangles were rebuilt for every polygon: over half of a dungeon's or city's build)."""
    key = (id(portals), voxel)
    cached = _PORTAL_BOXES.get(key)
    if cached is not None and cached[0] is portals and len(cached[1]) == len(portals) \
            and all(a is b for a, b in zip(cached[1], portals)):
        return cached[2:]
    entries = []
    for portal in portals:
        boxes = portal.get("split_boxes")
        if boxes is None:
            boxes = [(None, rectangle_points(portal["centre"], portal["axis_a"], portal["half_a"] + voxel,
                                             portal["axis_b"], portal["half_b"] + voxel, 1e9))]
        entries += [(portal, name, corners) for name, corners in boxes]
    lows = np.array([corners.min(0) for _, _, corners in entries]).reshape(-1, 3)
    highs = np.array([corners.max(0) for _, _, corners in entries]).reshape(-1, 3)
    _PORTAL_BOXES.clear()
    _PORTAL_BOXES[key] = (portals, tuple(portals), entries, lows, highs)
    return entries, lows, highs


def crossing_portals(polygon: Polygon, portals: list[dict], voxel: float) -> list[dict]:
    """The portals whose rectangle (one voxel wider) the polygon's box reaches and whose plane it straddles. A portal
    with `split_boxes` ([(name, corners)]: a city's merged top portals, ../city/structure.py) is tested by those
    boxes instead of its rectangle (the plain cover's rectangles, so the faces are split as before), as a candidate
    of the box's name per box reached."""
    low, high = polygon.points.min(0) - 2 * voxel, polygon.points.max(0) + 2 * voxel
    entries, lows, highs = _portal_boxes(portals, voxel)
    reached = ~((highs < low).any(1) | (lows > high).any(1))
    candidates = []
    for k in np.flatnonzero(reached):
        portal, name, _ = entries[k]
        side = polygon.points @ portal["normal"] - portal["normal"] @ portal["centre"]
        if side.min() < -0.5 and side.max() > 0.5:
            candidates.append(portal if name is None else dict(portal, name=name))
    return candidates


def assign_faces(rooms: NearestRoom, polygons: list[Polygon], portals: list[dict], stats: Counter,
                 log: dict, minor_split: bool = False, split_retry: bool = False,
                 thin_walls: bool = False, restore_holes: bool = True,
                 dropped: list | None = None, corner_samples: bool = False) -> list[Polygon]:
    """Each polygon goes to the room in front of it; one that sees two rooms is split by the portal planes between
    them until each part sees one. log['dropped'] and log['mixed'] collect the faces dropped and left mixed.
    minor_split (map setting `split_minor_rooms`): a polygon that crosses a portal plane (near the portal) is always
    split there, not only when its second room has 15 % of the samples: a long floor strip running from a hall under a
    wall into a vault otherwise stays whole in the hall, its samples in the vault being few or under the wall, and
    the engine then puts a party standing in the vault into the hall's sector (whose floor is under it).
    restore_holes (map setting `restore_floor_holes`, default on): a dropped up-facing polygon beside a kept coplanar
    polygon of its model, with labelled air above, takes that polygon's room (floors.restore_floor_holes; the
    Thousand Terrors' tread tops). `dropped` collects the polygons left dropped (for the floor-hole check).
    corner_samples (map setting `corner_samples`): the votes sample each polygon over its corners only
    (NearestRoom.front)."""
    voxel = rooms.grid.size
    lost = [] if dropped is None else dropped
    entries = {}                    # id(dropped polygon) -> its log['dropped'] entry
    rooms.thin_walls = thin_walls
    rooms.corner_samples = corner_samples
    result = []
    queue = [(p, 0) for p in polygons]
    while queue:
        polygon, depth = queue.pop()
        if polygon.role == "glass":
            polygon.label = polygon.notes["glass_room"]
            result.append(polygon)
            continue
        found, samples = rooms.front(polygon, with_samples=True)
        counts = Counter(int(v) for v in found if v)
        if counts and polygon.normal[1] >= 0.7:
            # a floor's samples vote with the air straight over them (air_over), where enough of them have it
            over = air_over(rooms, samples)
            if (over > 0).sum() >= max(2, FLOOR_AIR_SHARE * len(over)):
                votes = Counter(int(v) for v in over if v)
                if votes.most_common(1)[0][0] != counts.most_common(1)[0][0]:
                    stats["floors_to_room_over"] += 1
                found, counts = over, votes
        if not counts:
            stats["faces_without_air_dropped"] += 1
            log["dropped"].append({"model": polygon.model, "texture": polygon.texture.split("\\")[-1],
                                   "centre_lt": polygon.points.mean(0).round(1).tolist(),
                                   "normal_lt": polygon.normal.round(2).tolist(), "area_lt": round(polygon.area)})
            lost.append(polygon)
            entries[id(polygon)] = log["dropped"][-1]
            continue
        second = counts.most_common(2)[1][1] if len(counts) > 1 else 0
        threshold = max(3, 0.15 * sum(counts.values()))
        crossing = minor_split and depth < 10 and crossing_portals(polygon, portals, voxel)
        if crossing and (len(counts) == 1 or second < threshold):
            stats["face_splits_minor_room"] += 1
        elif len(counts) == 1 or depth >= 10 or second < threshold:
            # A floor reaching a little way into a room no portal across it joins (a smithy's floor running on under
            # the wall into the street: the anvil on its smithy end went to the street's sector) is split where its
            # rooms' samples separate, however few the second room's are: the engine finds a prop's sector by the
            # floor under it.
            plane = separating_plane(samples, found, counts, polygon.points, split_retry) \
                if len(counts) > 1 and depth < 10 and second >= 3 and polygon.normal[1] >= 0.7 \
                and not crossing_portals(polygon, portals, voxel) else None
            if plane is not None:
                front, back = clip(polygon, plane[0], plane[1], f"floor{depth}")
                stats["floor_splits_minor_room"] += 1
                queue.extend((part, depth + 1) for part in (front, back) if part is not None)
                continue
            polygon.label = counts.most_common(1)[0][0]
            polygon.notes["votes"] = dict(counts)
            if len(counts) > 1 and depth >= 10:
                stats["faces_mixed_after_splitting"] += 1
            result.append(polygon)
            continue
        candidates = crossing_portals(polygon, portals, voxel)
        if not candidates:
            # A face over several rooms without a portal between them (a ceiling or floor brush running over the
            # walls between rooms): split it where the rooms' samples separate along a horizontal axis.
            plane = separating_plane(samples, found, counts, polygon.points, split_retry)
            if plane is None:
                polygon.label = counts.most_common(1)[0][0]
                polygon.notes["votes"] = dict(counts)
                stats["faces_mixed_without_portal"] += 1
                if counts.most_common(1)[0][1] < 0.8 * sum(counts.values()):
                    stats["faces_mixed_without_portal_minority_over_20pct"] += 1
                    log["mixed"].append({"texture": polygon.texture.split("\\")[-1],
                                         "centre_lt": polygon.points.mean(0).round().tolist(),
                                         "normal_lt": polygon.normal.round(2).tolist(),
                                         "area_lt": round(polygon.area), "rooms": dict(counts)})
                result.append(polygon)
                continue
            front, back = clip(polygon, plane[0], plane[1], f"wall{depth}")
            stats["face_splits_at_walls"] += 1
            for part in (front, back):
                if part is not None:
                    queue.append((part, depth + 1))
            continue
        portal = candidates[0]
        front, back = clip(polygon, portal["normal"], float(portal["normal"] @ portal["centre"]), portal["name"])
        stats["face_splits"] += 1
        for part in (front, back):
            if part is not None:
                queue.append((part, depth + 1))
    if restore_holes:
        from .floors import restore_floor_holes
        restored = restore_floor_holes(rooms, result, lost, stats, log)
        if restored:
            stats["faces_without_air_dropped"] -= len(restored)
            gone = {id(entries[id(p)]) for p in restored}
            log["dropped"] = [entry for entry in log["dropped"] if id(entry) not in gone]
            result.extend(restored)
    return result


def _clip_ring(points: np.ndarray, normal: np.ndarray, offset: float) -> tuple[np.ndarray | None, np.ndarray | None]:
    """A convex ring split by the plane normal . p = offset: (front part, back part), None for an empty part."""
    side = points @ normal - offset
    front, back = [], []
    for index in range(len(points)):
        j = (index + 1) % len(points)
        if side[index] >= 0:
            front.append(points[index])
        if side[index] <= 0:
            back.append(points[index])
        if (side[index] > 0 > side[j]) or (side[index] < 0 < side[j]):
            point = points[index] + (points[j] - points[index]) * (side[index] / (side[index] - side[j]))
            front.append(point)
            back.append(point)
    return (np.array(front) if len(front) >= 3 else None), (np.array(back) if len(back) >= 3 else None)


def split_straddling_portals(grid: VoxelGrid, labels: np.ndarray, portals: list[dict], stats: Counter) -> list[dict]:
    """A portal whose one side opens onto two rooms (a house window or door on a street where a street cut ends at
    the wall in front of it: Thjorgard City, 2026-11-01) is split at the plane of the portal between those rooms, one
    piece per room. Whole, it led to the room most of it faces only, and the other room, seen through the rest of it,
    was rejected as behind the camera: sky showed there. Rectangle portals split others; merged top portals neither."""
    splitters = [p for p in portals if "ring" not in p and "side_points" not in p and len(set(p.get("rooms", ()))) == 2]
    result = []
    for portal in portals:
        if "side_points" in portal or len(set(portal.get("rooms", ()))) < 2:
            result.append(portal)
            continue
        points = rectangle_points(portal["centre"], portal["axis_a"], portal["half_a"] * 0.9, portal["axis_b"],
                                  portal["half_b"] * 0.9, grid.size / 2)
        found = set()
        for sign in (1, -1):
            cells = grid.index(points + portal["normal"] * sign * grid.size * 1.5)
            counts = Counter(int(v) for v in labels[cells[:, 0], cells[:, 1], cells[:, 2]] if v)
            if len(counts) > 1 and counts.most_common(2)[1][1] >= max(3, 0.15 * len(points)):
                found |= {room for room, count in counts.items() if count >= 3}
        if not found:
            result.append(portal)
            continue
        rectangle = np.array([
            portal["centre"] + sa * portal["axis_a"] * portal["half_a"] + sb * portal["axis_b"] * portal["half_b"]
            for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
        ring = portal["ring"] if "ring" in portal else rectangle
        split = None
        for other in splitters:
            if other is portal or not set(other["rooms"]) <= found:
                continue
            offset = float(other["normal"] @ other["centre"])
            side = ring @ other["normal"] - offset
            if side.max() <= 1.0 or side.min() >= -1.0:
                continue
            # the splitter must reach the portal: the portal's centre within its rectangle (+ 2 voxels) in its plane
            relative = portal["centre"] - other["centre"]
            if (abs(relative @ other["axis_a"]) > other["half_a"] + 2 * grid.size
                    or abs(relative @ other["axis_b"]) > other["half_b"] + 2 * grid.size):
                continue
            split = (other["normal"], offset)
            break
        if split is None:
            result.append(portal)
            continue
        stats["portals_split_at_crossing_portals"] += 1
        # each piece's face is the grown face's piece (face_halves); its rectangle stays the barrier's piece
        face_ring = portal["ring"] if "ring" in portal else portal_corners(portal)
        for index, (piece, face_piece) in enumerate(zip(_clip_ring(ring, *split), _clip_ring(face_ring, *split))):
            if piece is None or face_piece is None:
                continue
            axis_a, axis_b, base = portal["axis_a"], portal["axis_b"], portal["centre"]
            a, b = piece @ axis_a, piece @ axis_b
            centre = (base + axis_a * ((a.max() + a.min()) / 2 - base @ axis_a)
                      + axis_b * ((b.max() + b.min()) / 2 - base @ axis_b))
            made = dict(portal, name=f"{portal['name']}_part{index + 1}", centre=centre, half_a=float(np.ptp(a)) / 2,
                        half_b=float(np.ptp(b)) / 2, ring=face_piece)
            made["rooms"] = portal_sides(grid, labels, made)
            result.append(made)
    return result


def portal_side_faces(polygons: list[Polygon], portals: list[dict], voxel: float, stats: Counter) -> None:
    """Faces in a portal's opening take the room on their side of its plane. A doorway one wall thick is one barrier
    voxel, so the pieces of its threshold floor, reveals and lintel cut at the portal plane (assign_faces) take the
    room of whichever air voxel is nearest, often the room on the other side; the engine then puts a party standing
    past the portal in that room and draws the wrong one (Thjorgard City's upper rooms, 2026-11-01). A face wholly on
    one side within 1.5 voxels of the plane and inside the rectangle (+ 2 LT) that holds one of the portal's two rooms
    takes the room on its side. Rectangle portals only (doors, windows, cuts; not a city's merged top portals)."""
    reach = 1.5 * voxel
    for portal in portals:
        front, back = (portal.get("rooms") or (0, 0))[:2]
        if "ring" in portal or "side_points" in portal or not front or not back or front == back:
            continue
        normal, centre = portal["normal"], portal["centre"]
        axis_a, axis_b = portal["axis_a"], portal["axis_b"]
        half_a, half_b = (half + 2.0 for half in face_halves(portal))
        low, high = centre - reach - half_a - half_b, centre + reach + half_a + half_b
        for polygon in polygons:
            if polygon.label not in (front, back) or polygon.role == "glass":
                continue
            points = polygon.points
            if (points.min(0) > high).any() or (points.max(0) < low).any():
                continue
            relative = points - centre
            distance = relative @ normal
            if np.abs(relative @ axis_a).max() > half_a or np.abs(relative @ axis_b).max() > half_b:
                continue
            if distance.max() > reach or distance.min() < -reach:
                continue
            if distance.min() >= -0.5 and distance.max() > 0.5:
                side = front
            elif distance.max() <= 0.5 and distance.min() < -0.5:
                side = back
            else:
                continue                    # in the plane or across it
            if polygon.label != side:
                polygon.label = side
                stats["faces_moved_to_their_portal_side"] += 1


DOORWAY_FLOOR_DEPTH_VOXELS = 6      # how far either side of a doorway portal floor pieces take the room of their side


def doorway_floors(polygons: list[Polygon], portals: list[dict], rooms: NearestRoom, stats: Counter) -> list[Polygon]:
    """Floor pieces in a doorway take the room on their side of its portal. The engine finds a party's sector by the
    floor under it, so a floor of one room reaching past a portal into the other room's side puts a party standing
    there in the wrong room, and the view from there runs out of drawn rooms: black (Anskram Keep's doorway floors,
    reaching 134 units past the portal moved onto the leaves' face; Drangheim City's house sills, a strip along the
    whole front wall that never crosses the plane, so neither the crossing split nor portal_side_faces' rectangle test
    caught it; user reports 2026-11-06). Each floor at the foot of a vertical rectangle portal is cut at the opening's
    sides, at DOORWAY_FLOOR_DEPTH_VOXELS each way and at the portal plane; the pieces inside take the room of their
    side; the parts outside keep theirs, except a part cut off beyond the depth on the far side of a floor that reached
    past the portal, which takes the room of the air over it (Drangheim City: a room's floor running 550 units on into
    the next room). Rectangle portals only, not a city's merged top portals."""
    voxel = rooms.grid.size
    up = np.array([0.0, 1.0, 0.0])
    depth = DOORWAY_FLOOR_DEPTH_VOXELS * voxel
    for portal in portals:
        front, back = (portal.get("rooms") or (0, 0))[:2]
        if "ring" in portal or "side_points" in portal or not front or not back or front == back:
            continue
        normal = np.asarray(portal["normal"], float)
        if abs(normal[1]) > 0.3:
            continue
        across = np.cross(up, normal)
        across /= np.linalg.norm(across)
        centre = np.asarray(portal["centre"], float)
        corners = portal_corners(portal)            # the face (face_halves): its jamb strips are the doorway's
        widths = corners @ across
        bottom = float(corners[:, 1].min())
        plane = float(normal @ centre)
        cuts = [(across, float(widths.max())), (-across, -float(widths.min())), (normal, plane + depth),
                (-normal, -(plane - depth))]
        result = []
        for polygon in polygons:
            points = polygon.points
            if (polygon.label not in (front, back) or polygon.role == "glass" or polygon.normal[1] < 0.7
                    or points[:, 1].max() < bottom - voxel or points[:, 1].min() > bottom + voxel
                    or (points @ across).max() <= widths.min() or (points @ across).min() >= widths.max()
                    or (points @ normal).max() <= plane - depth or (points @ normal).min() >= plane + depth):
                result.append(polygon)
                continue
            inside, outsides = polygon, []
            for index, (cut_normal, cut_offset) in enumerate(cuts):   # the parts outside the doorway box
                if inside is None:
                    break
                outside, inside = clip(inside, cut_normal, cut_offset, "doorway")
                if outside is not None:
                    outside.label = polygon.label
                    outsides.append((outside, index >= 2))
            parts = [] if inside is None else [
                (part, room) for part, room in zip(clip(inside, normal, plane, "doorway_plane"), (front, back))
                if part is not None]
            if not any(room != polygon.label for _, room in parts):
                result.append(polygon)                      # wholly on its own room's side: kept whole
                continue
            for outside, beyond_depth in outsides:
                if beyond_depth:                            # past the box along the normal: the air over it decides
                    owner = rooms.owner(outside.points.mean(0) + up * 1.5 * voxel)
                    if owner in (front, back) and owner != outside.label:
                        outside.label = owner
                        stats["doorway_floor_far_parts_moved_to_their_air"] += 1
                result.append(outside)
            for part, room in parts:
                part.label = room
                stats["doorway_floor_pieces_moved_to_their_side"] += room != polygon.label
                result.append(part)
        polygons = result
    return polygons


def archway_portals(grid: VoxelGrid, air: np.ndarray, extra: dict) -> list[dict]:
    """An archway cut: the air of the voxel slice perpendicular to `axis` (x or z) through `point` (or each of
    `points`, for a cut across several openings in one plane), as far as it connects to the point within that slice
    and within `span` of it along the cut, is the barrier; each opening's bounding rectangle is a portal (one per
    opening, since each joins its own pair of rooms)."""
    axis = {"x": 0, "z": 2}[extra["axis"]]
    others = [a for a in range(3) if a != axis]
    horizontal = others[1] if others[1] != 1 else others[0]
    h, v = others.index(horizontal), others.index(1)
    seeds = [np.array(p, float) for p in extra.get("points", [extra.get("point")])]
    plane_cell = grid.index(seeds[0][None])[0][axis]
    slice_air = np.take(air, plane_cell, axis=axis)                     # 2D over the two other axes in order
    span_cells = int(np.ceil(extra.get("span", 256) / grid.size))
    openings = []
    for point in seeds:
        cell = grid.index(point[None])[0]
        seed = (cell[others[0]], cell[others[1]])
        if not slice_air[seed]:
            near = np.argwhere(slice_air)
            seed = tuple(near[np.argmin(np.abs(near - np.array(seed)).sum(1))])
        window = np.zeros_like(slice_air)
        index = [slice(None), slice(None)]
        index[h] = slice(max(seed[h] - span_cells, 0), seed[h] + span_cells + 1)
        window[tuple(index)] = True
        windowed, _ = ndimage.label(slice_air & window)
        component = windowed == windowed[seed]
        if not any((component & other).any() for other in openings):
            openings.append(component)
    plane = grid.origin[axis] + (plane_cell + 0.5) * grid.size
    portals = []
    for number, component in enumerate(openings):
        cells2 = np.argwhere(component)
        cells = np.zeros((len(cells2), 3), np.int64)
        cells[:, axis] = plane_cell
        cells[:, others[0]], cells[:, others[1]] = cells2[:, 0], cells2[:, 1]
        low = grid.origin[others] + cells2.min(0) * grid.size
        high = grid.origin[others] + (cells2.max(0) + 1) * grid.size
        centre = np.zeros(3)
        centre[axis] = plane
        centre[others] = (low + high) / 2
        normal = np.zeros(3); normal[axis] = 1.0
        axis_a = np.zeros(3); axis_a[horizontal] = 1.0
        name = extra["name"] if len(openings) == 1 else f"{extra['name']}_{number + 1}"
        portals.append({"name": name, "kind": "archway", "centre": centre, "normal": normal, "axis_a": axis_a,
                        "half_a": (high[h] - low[h]) / 2, "axis_b": np.array([0.0, 1.0, 0.0]),
                        "half_b": (high[v] - low[v]) / 2, "cells": cells})
    return portals


# --- Plans ------------------------------------------------------------------------------------------------------------

def room_colour(label: int) -> tuple:
    r, g, b = colorsys.hsv_to_rgb((label * 0.618034) % 1.0, 0.55 + 0.35 * (label % 3) / 2, 0.95)
    return int(r * 255), int(g * 255), int(b * 255)


def draw_plan(path: Path, polygons: list[Polygon], portals: list[dict], title: str, scale=0.2,
              level: tuple | None = None):
    """Top view in LithTech x/z: floors coloured by room (lit by height), walls, portals (white) and room numbers,
    with a 256-unit grid. `level` (low, high LithTech y) limits the floors and walls to one storey."""
    if level is not None:
        polygons = [p for p in polygons if level[0] <= p.points[:, 1].mean() <= level[1]]
        portals = [p for p in portals if level[0] <= p["centre"][1] <= level[1]]
    points = np.concatenate([p.points for p in polygons])
    x0, z1 = points[:, 0].min() - 60, points[:, 2].max() + 60
    width = int((points[:, 0].max() + 60 - x0) * scale)
    height = int((z1 - points[:, 2].min() + 60) * scale)
    image = Image.new("RGB", (width, height), (18, 18, 26))
    draw = ImageDraw.Draw(image)
    to = lambda x, z: ((x - x0) * scale, (z1 - z) * scale)      # noqa: E731
    floors = [p for p in polygons if p.normal[1] > 0.7]
    y_low, y_high = points[:, 1].min(), points[:, 1].max()
    for polygon in sorted(floors, key=lambda p: p.points[:, 1].mean()):
        colour = room_colour(polygon.label) if polygon.label > 0 else (90, 90, 90)
        shade = 0.55 + 0.45 * np.clip((polygon.points[:, 1].mean() - y_low) / max(y_high - y_low, 1), 0, 1)
        draw.polygon([to(p[0], p[2]) for p in polygon.points], fill=tuple(int(c * shade) for c in colour))
    for polygon in polygons:
        if abs(polygon.normal[1]) < 0.3:
            xy = [to(p[0], p[2]) for p in polygon.points]
            draw.line(xy + [xy[0]], fill=(10, 10, 10), width=1)
    for portal in portals:
        if portal.get("kind") == "roof_line" and "ring" in portal:
            # a city's merged top portal (../city/structure.py): its outline
            xy = [to(p[0], p[2]) for p in portal["ring"]]
            draw.line(xy + [xy[0]], fill=(255, 255, 255), width=2)
            continue
        a = portal["centre"] - portal["axis_a"] * portal["half_a"]
        b = portal["centre"] + portal["axis_a"] * portal["half_a"]
        draw.line([to(a[0], a[2]), to(b[0], b[2])], fill=(255, 255, 255), width=3)
    labels = defaultdict(list)
    for polygon in floors:
        if polygon.label > 0:
            labels[polygon.label].append(polygon.points.mean(0))
    for label, centres in labels.items():
        centre = np.mean(centres, axis=0)
        draw.text(to(centre[0], centre[2]), str(label), fill=(255, 255, 255))
    for gx in range(int(np.floor(x0 / 256)) * 256, int(points[:, 0].max()) + 257, 256):
        draw.line([to(gx, z1), to(gx, z1 - height / scale)], fill=(70, 70, 90) if gx % 1024 else (140, 140, 170))
        draw.text(to(gx + 4, z1 - 20), str(gx), fill=(150, 150, 180))
    for gz in range(int(np.floor(points[:, 2].min() / 256)) * 256, int(z1) + 1, 256):
        draw.line([to(x0, gz), to(x0 + width / scale, gz)], fill=(70, 70, 90) if gz % 1024 else (140, 140, 170))
        draw.text(to(x0 + 4, gz + 30), str(gz), fill=(150, 150, 180))
    draw.text((6, 6), title, fill=(255, 255, 255))
    image.save(path)


def portal_face_ring(portal: dict) -> np.ndarray:
    """The polygon a portal's face is written as (build.faces): its ring, else its rectangle (face_halves)."""
    return np.asarray(portal["ring"], float) if "ring" in portal else portal_corners(portal)


def uncovered_barriers(grid: VoxelGrid, air: np.ndarray, labels: np.ndarray, barrier_portals: list[dict],
                       portals: list[dict]) -> list[dict]:
    """Barrier voxels between two rooms that no portal face covers: holes in the portal graph. Two rooms meet only
    across barrier voxels (label_rooms), and the engine sees from one into the other only through a portal face, so
    where a barrier separates two rooms with no face over it, neither is drawn from the other: the view runs out of
    drawn rooms there (MM9 portal sweep 2026-11-08: a doorway's jamb strip, a city platform under the roof line).
    A barrier voxel separates two rooms when the first non-barrier air voxels either way along an axis (within three,
    through barrier air only) are of two rooms; it is covered when a portal face lies within 0.75 voxel of its centre and holds its projection
    (half a voxel of slack). Returns the uncovered ones as clusters, largest first."""
    size = grid.size
    barrier = np.zeros(grid.shape, bool)
    for portal in barrier_portals:
        cells = portal["cells"] if "cells" in portal else portal_barrier(grid, portal)
        barrier[cells[:, 0], cells[:, 1], cells[:, 2]] = True
    cells = np.argwhere(barrier & air)
    if not len(cells):
        return []
    high = np.array(grid.shape) - 1
    separating = np.zeros(len(cells), bool)
    pairs = np.zeros((len(cells), 2), np.int64)
    for axis in range(3):
        found = []
        for sign in (1, -1):
            room = np.zeros(len(cells), np.int64)
            going = np.ones(len(cells), bool)               # through barrier air only: a solid voxel ends the search
            for step in range(1, 4):
                probe = cells.copy()
                probe[:, axis] += sign * step
                inside = (probe[:, axis] >= 0) & (probe[:, axis] <= high[axis])
                probe = np.clip(probe, 0, high)
                is_air = inside & air[probe[:, 0], probe[:, 1], probe[:, 2]]
                is_barrier = barrier[probe[:, 0], probe[:, 1], probe[:, 2]]
                take = going & is_air & ~is_barrier
                room[take] = labels[probe[take, 0], probe[take, 1], probe[take, 2]]
                going &= is_air & is_barrier
            found.append(room)
        split = (found[0] > 0) & (found[1] > 0) & (found[0] != found[1]) & ~separating
        pairs[split] = np.stack([found[0][split], found[1][split]], axis=1)
        separating |= split
    cells, pairs = cells[separating], np.sort(pairs[separating], axis=1)
    centres = grid.centre(cells)
    covered = np.zeros(len(cells), bool)
    for portal in portals:
        ring = portal_face_ring(portal)
        normal = np.asarray(portal["normal"], float)
        low, top = ring.min(0) - size, ring.max(0) + size
        near = np.flatnonzero(~covered & (centres >= low).all(1) & (centres <= top).all(1))
        if not len(near):
            continue
        relative = centres[near] - ring[0]
        near = near[np.abs(relative @ normal) <= 0.75 * size]
        if not len(near):
            continue
        # inside the convex ring (either winding), each edge moved out by half a voxel
        signs = []
        for a, b in zip(ring, np.roll(ring, -1, axis=0)):
            edge = b - a
            length = np.linalg.norm(edge)
            if length < 1e-6:
                continue
            outward = np.cross(edge, normal) / length
            signs.append((centres[near] - a) @ outward)
        signs = np.array(signs)
        inside = (signs <= 0.5 * size).all(0) | (signs >= -0.5 * size).all(0)
        covered[near[inside]] = True
    cells, pairs = cells[~covered], pairs[~covered]
    if not len(cells):
        return []
    mask = np.zeros(grid.shape, bool)
    mask[cells[:, 0], cells[:, 1], cells[:, 2]] = True
    clusters, _ = ndimage.label(mask, structure=np.ones((3, 3, 3), bool))
    ids = clusters[cells[:, 0], cells[:, 1], cells[:, 2]]
    result = []
    for cluster in np.unique(ids):
        members = ids == cluster
        rooms = Counter(tuple(int(v) for v in pair) for pair in pairs[members]).most_common(1)[0][0]
        points = grid.centre(cells[members])
        result.append({"voxels": int(members.sum()), "rooms": list(rooms), "centre_lt": points.mean(0).round().tolist(),
                       "low_lt": points.min(0).round().tolist(), "high_lt": points.max(0).round().tolist()})
    return sorted(result, key=lambda c: -c["voxels"])


def floor_mismatches(rooms: NearestRoom, polygons: list[Polygon], spacing: float = 16.0) -> dict:
    """The floor check (playbook gate 4): floor samples whose air right above (a voxel and a half: the voxel the
    surface is in is solid) is labelled air of another room than the floor's. The engine finds a party's sector by the
    floor under it, so such a floor puts a party standing there into the wrong sector (a vault drawn black, a fall
    through). Until 2026-11-06 it looked 8 LT up, inside the floor's own solid voxel, and saw almost nothing (Anskram's
    floors running through 19 doorways measured 291 LT²). Returns {(floor room, air room): LT² area}."""
    grid, labels = rooms.grid, rooms.labels
    found = Counter()
    for polygon in polygons:
        if polygon.normal[1] < 0.7 or polygon.role != "static" or polygon.label <= 0:
            continue
        samples = sample_polygon(polygon.points, spacing)
        cells = grid.index(samples + np.array([0.0, 1.5 * grid.size, 0.0]))
        above = labels[cells[:, 0], cells[:, 1], cells[:, 2]]
        weight = polygon.area / max(len(samples), 1)
        for value in above[(above > 0) & (above != polygon.label)]:
            found[(int(polygon.label), int(value))] += weight
    return {f"{a}->{b}": round(area) for (a, b), area in sorted(found.items(), key=lambda kv: -kv[1])}


# --- Faces two rooms see ---------------------------------------------------------------------------------------------

SHARED_PLANE_LT = 0.5           # an edge this close to a face's plane (both ends) lies in it
SHARED_CONTACT_LT = 4.0         # the shortest contact between two faces that counts
SHARED_VOTE_SHARE = 0.2         # a face whose second room has this share of its votes sees that room too
SHARED_CELL_LT = 128.0
SHARED_OPEN_ROOM_SHARE = 0.3    # a room with this share of the drawn faces is the open air: no face's back room
SHARED_UP = 0.7                 # walkable floors keep one room (the engine finds the party's room by its floor)


def _edge_on(edges: np.ndarray, polygon: Polygon, normal: np.ndarray) -> float:
    """The length of the edges (m, 2, 3) lying in the polygon's plane and inside it (its boundary included)."""
    origin = polygon.points[0]
    distance = (edges - origin) @ normal
    edges = edges[(np.abs(distance) <= SHARED_PLANE_LT).all(axis=1)]
    if not len(edges):
        return 0.0
    ring = polygon.points
    inward = np.cross(normal, np.roll(ring, -1, axis=0) - ring)          # convex ring wound about its normal
    inward_length = np.linalg.norm(inward, axis=1)
    keep = inward_length > 1e-9
    inward, ring = inward[keep] / inward_length[keep, None], ring[keep]
    total = 0.0
    for a, b in edges:
        low, high = 0.0, 1.0
        for m, c in zip(inward, ring):
            start, change = (a - c) @ m + SHARED_PLANE_LT, (b - a) @ m
            if abs(change) < 1e-12:
                if start < 0:
                    high = -1.0
                    break
                continue
            t = -start / change
            if change > 0:
                low = max(low, t)
            else:
                high = min(high, t)
            if high <= low:
                break
        if high > low:
            total += (high - low) * float(np.linalg.norm(b - a))
    return total


def shared_rooms(polygons: list[Polygon], stats: Counter, log: dict) -> None:
    """A face in a wall's thickness belongs to the rooms on both sides of it, and the voxels (32-64 LT) cannot tell
    which side it faces: a door jamb or window reveal a few units deep, the band of wall between a raised floor and
    the slab under it, a thin wall between a tavern and the street. The assignment gives it the room whose air is
    nearest, often the outdoor room, and the room it bounds never draws it: lines and slits of sky along wall bases,
    jambs and window frames (Bootcamp, 2026-11-07). Such a face takes a second room (notes['back_label'], the BLV face's
    room behind; the engine draws it when either room is visible): the room of a face that meets it in a concave
    corner (an edge of one lying on the other, each in front of the other's plane: the two bound the same air) or
    goes on in its plane (a wall cut at a room boundary), the longest contact winning, else the second room of its own votes when that has SHARED_VOTE_SHARE of them. Static
    faces only, not walkable floors (the party's room is its floor's), sky faces or a destructible's (cog) faces."""
    drawn = [p for p in polygons if p.role in ("static", "glass", "nonsolid") and p.label > 0
             and not p.texture.lower().endswith("skymarker.dtx")]
    # No back room that holds SHARED_OPEN_ROOM_SHARE of the faces (a region's open air): it is visible from nearly
    # everywhere, and an interior face drawn with it would be drawn always (Bootcamp's frame time doubled,
    # 2026-11-07); seen from the open air through an opening, the interior room is visible through its portal anyway.
    sizes = Counter(p.label for p in drawn)
    open_rooms = {label for label, count in sizes.items() if count >= SHARED_OPEN_ROOM_SHARE * len(drawn)}
    cells = defaultdict(list)
    boxes = []
    for index, polygon in enumerate(drawn):
        low = np.floor((polygon.points.min(0) - SHARED_PLANE_LT) / SHARED_CELL_LT).astype(int)
        high = np.floor((polygon.points.max(0) + SHARED_PLANE_LT) / SHARED_CELL_LT).astype(int)
        boxes.append((polygon.points.min(0) - SHARED_PLANE_LT, polygon.points.max(0) + SHARED_PLANE_LT))
        if np.prod(high - low + 1) > 4096:          # a far-scenery sheet: no wall thickness to share
            continue
        for x in range(low[0], high[0] + 1):
            for y in range(low[1], high[1] + 1):
                for z in range(low[2], high[2] + 1):
                    cells[(x, y, z)].append(index)
    normals = [p.normal for p in drawn]
    edges = [np.stack([p.points, np.roll(p.points, -1, axis=0)], axis=1) for p in drawn]
    for index, polygon in enumerate(drawn):
        if polygon.role != "static" or polygon.notes.get("cog") or normals[index][1] >= SHARED_UP:
            continue
        low = np.floor(boxes[index][0] / SHARED_CELL_LT).astype(int)
        high = np.floor(boxes[index][1] / SHARED_CELL_LT).astype(int)
        if np.prod(high - low + 1) > 4096:
            continue
        candidates = set()
        for x in range(low[0], high[0] + 1):
            for y in range(low[1], high[1] + 1):
                for z in range(low[2], high[2] + 1):
                    candidates.update(cells.get((x, y, z), ()))
        normal, contact = normals[index], Counter()
        for other in candidates:
            neighbour = drawn[other]
            if neighbour.label == polygon.label or neighbour.label in open_rooms:
                continue
            if (boxes[other][0] > boxes[index][1]).any() or (boxes[other][1] < boxes[index][0]).any():
                continue
            # the same wall going on (coplanar, facing the same way), or a concave corner (each has a point in
            # front of the other's plane)
            offsets = (neighbour.points - polygon.points[0]) @ normal
            coplanar = normals[other] @ normal > 0.999 and np.abs(offsets).max() <= SHARED_PLANE_LT
            if not coplanar and (offsets.max() <= SHARED_PLANE_LT
                                 or ((polygon.points - neighbour.points[0]) @ normals[other]).max() <= SHARED_PLANE_LT):
                continue
            length = max(_edge_on(edges[other], polygon, normal), _edge_on(edges[index], neighbour, normals[other]))
            if length >= SHARED_CONTACT_LT:
                contact[neighbour.label] += length
        if contact:
            polygon.notes["back_label"] = contact.most_common(1)[0][0]
            stats["faces_shared_by_corner"] += 1
            continue
        votes = Counter({int(k): v for k, v in polygon.notes.get("votes", {}).items()
                         if int(k) != polygon.label and int(k) not in open_rooms})
        if votes and votes.most_common(1)[0][1] >= SHARED_VOTE_SHARE * sum(polygon.notes["votes"].values()):
            polygon.notes["back_label"] = votes.most_common(1)[0][0]
            stats["faces_shared_by_votes"] += 1
    log["shared_rooms"] = Counter(f"{p.label}->{p.notes['back_label']}" for p in drawn if "back_label" in p.notes)


def restore_continuations(polygons: list[Polygon], dropped: list[Polygon], stats: Counter, log: dict) -> list[Polygon]:
    """A dropped wall (no air in front: assign_faces) that goes on in the plane of a kept wall, facing the same way and
    sharing an edge with it (SHARED_CONTACT_LT), is that wall's continuation into a place too thin for the voxels: the
    face closing the slot between a pilaster and a wall (Bootcamp's west hall, 2026-11-07), which MM9 draws. It is
    kept in that wall's room, the longest contact winning. Walls only (floors have restore_floor_holes). Returns the
    restored polygons and removes them from `dropped` and log['dropped']."""
    kept = [p for p in polygons if p.role == "static" and p.label > 0 and abs(p.normal[1]) < SHARED_UP]
    cells = defaultdict(list)
    for index, polygon in enumerate(kept):
        low = np.floor((polygon.points.min(0) - SHARED_PLANE_LT) / SHARED_CELL_LT).astype(int)
        high = np.floor((polygon.points.max(0) + SHARED_PLANE_LT) / SHARED_CELL_LT).astype(int)
        if np.prod(high - low + 1) > 4096:
            continue
        for x in range(low[0], high[0] + 1):
            for y in range(low[1], high[1] + 1):
                for z in range(low[2], high[2] + 1):
                    cells[(x, y, z)].append(index)
    restored = []
    for polygon in dropped:
        normal = polygon.normal
        if polygon.role != "static" or polygon.notes.get("cog") or abs(normal[1]) >= SHARED_UP:
            continue
        low = np.floor((polygon.points.min(0) - SHARED_PLANE_LT) / SHARED_CELL_LT).astype(int)
        high = np.floor((polygon.points.max(0) + SHARED_PLANE_LT) / SHARED_CELL_LT).astype(int)
        if np.prod(high - low + 1) > 4096:
            continue
        candidates = set()
        for x in range(low[0], high[0] + 1):
            for y in range(low[1], high[1] + 1):
                for z in range(low[2], high[2] + 1):
                    candidates.update(cells.get((x, y, z), ()))
        edges = np.stack([polygon.points, np.roll(polygon.points, -1, axis=0)], axis=1)
        contact = Counter()
        for other in candidates:
            wall = kept[other]
            if wall.normal @ normal <= 0.999 or np.abs((wall.points - polygon.points[0]) @ normal).max() > SHARED_PLANE_LT:
                continue
            wall_edges = np.stack([wall.points, np.roll(wall.points, -1, axis=0)], axis=1)
            length = max(_edge_on(wall_edges, polygon, normal), _edge_on(edges, wall, wall.normal))
            if length >= SHARED_CONTACT_LT:
                contact[wall.label] += length
        if contact:
            polygon.label = contact.most_common(1)[0][0]
            restored.append(polygon)
    if restored:
        gone = {id(p) for p in restored}
        dropped[:] = [p for p in dropped if id(p) not in gone]
        centres = {tuple(p.points.mean(0).round(1)) for p in restored}
        log["dropped"] = [e for e in log["dropped"] if tuple(e["centre_lt"]) not in centres]
        stats["faces_without_air_dropped"] -= len(restored)
        stats["walls_restored_as_continuations"] += len(restored)
    return restored
