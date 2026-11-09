"""
MM9's liquid volumes as the scene's `water_volumes` (devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md §1): the engine
swims, dives and drowns the party in them and binds swimmers to them. One shared rule for every map (the user,
2026-11-06: MM9's volumes are the authority): every volume becomes the scene's water, swum where it is deep enough
and waded where it is not; `swimming(project)` is the switch, on unless overrides.yml says `map: {swim: false}` (an
opt-out that must say why). With it the shared build (`Build.swim_surfaces`) makes the volumes' surfaces non-solid:
the liquid models a map keeps, and any up-facing polygon with a liquid texture (`LIQUID_TEXTURE_WORDS`) at a volume's
top inside its footprint, which is what the maps' own hooks built as wading floors, where a floor lies under it in the
volume (`Beds.has_bed`; over an unbuilt bed, a far sea past a map's near box, it stays a solid wading floor); MM9's swimmers (`SWIMMER_CLASSES`)
placed in a volume float at their DAT height (`swimmer_foot`, dungeon/content.py). A volume MM9 draws with its sprite
(ShowSurface) whose top no built face covers gets one (`drawn_surfaces`).

    volumes = water_volumes(source, project.native)                 # every liquid volume of a DAT world
    volumes = water_volumes(source, project.native, names={"BlueWater0"}, movers={"WaterTrap": 76})

A volume is a liquid-class DAT object (BlueWater, DirtyWater, ClearWater, CorrosiveFluid, Kato, LiquidNitrogen; not
`Hidden`) with a world model of its name. Its pieces are vertical prisms: one per up-facing polygon of the brush (a
6-poly box has one: its footprint), from that polygon's height down to the brush's lowest point under it. A point is
in the volume when it is inside a piece's polygon and between its bottom and top; volumes never collide, the map's
own faces are the walls and beds. Per class: the liquid (`lava` for Kato, MM9 code 5; `water` otherwise) and MM9's
light scale as `tint` (cshell 0x100ac07c); `fog` only from `FogEnable 1` (FogNearZ/FarZ x 2.56, a negative near is
0); `current` (the LT vector in the native frame, x 2.56) only when longer than MM9's threshold of 1 LT/s; a volume
whose model is a mover (DrainWater.scr's WaterTrap, Bathhouse's BlueWater2) takes `mover_door_id`: the door that
moves its top (the caller passes model -> door id; the top is the BLV's stored pose of that door).

Rooms: the air under a surface must be the room above it (the party swims through the surface; the engine crosses
rooms only at portals). `room_mismatches(build, volumes)` samples each piece just under and just over its top and
reports the pieces where the voxel labels differ (`build.stats["water_room_mismatches"]`).
"""

from __future__ import annotations

import numpy as np

from .geometry import poly_ring
from .source import SCALE, lt_vector_to_native

# Class -> (liquid, MM9's light scale under it). LiquidNitrogen also adds 0.1 light in MM9 (not carried).
LIQUIDS = {
    "BlueWater": ("water", (0.0, 0.5, 0.7)),
    "DirtyWater": ("water", (0.25, 0.3, 0.05)),
    "ClearWater": ("water", (0.3, 0.8, 0.8)),
    "CorrosiveFluid": ("water", (0.3, 0.4, 0.0)),
    "Kato": ("lava", (0.5, 0.15, 0.0)),
    "LiquidNitrogen": ("water", (0.0, 0.5, 0.7)),
}
# MM9's AISwimFly classes (generate_mm9_monster_tables.py SWIMMER_SOURCES): placed in a volume, they swim there
SWIMMER_CLASSES = ("JellySpore", "GelatinousSpore", "NettleSpore", "SeaMonsterMale", "SeaMonsterFemale", "Fish")
# A built surface is a liquid's when its MM9 texture path has one of these (Water115, water123/125, Ocean3/4, slime)
LIQUID_TEXTURE_WORDS = ("water", "ocean", "slime", "lava")
# MM9's ShowSurface sprites -> the old import's alias of each (the same in every MM9 map's material aliases): a volume
# that MM9 draws with its sprite and the map builds no face for gets its top as a non-solid face of this texture
# (`drawn_surfaces`); Water2.spr (Bathhouse's never-built tunnels) is not in the extract and stays undrawn
SURFACE_SPRITES = {"water115.spr": "WATEZWECUN", "water125.spr": "WATE27JPCX", "water123.spr": "WATE1XKSQP",
                   "water115flowing.spr": "WATEPOAUQK", "water123flowing.spr": "WATE31AMUQ", "ocean.spr": "OCEAWBKXOO",
                   "ocean3.spr": "OCEA8LH6KA", "ocean4.spr": "OCEABYM7AI", "slime.spr": "SLIM91P4YN"}
SURFACE_SPRITE_TEXELS = 128         # their bitmaps' size; one texel per LT
SURFACE_MATCH_LT = 8.0              # a surface polygon lies within this of its volume's top (hooks build at top + 1 native)
CURRENT_THRESHOLD_LT = 1.0          # MM9 adds a current only when it is longer than this (cshell 0x100995d4)
UP = 0.99                           # an up-facing (top) polygon's normal y


def swimming(project) -> bool:
    """The shared water rule's switch: on for every map unless overrides.yml says `map: {swim: false}`."""
    return bool(project.overrides["map"].get("swim", True))


def liquid_texture(texture: str) -> bool:
    """An MM9 texture path of a liquid surface (`LIQUID_TEXTURE_WORDS` in its file name)."""
    name = str(texture).replace("\\", "/").rsplit("/", 1)[-1].lower()
    return any(word in name for word in LIQUID_TEXTURE_WORDS)


def surface_pieces(source) -> list[tuple]:
    """(volume name, ring (LT x, z), top, bottom) of every piece of every volume, for the surface and swimmer rules."""
    return [(o["name"], piece["ring"], piece["top"], piece["bottom"])
            for o in liquid_objects(source) for piece in pieces_lt(source.models[o["name"]])]


def piece_at(pieces: list[tuple], x: float, y: float, z: float, above: float = 0.0):
    """The piece holding the LT point (x, y, z) (up to `above` over its top), or None."""
    for piece in pieces:
        _, ring, top, bottom = piece
        if bottom - 1.0 <= y <= top + above and _inside(x, z, ring):
            return piece
    return None


def surface_polygon(pieces: list[tuple], polygon):
    """The piece whose top a horizontal up-facing polygon with a liquid texture lies at, inside its footprint (a water
    surface: MM9's own brush face, or a wading floor a map's hook built there), or None."""
    if polygon.normal[1] < UP or not liquid_texture(polygon.texture):
        return None
    x, y, z = polygon.points.mean(0)
    for piece in pieces:
        _, ring, top, _ = piece
        if abs(y - top) <= SURFACE_MATCH_LT and _inside(x, z, ring):
            return piece
    return None


class Beds:
    """The static floors (up-facing polygons) of a polygon list, for `has_bed`."""
    def __init__(self, polygons: list):
        self.floors = [p for p in polygons if p.role == "static" and p.normal[1] > 0.3]
        self.low = np.array([p.points[:, [0, 2]].min(0) for p in self.floors]).reshape(-1, 2)
        self.high = np.array([p.points[:, [0, 2]].max(0) for p in self.floors]).reshape(-1, 2)

    def under(self, x: float, z: float, bottom: float, top: float) -> bool:
        """A floor under (x, z) between bottom and top (LT)."""
        near = np.nonzero((self.low[:, 0] <= x) & (x <= self.high[:, 0]) & (self.low[:, 1] <= z)
                          & (z <= self.high[:, 1]))[0]
        for i in near:
            polygon = self.floors[i]
            if not _inside(x, z, polygon.points[:, [0, 2]]):
                continue
            n = polygon.normal
            y = (n @ polygon.points[0] - n[0] * x - n[2] * z) / n[1]
            if bottom - 1.0 <= y < top - 1.0:
                return True
        return False

    def has_bed(self, polygon, piece: tuple) -> bool:
        """A floor under at least half of five points of the surface polygon (its centre and its corners pulled in),
        within its piece: open water a body would sink through otherwise (an unbuilt seabed)."""
        _, _, top, bottom = piece
        points = polygon.points[:, [0, 2]]
        centre = points.mean(0)
        samples = [centre] + [centre + 0.7 * (q - centre) for q in points[:4]]
        return 2 * sum(self.under(x, z, bottom, top) for x, z in samples) >= len(samples)


def _overlaps(ring_a: np.ndarray, ring_b: np.ndarray) -> bool:
    """Two (x, z) rings overlap: a corner or the centre of one inside the other, or a 5 x 5 sample of b's box inside
    both (a strip of tiles whose centres all lie in a neighbouring piece still covers this one)."""
    for ring, other in ((ring_a, ring_b), (ring_b, ring_a)):
        centre = ring.mean(0)
        # corners pulled in a little: rings that only share an edge do not overlap
        if any(_inside(x, z, other) for x, z in list(centre + 0.95 * (ring - centre)) + [centre]):
            return True
    lo, hi = ring_b.min(0), ring_b.max(0)
    for x in np.linspace(lo[0], hi[0], 7)[1:-1]:
        for z in np.linspace(lo[1], hi[1], 7)[1:-1]:
            if _inside(x, z, ring_b) and _inside(x, z, ring_a):
                return True
    return False


def drawn_surfaces(source, polygons: list, skipped: set) -> list:
    """The tops MM9 draws with a volume's sprite (ShowSurface 1, a sprite of `SURFACE_SPRITES`) for the volumes whose
    model the map skips (not static, not a mover) and where no polygon with a liquid texture lies at that piece's top:
    one non-solid, upward face per piece, over its footprint at its top, with the sprite's texture (registered in the
    source's aliases under the sprite path). The rest of the build treats it as the map's own water surface."""
    from .geometry import Polygon
    covered = [polygon for polygon in polygons if polygon.role != "invisible" and polygon.normal[1] >= UP
               and liquid_texture(polygon.texture)]
    out = []
    for o in liquid_objects(source):
        p = o["properties"]
        sprite = str(p.get("SpriteSurfaceName") or "").replace("\\", "/").rsplit("/", 1)[-1].lower()
        if (not p.get("ShowSurface") or sprite not in SURFACE_SPRITES or o["name"] not in skipped
                or "drainwater" in str(p.get("ScriptName") or "").lower()):
            continue
        texture = str(p["SpriteSurfaceName"])
        source.aliases.setdefault(texture.lower(), {"source_texture": texture, "alias": SURFACE_SPRITES[sprite],
                                                    "width": SURFACE_SPRITE_TEXELS, "height": SURFACE_SPRITE_TEXELS})
        for piece in pieces_lt(source.models[o["name"]]):
            ring, top = piece["ring"], piece["top"]
            if any(abs(c.points[:, 1].mean() - top) <= SURFACE_MATCH_LT and _overlaps(c.points[:, [0, 2]], ring)
                   for c in covered):
                continue
            points = np.array([[x, top, z] for x, z in ring], float)
            mapping = (np.zeros(3), np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0]))
            polygon = Polygon(points, [tuple(np.round(q, 1)) for q in points], texture, mapping, 0x1081, o["name"],
                              "nonsolid")
            if polygon.normal[1] < 0:
                polygon = Polygon(points[::-1], [tuple(np.round(q, 1)) for q in points[::-1]], texture, mapping,
                                  0x1081, o["name"], "nonsolid")
            polygon.notes.update(width=SURFACE_SPRITE_TEXELS, height=SURFACE_SPRITE_TEXELS)
            out.append(polygon)
    return out


def untextured_volume_faces(source, polygons: list) -> int:
    """A liquid volume kept as geometry draws its polygons with the volume's surface sprite (`SpriteSurfaceName`, a
    sprite of `SURFACE_SPRITES`) where MM9 gave them no texture of their own ("Default", the editor's untextured
    marker): Frosgard's teleporter to Yanmir's Fort is a thin upright ClearWater (WavySurface4, Water115.spr) whose
    faces drew as the converter's placeholder, a green checkerboard, until 2026-11-08 (a player's report; the gates at
    the Yanmir's Fort end carry Water115 on their brushes). Returns how many polygons were retextured."""
    count = 0
    volumes = {o["name"]: o["properties"] for o in liquid_objects(source)}
    for polygon in polygons:
        properties = volumes.get(polygon.model)
        if properties is None or polygon.role == "invisible":
            continue
        if polygon.texture.replace("\\", "/").rsplit("/", 1)[-1].lower() not in ("default", "default.dtx"):
            continue
        texture = str(properties.get("SpriteSurfaceName") or "")
        sprite = texture.replace("\\", "/").rsplit("/", 1)[-1].lower()
        if sprite not in SURFACE_SPRITES:
            continue
        source.aliases.setdefault(texture.lower(), {"source_texture": texture, "alias": SURFACE_SPRITES[sprite],
                                                    "width": SURFACE_SPRITE_TEXELS, "height": SURFACE_SPRITE_TEXELS})
        polygon.texture = texture
        polygon.notes.update(width=SURFACE_SPRITE_TEXELS, height=SURFACE_SPRITE_TEXELS)
        count += 1
    return count


def swimmer_foot(build, o: dict, height: float, pieces: list[tuple]) -> int | None:
    """A swimmer's foot (the actor's z, native) when MM9 placed it in a volume, else None: MM9's position is the centre
    of its body box (Gravity 0, MoveToFloor 0), so the box's centre goes there, then down until the box is under the
    volume's top and up to clear the bed (the models carry MM9's origin at the box centre; outdoor_blv.py's sea rule)."""
    pos = o["properties"]["Pos"]
    piece = piece_at(pieces, pos[0], pos[1], pos[2], above=float(height) / SCALE)
    if piece is None:
        return None
    native = build.project.native
    foot = float(native(np.array(pos, float))[2]) - height / 2
    surface = float(native(np.array([pos[0], piece[2], pos[2]], float))[2])
    foot = min(foot, surface - height - 8.0)
    bed = build.content.floor_at(pos[0], pos[2], pos[1])
    if bed is not None:
        foot = max(foot, float(native(np.array([pos[0], bed, pos[2]], float))[2]) + 1.0)
    return int(round(foot))


def liquid_objects(source, names=None) -> list[dict]:
    """The DAT objects of a liquid class that are not Hidden and have a world model of their name."""
    wanted = None if names is None else {name.lower() for name in names}
    found = []
    for o in source.objects:
        if o["class"] not in LIQUIDS or o["properties"].get("Hidden"):
            continue
        if wanted is not None and o["name"].lower() not in wanted:
            continue
        if o["name"] in source.models:
            found.append(o)
    return found


def _normal(points: np.ndarray) -> np.ndarray:
    normal = np.zeros(3)
    for k in range(1, len(points) - 1):
        normal += np.cross(points[k] - points[0], points[k + 1] - points[0])
    length = np.linalg.norm(normal)
    return normal / length if length > 1e-9 else normal


def _inside(x: float, z: float, ring: np.ndarray) -> bool:
    hit = False
    for (x1, z1), (x2, z2) in zip(ring, np.roll(ring, -1, axis=0)):
        if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / (z2 - z1) + x1:
            hit = not hit
    return hit


def pieces_lt(model) -> list[dict]:
    """The brush's pieces in LithTech units: {ring (x, z points), top (y), bottom (y)}."""
    polygons = []
    for poly in model.polies:
        ring = poly_ring(poly)
        if len(ring) >= 3:
            points = np.array([model.points[i] for i in ring], float)
            polygons.append((points, _normal(points)))
    out = []
    for points, normal in polygons:
        if normal[1] < UP:
            continue
        ring = points[:, [0, 2]]
        top = float(points[:, 1].mean())
        # The brush's lowest point under the top: the down-facing polygons whose centre lies under it (a box's one
        # bottom), else the whole brush's lowest point.
        under = [float(p[:, 1].min()) for p, n in polygons
                 if n[1] < -UP and _inside(*p[:, [0, 2]].mean(0), ring)]
        under += [float(q[1]) for p, n in polygons for q in p if n[1] < -UP and _inside(q[0], q[2], ring)]
        bottom = min(under) if under else float(min(p[:, 1].min() for p, _ in polygons))
        if bottom < top:
            out.append({"ring": ring, "top": top, "bottom": bottom})
    return out


def volume(source, native, o: dict, mover_door_id: int | None = None) -> dict | None:
    """One DAT liquid object as a scene volume (native units), or None when its brush has no top."""
    model = source.models[o["name"]]
    p = o["properties"]
    liquid, tint = LIQUIDS[o["class"]]
    pieces = []
    for piece in pieces_lt(model):
        ring = piece["ring"]
        points = native(np.stack([ring[:, 0], np.full(len(ring), piece["top"]), ring[:, 1]], axis=1))
        bottom = float(native(np.array([ring[0, 0], piece["bottom"], ring[0, 1]]))[2])
        pieces.append({"polygon": [[round(float(x), 1), round(float(y), 1)] for x, y in points[:, :2]],
                       "bottom": round(bottom, 1), "top": round(float(points[0, 2]), 1)})
    if not pieces:
        return None
    block = {"id": o["name"], "liquid": liquid, "pieces": pieces, "tint": list(tint)}
    if p.get("FogEnable"):
        block["fog"] = {"color_rgb": [int(round(min(255.0, max(0.0, float(c))))) for c in p.get("FogColor", [0, 0, 0])],
                        "near_distance": round(max(0.0, float(p.get("FogNearZ", 0.0))) * SCALE, 1),
                        "far_distance": round(max(1.0, float(p.get("FogFarZ", 300.0))) * SCALE, 1)}
        if block["fog"]["far_distance"] <= block["fog"]["near_distance"]:
            block["fog"]["far_distance"] = block["fog"]["near_distance"] + 1.0
    current = np.asarray(p.get("Current") or [0, 0, 0], float)
    if np.linalg.norm(current) > CURRENT_THRESHOLD_LT:
        block["current"] = [round(float(v) * SCALE, 1) for v in lt_vector_to_native(current)]
    if mover_door_id is not None:
        block["mover_door_id"] = int(mover_door_id)
    return block


def water_volumes(source, native, names=None, movers: dict | None = None) -> list[dict]:
    """Every liquid volume of the DAT world (or those named), as the scene's `water_volumes` entries. `native` maps
    LithTech points to the native frame (Project.native); `movers` maps a volume's DAT name to the door id that moves
    its top."""
    movers = {name.lower(): door for name, door in (movers or {}).items()}
    out = []
    for o in liquid_objects(source, names):
        block = volume(source, native, o, movers.get(o["name"].lower()))
        if block is not None:
            out.append(block)
    return out


def mover_doors(build, names) -> dict:
    """{DAT model name: door id} for the given mover models, from the build's movers (work/doors.json)."""
    doors = {}
    for mover in build.movers:
        for model in mover.get("dat_models", []):
            if model in names:
                doors[model] = mover["door_id"]
    return doors


def room_mismatches(build, objects: list[dict], depth_lt: float = 6.0) -> list[dict]:
    """The pieces whose air just under the top is another room than the air just over it (sampled on a grid over the
    piece; points in solid voxels skipped). Empty when the surface joins one room."""
    grid, labels = build.grid, build.labels
    found = []
    for o in objects:
        for k, piece in enumerate(pieces_lt(build.source.models[o["name"]])):
            ring = piece["ring"]
            lo, hi = ring.min(0), ring.max(0)
            xs = np.linspace(lo[0], hi[0], 9)[1:-1]
            zs = np.linspace(lo[1], hi[1], 9)[1:-1]
            pairs = {}
            for x in xs:
                for z in zs:
                    if not _inside(x, z, ring):
                        continue
                    cells = grid.index(np.array([[x, piece["top"] - depth_lt, z], [x, piece["top"] + depth_lt, z]]))
                    below, above = (int(labels[c[0], c[1], c[2]]) for c in cells)
                    if below and above and below != above:
                        pairs[(below, above)] = pairs.get((below, above), 0) + 1
            if pairs:
                found.append({"volume": o["name"], "piece": k, "rooms_below_above": [list(key) + [n] for key, n in
                                                                                     pairs.items()]})
    return found


def _inside_many(x: np.ndarray, z: np.ndarray, ring: np.ndarray) -> np.ndarray:
    """`_inside` over arrays of points (the same crossing test per edge, elementwise)."""
    hit = np.zeros(np.shape(x), bool)
    with np.errstate(divide="ignore", invalid="ignore"):
        for (x1, z1), (x2, z2) in zip(ring, np.roll(ring, -1, axis=0)):
            hit ^= ((z1 > z) != (z2 > z)) & (x < (x2 - x1) * (z - z1) / (z2 - z1) + x1)
    return hit


def bed_holes(build, objects: list[dict], spacing_lt: float = 24.0) -> list[dict]:
    """Points of open water with no floor under them inside the volume: a sample of a piece just under its top that is
    labelled air and has no static up-facing polygon between the piece's bottom and its top (a swimmer would sink out
    of the map). Samples inside rock (no air) do not count: MM9's brushes run on under the ground round the water.
    Each piece's samples are one (x, z) lattice; each floor tests only the lattice block under its box (the per-sample
    scan over every floor took most of a region's build: Lindisfarne's 300 000 holes)."""
    grid, labels = build.grid, build.labels
    floors = [p for p in build.polygons if p.role == "static" and p.normal[1] > 0.3]
    boxes = [(p.points[:, [0, 2]].min(0), p.points[:, [0, 2]].max(0)) for p in floors]
    holes = []
    for o in objects:
        for k, piece in enumerate(pieces_lt(build.source.models[o["name"]])):
            ring = piece["ring"]
            lo, hi = ring.min(0), ring.max(0)
            xs = np.arange(lo[0] + spacing_lt / 2, hi[0], spacing_lt)
            zs = np.arange(lo[1] + spacing_lt / 2, hi[1], spacing_lt)
            if not len(xs) or not len(zs):
                continue
            x, z = np.meshgrid(xs, zs, indexing="ij")
            wet = _inside_many(x, z, ring)
            points = np.stack([x, np.full(x.shape, piece["top"] - grid.size), z], axis=-1)
            cells = grid.index(points.reshape(-1, 3))
            wet &= (labels[cells[:, 0], cells[:, 1], cells[:, 2]] != 0).reshape(x.shape)
            if not wet.any():
                continue
            found = np.zeros(x.shape, bool)
            for polygon, (low, high) in zip(floors, boxes):
                i0, i1 = np.searchsorted(xs, low[0], "left"), np.searchsorted(xs, high[0], "right")
                j0, j1 = np.searchsorted(zs, low[1], "left"), np.searchsorted(zs, high[1], "right")
                if i0 >= i1 or j0 >= j1:
                    continue
                block = wet[i0:i1, j0:j1] & ~found[i0:i1, j0:j1]
                if not block.any():
                    continue
                bx, bz = x[i0:i1, j0:j1], z[i0:i1, j0:j1]
                corners = polygon.points
                block &= _inside_many(bx, bz, corners[:, [0, 2]])
                n = polygon.normal
                y = (n @ corners[0] - n[0] * bx - n[2] * bz) / n[1]
                block &= (piece["bottom"] - 1.0 <= y) & (y < piece["top"])
                found[i0:i1, j0:j1] |= block
            open_water = wet & ~found
            if open_water.any():
                where = np.stack([x[open_water], np.full(int(open_water.sum()), piece["top"]), z[open_water]], axis=1)
                for native in build.project.native(where).round().astype(int).tolist():
                    holes.append({"volume": o["name"], "piece": k, "native": native})
    return holes
