"""
The pose MM9 draws a prop in: LithTech draws a Static_Model prop in its model's first animation at its first key
(Thjorgard City's props `first_pose_points`, 2026-11-01), and the props projects' GLBs are the ABC's bind mesh. The
`*NS` furniture (BookCase02NS, DresserNS, Desk01NS, Cabinet0xNS, Stovens, Table01NS, the pews, WeaponRackNS...) is its
`*EW` / plain twin's file with one difference: its static animation turns the Scene Root a quarter about the vertical.
Drawn unposed, every such prop stood a quarter turn off: bookcases and dressers with their sides to the wall
(Anskram Keep, Kluso's House, 2026-11-06), Thjorgard's library bookcases through its wall. The old transcoder's bake,
which the props projects' placements fit to, carries the same error.

A prop running PropAnim.scr loops the animation its ScriptParams name ("ns", "ew") instead: MM9 draws it in that
animation's pose, which turns some models a quarter from their first animation (the Anskram Keep's BedMedium "ew", Kluso's
weapon cabinets and trestle table "ns", the Lindisfarne and Temple of Honk stone benches "NS", the Beethoven and 1000
Terrors raised coffins "ns"; 2026-11-07). That is this module's one rule for it: the props projects' own `POSE_TURN`
tables are retired.

`placement(entry, objects)` gives the native (position, yaw) of a props.json entry with the pose applied: the bind
model turned by the pose about the ABC origin, as MM9 draws it, and the decoration's GLB placed to match. Only models
whose pose turns the whole mesh a quarter (or half) turn and whose GLB is that unturned bind mesh change; every other
entry keeps its props.json placement (the torches, the posed axes and statues, whose GLBs carry their pose).
The yaw is MM9's own facing (-ry, the props' convention) plus the pose turn; props.json yaw fixes made against the old
bake for these models (Kluso's `YAW_FIX`) are replaced, and an entry that already holds the pose (`pose_turn_degrees`,
Thjorgard City) gives the same result.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from .source import ROOT

sys.path.insert(0, str(ROOT / "tools/mm9_import_discovery"))
MODELS = ROOT / "mm9/extracted/MODELS"
QUARTER_TOLERANCE = 1.0         # degrees: a pose turn is a quarter, half or three-quarter turn within this
RIGID_TOLERANCE = 2.0           # native units: the posed mesh is the bind mesh turned about the vertical within this
RIGID_SHARE = 0.6               # ... for at least this share of its vertices (Kluso's weapon cabinet's "NS" pose turns
                                # the cabinet a quarter with its doors ajar: 73 % of it is the bind mesh turned)
GLB_FIT_TOLERANCE = 3.0         # native units: median distance of a bind-mesh GLB from the bind mesh
LT_UNITS = 2.56                 # native units per LithTech unit

_abc_cache: dict = {}
_glb_cache: dict = {}
_fit_cache: dict = {}


def _rotation(degrees: float) -> np.ndarray:
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def resolve_model(source_model: str) -> Path | None:
    """An ABC path from a DAT `Filename` (models\\Props\\DresserNS.ABC), found case-insensitively under MODELS."""
    parts = [p for p in str(source_model).replace("\\", "/").split("/") if p]
    folder = MODELS
    for part in parts:
        if not folder.is_dir():
            return None
        found = next((c for c in folder.iterdir() if c.name.lower() == part.lower()), None)
        if found is None and folder.parent == MODELS.parent and folder == MODELS:
            found = next((c for c in folder.iterdir() if c.name.lower() == "models"), None)
            if found is not None:
                found = next((c for c in found.iterdir() if c.name.lower() == part.lower()), None)
        if found is None:
            return None
        folder = found
    return folder if folder.is_file() else None


def _quaternion_matrix(rotation, translation) -> np.ndarray:
    x, y, z, w = rotation
    m = np.eye(4)
    m[:3, :3] = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                 [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                 [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    m[:3, 3] = translation
    return m


def dat_name(entry: dict) -> str:
    """A props.json entry's DAT object name: a repeated DAT name's later objects are renamed <name>_<object index>
    and keep the DAT's in `dat_name` (Sturmford City's two Table0)."""
    return str(entry.get("dat_name") or entry.get("source_name", ""))


def scripted_animation(properties: dict) -> str:
    """The animation a DAT object's PropAnim.scr loops (its ScriptParams), or "" for an object without that script."""
    if "propanim" not in str(properties.get("ScriptName", "") or "").lower():
        return ""
    return str(properties.get("ScriptParams", "") or "").strip()


def bind_and_pose(source_model: str, animation: str = ""):
    """(bind, posed) LOD0 vertices of an ABC in native-local axes ((x, z, y) of LithTech) and native units at scale
    1: the bind mesh and the mesh at the first key of the named animation (case-insensitive; PropAnim.scr's), else of
    its first animation; posed is None without an animation."""
    key = (str(source_model).lower(), animation.lower())
    if key in _abc_cache:
        return _abc_cache[key]
    path = resolve_model(source_model)
    if path is None:
        _abc_cache[key] = (None, None)
        return _abc_cache[key]
    from convert_abc_model import read_abc, source_animation_pose
    model = read_abc(path)
    vertices = [v for piece in model.pieces for v in piece.lods[0].vertices]
    bind = np.array([v.position for v in vertices], float)
    posed = None
    if model.animations:
        chosen = next((a for a in model.animations if animation and a.name.lower() == animation.lower()),
                      model.animations[0])
        pose = source_animation_pose(model, chosen, 0.0)
        parents = {child: index for index, node in enumerate(model.nodes) for child in node.children}
        world = []
        for index in range(len(model.nodes)):
            local = _quaternion_matrix(pose[index].rotation, pose[index].translation)
            world.append(local if index not in parents else world[parents[index]] @ local)
        skin = [w @ np.linalg.inv(node.bind_matrix) for w, node in zip(world, model.nodes)]
        posed = np.array([sum(weight.bias * (skin[weight.node_index] @ np.append(v.position, 1.0))
                              for weight in v.weights)[:3] for v in vertices])
    swap = np.array([0, 2, 1])
    _abc_cache[key] = (bind[:, swap] * LT_UNITS, None if posed is None else posed[:, swap] * LT_UNITS)
    return _abc_cache[key]


def pose_turn(source_model: str, animation: str = "") -> tuple[float, np.ndarray]:
    """(degrees, offset): the native turn about the vertical and the plan shift that take the bind mesh to MM9's
    posed mesh (posed = R(degrees) bind + offset, native-local, scale 1), for a pose that only turns the whole mesh by
    a quarter, half or three-quarter turn (most of its vertices: a door may swing in it); (0, 0) for any other model
    (no pose, an unturned pose, or one that moves most of its pieces: a pose built into the props project's GLB,
    Thjorgard's `POSES`). Measured on the vertices (a 2D Procrustes fit), not read off the root key. animation: the one PropAnim.scr loops (scripted_animation)."""
    bind, posed = bind_and_pose(source_model, animation)
    if bind is None or posed is None or not len(bind):
        return 0.0, np.zeros(3)
    a, b = bind[:, :2], posed[:, :2]
    ca, cb = a.mean(0), b.mean(0)
    h = (a - ca).T @ (b - cb)
    angle = math.degrees(math.atan2(h[0, 1] - h[1, 0], h[0, 0] + h[1, 1]))
    quarter = round(angle / 90.0) * 90.0
    if not quarter % 360 or abs(angle - quarter) > QUARTER_TOLERANCE:
        return 0.0, np.zeros(3)
    rotation = _rotation(quarter)
    offset = np.median(posed - bind @ rotation.T, axis=0)
    offset[2] = 0.0
    if np.mean(np.linalg.norm(bind @ rotation.T + offset - posed, axis=1) <= RIGID_TOLERANCE) < RIGID_SHARE:
        return 0.0, np.zeros(3)
    return quarter, offset


def glb_points(model: str, height: float) -> np.ndarray:
    """A decoration GLB's first mesh vertices placed as the engine places them: glTF (x, y, z) -> native (-x, z, y),
    scaled to the binding height."""
    key = (model, height)
    if key not in _glb_cache:
        native = _glb_native(model)
        _glb_cache[key] = native * (height / max(float(np.ptp(native[:, 2])), 1e-6))
    return _glb_cache[key]


def binding_points(binding: dict) -> np.ndarray:
    """A binding's points as the engine places them: its model's (glb_points) and its moving parts' at rest, which are
    authored in the model's asset space and drawn at the model's scale (devdocs/ANIMATED_DECORATIONS.md)."""
    height = float(binding["height"])
    points = [glb_points(binding["model"], height)]
    if binding.get("parts"):
        native = _glb_native(binding["model"])
        scale = height / max(float(np.ptp(native[:, 2])), 1e-6)
        points += [_glb_native(part, at_rest=True) * scale for part in binding["parts"]]
    return np.concatenate(points)


def _glb_native(model: str, at_rest: bool = False) -> np.ndarray:
    """A GLB's first mesh vertices in native axes (-x, z, y), unscaled; at_rest: moved by their node's own transform
    (a part's rest)."""
    key = (model, "rest" if at_rest else None)
    if key in _glb_cache:
        return _glb_cache[key]
    data = (ROOT / "assets_source" / model).read_bytes()
    length = int.from_bytes(data[12:16], "little")
    document = json.loads(data[20:20 + length])
    binary = data[20 + length + 8:]
    node = next(n for n in document["nodes"] if "mesh" in n)
    points = []
    for primitive in document["meshes"][node["mesh"]]["primitives"]:
        accessor = document["accessors"][primitive["attributes"]["POSITION"]]
        view = document["bufferViews"][accessor["bufferView"]]
        start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        stride = view.get("byteStride", 12)
        raw = np.frombuffer(binary, np.uint8, count=stride * (accessor["count"] - 1) + 12, offset=start)
        rows = np.lib.stride_tricks.as_strided(raw, (accessor["count"], 12), (stride, 1)).copy()
        points.append(rows.view(np.float32).reshape(-1, 3).astype(float))
    a = np.concatenate(points)
    if at_rest:
        a = a @ _node_matrix(node)[:3, :3].T + _node_matrix(node)[:3, 3]
    native = np.stack([-a[:, 0], a[:, 2], a[:, 1]], 1)
    _glb_cache[key] = native
    return native


def glb_fit(binding: dict, source_model: str, scale: float) -> tuple[float, np.ndarray, float]:
    """(turn, offset, distance): the binding's GLB placed unturned at the origin matches the bind mesh (at the DAT
    scale) turned by `turn` (0, 90, 180 or 270) and moved by `offset`, bind ~ R(turn) glb + offset, at this median
    vertex distance. The GLB is the bind mesh as its props project built it (mirrored, maybe turned), its origin at its
    base centre; a split prop's moving parts at rest count with it (binding_points: its body alone, a chest without
    its lid, would centre off the bind mesh)."""
    key = (binding["model"], tuple(binding.get("parts") or ()), round(float(binding["height"]), 3),
           str(source_model).lower(), round(scale, 4))
    if key in _fit_cache:
        return _fit_cache[key]
    glb = binding_points(binding)
    bind, _ = bind_and_pose(source_model)
    bind = bind * scale
    tree = cKDTree(bind)
    best = None
    for turn in (0, 90, 180, 270):
        turned = glb @ _rotation(turn).T
        offset = (bind.min(0) + bind.max(0)) / 2 - (turned.min(0) + turned.max(0)) / 2
        distance = float(np.median(tree.query(turned + offset)[0]))
        if best is None or distance < best[0]:
            best = (distance, turn, offset)
    _fit_cache[key] = (float(best[1]), best[2], best[0])
    return _fit_cache[key]


def placement(entry: dict, objects: list, binding: dict | None) -> tuple[tuple, float] | None:
    """The native (position, yaw degrees) of a props.json entry drawn in MM9's pose, or None when its model's pose
    does not turn it, whose GLB is not its unturned bind mesh (a props project that built the pose or a turn into its
    GLB placed it against that), or whose DAT object, model or binding is missing: the caller keeps the entry's own
    placement.

    The GLB point g lands at P + R(yaw) g. With bind ~ R(turn) g + offset, the entry places the bind model's origin
    at P - R(yaw - turn) offset, turned yaw - turn. MM9 turns the bind model by the DAT facing (-ry) and the pose
    (posed = R(pose) bind + pose_offset) about that origin, so the GLB takes yaw' = -ry + pose + turn at
    origin + R(-ry) pose_offset + R(yaw' - turn) offset."""
    index = entry.get("source_object")
    model = entry.get("source_model")
    if binding is None or not model or not isinstance(index, int) or not 0 <= index < len(objects):
        return None
    properties = objects[index]["properties"]
    if str(properties.get("Name", "")).lower() != dat_name(entry).lower():
        return None
    angle, pose_offset = pose_turn(model, scripted_animation(properties))
    if not angle:
        return None
    scale = float(properties.get("Scale", 1.0) or 1.0)
    turn, offset, distance = glb_fit(binding, model, scale)
    if turn or distance > GLB_FIT_TOLERANCE:
        return None
    facing = -math.degrees(float((properties.get("Rotation") or [0, 0, 0, 0])[1]))
    yaw_old = float(entry["yaw_degrees"])
    position = np.array([entry["x"], entry["y"], entry["z"]], float)
    origin = position - _rotation(yaw_old - turn) @ offset
    yaw = (facing + angle + turn) % 360.0
    new = origin + _rotation(facing) @ (pose_offset * scale) + _rotation(yaw - turn) @ offset
    return (float(new[0]), float(new[1]), float(position[2])), round(yaw, 2)


# How MM9 places a prop (traced in lithtech.exe and object.lto, devdocs/mm9_rework/MM9_PROP_PLACEMENT_RE.md,
# 2026-11-07; it replaces the fitted rule of before, a prop standing by its base on a surface 4 under to 24 over its
# DAT Pos). The server creates the object at its DAT Pos with dims (1, 1, 1) (lithtech.exe 0x0044af18); ModelObject's
# initial update applies the DAT Scale (the server's SetObjectScale leaves the dims alone); ObjectBase's then takes the
# model's first animation user dims D, unscaled (GetModelAnimUserDims), and ModelObject's dims setter (object.lto
# 0x100beb20) sets the dims to D x Scale and moves the object up by D.y minus its dims before: D.y - 1 LithTech unit.
# Nothing is tested: no collision, no floor. The model is drawn at the object's position plus the binding translation.
# So a chair stored with its Pos on the floor rises by its half height and stands there, a candle stored on its table
# top stands on the table, a lamp rises by its own half height. A MoveToFloor object then drops (move_to_floor).
# The lift belongs to ModelObject: every class whose dims setter is ModelObject's (object.lto vtables, slot 0x38) is
# lifted; Torch, WallTorch and Brazier (Fire > ObjectBase), doors and the AI have other setters and are not.
# The props.json placements fit the old bake, which drew every model at its DAT Pos plus the translation.
LIFT_CLASSES = frozenset(name.lower() for name in (
    "BagGold", "Barrel", "BonePile", "ButterFlyCloud", "CandleProp", "Cauldron", "Clover", "Cookpot", "Corpse",
    "DeathMatchItem", "DestructableProp", "Drip", "FadeAwayInventoryItem", "Fan", "Fountain", "InventoryItem",
    "MeleeWeapon", "ModelObject", "ModelProp", "PickupItem", "ProjectileWeapon", "Prop", "PropDamager", "RUDEProp",
    "RollingProp", "SpawnedInventoryItem", "Sphere", "StatStone", "TreasureBag", "TreasureBase", "TreasureChest",
    "Weapon", "WellMMIX"))
CREATE_DIMS = LT_UNITS     # native units: the dims y a server object is created with (1 LithTech unit)
_box_cache: dict = {}


def model_box(properties: dict) -> tuple[np.ndarray, np.ndarray] | None:
    """(dims, translation) of a DAT model object, native axes and units, times its Scale, from its ABC's animation
    bindings (the AnimBindings record, lithtech.exe 0x00442d4e: user dims at +8, translation at +0x14), or None. The
    dims are the "STATIC_MODEL" animation's when the model has one (object.lto 0x100bd8d0 asks for it by name;
    Sarcophagus2vert and Sven have it third and fourth), else the first animation's; the translation is the first's."""
    filename = str(properties.get("Filename", ""))
    key = filename.lower()
    if key not in _box_cache:
        path = resolve_model(filename) if key.endswith(".abc") else None
        box = None
        if path is not None:
            from convert_abc_model import read_abc
            bindings = read_abc(path).anim_bindings
            if bindings:
                swap = [0, 2, 1]
                sized = next((b for b in bindings if b.name.lower() == "static_model"), bindings[0])
                box = (np.abs(np.asarray(sized.extents, float))[swap] * LT_UNITS,
                       np.asarray(bindings[0].origin, float)[swap] * LT_UNITS)
        _box_cache[key] = box
    box = _box_cache[key]
    if box is None:
        return None
    scale = float(properties.get("Scale", 1.0) or 1.0)
    return box[0] * scale, box[1] * scale


def lift(properties: dict, class_name: str) -> float:
    """The native height MM9 moves a DAT object up by at its initial update: its model's first animation user dims
    y, unscaled, less the dims it was created with, for the lifted classes (LIFT_CLASSES); 0 for the others."""
    if class_name.lower() not in LIFT_CLASSES:
        return 0.0
    box = model_box(properties)
    if box is None:
        return 0.0
    scale = float(properties.get("Scale", 1.0) or 1.0)
    return float(box[0][2]) / scale - CREATE_DIMS


SWAP = np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]], float)      # LithTech (x, y up, z) <-> native (x, y, z up) axes
UPRIGHT = 0.05             # radians: a prop with pitch and roll under this stands upright


def lt_euler(rotation) -> np.ndarray:
    """LithTech's rotation matrix of DAT Euler radians (pitch about x, yaw about y, roll about z), applied roll, then
    pitch, then yaw (R = Ry Rx Rz), right-handed in LithTech coordinates."""
    p, y, r = (float(v) for v in (list(rotation or [0, 0, 0]) + [0, 0, 0])[:3])
    cx, sx, cy, sy, cz, sz = math.cos(p), math.sin(p), math.cos(y), math.sin(y), math.cos(r), math.sin(r)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rzz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return ry @ rx @ rzz


def mm9_mesh(properties: dict, position, animation: str | None = None) -> np.ndarray | None:
    """The mesh MM9 draws for a DAT model object whose box centre is at a native position: its posed ABC (prop's
    PropAnim animation, else the first) at the DAT Scale, offset by the binding translation and turned by the full
    DAT Rotation (in native axes; the swap is a reflection), or None without the ABC. A model without bindings has no
    translation. animation: the animation to pose it in instead (a script's LoopAnim)."""
    clip = scripted_animation(properties) if animation is None else animation
    bind, posed = bind_and_pose(str(properties.get("Filename", "")), clip)
    if bind is None:
        return None
    box = model_box(properties)
    local = (posed if posed is not None else bind) * float(properties.get("Scale", 1.0) or 1.0)
    local = local if box is None else local + box[1]
    rotation = SWAP @ lt_euler(properties.get("Rotation")) @ SWAP
    return local @ rotation.T + np.asarray(position, float)


def mm9_centres(objects: list, native, floor_z) -> dict:
    """DAT object index -> the native box centre MM9 leaves each lifted object at after its initial update, in DAT
    (creation) order: its DAT Pos raised by `lift`, then for a MoveToFloor object the drop (object.lto 0x100c1630): a
    ray straight down from the centre (flags 3: the world and solid objects) and, when the box bottom is over what it
    hits, the centre to hit + dims y + 0.1 - 2 LT units (the box 1.9 units into it). The solid objects it can hit are
    the lifted ones created before it, at their own centres. floor_z(x, y, z_max): the world floor's native height under
    a point, or None."""
    centres, solids = {}, []
    for obj in objects:
        properties = obj["properties"]
        if obj["class"].lower() not in LIFT_CLASSES or properties.get("Pos") is None:
            continue
        box = model_box(properties)
        centre = native(np.asarray(properties["Pos"], float)) + np.array([0.0, 0.0, lift(properties, obj["class"])])
        if properties.get("MoveToFloor", 0) and box is not None:
            hits = [h for h in [floor_z(float(centre[0]), float(centre[1]), float(centre[2]))] if h is not None]
            for other_centre, other_dims in solids:
                top = float(other_centre[2] + other_dims[2])
                if top <= centre[2] and np.all(np.abs(other_centre[:2] - centre[:2]) <= other_dims[:2]):
                    hits.append(top)
            if hits and centre[2] - box[0][2] > max(hits):
                centre[2] = max(hits) + box[0][2] + (0.1 - 2.0) * LT_UNITS
        centres[obj["index"]] = centre
        if properties.get("Solid", 0) and box is not None:
            solids.append((centre, box[0]))
    return centres


def lifted(entry: dict, objects: list, binding: dict | None, position, native):
    """A props.json entry's decoration position (native, from `position`: its props.json one, posed) where MM9 draws
    its DAT object after the initial update's lift (`lift`), or None when the entry is not a MoveToFloor-0 object of a
    lifted class drawn with MM9's own model: other decorations stand in for MM9's (the regions' MM6-MM8 trees, sunk as
    their own worlds sink them), the seated townsfolk keep their seat z_offset (seats.py). The plan position is kept;
    the height comes from MM9's own mesh at the lifted position (mm9_mesh, its lowest point the GLB's), since some
    props.json heights were raised by hand against the old bake. A tilted prop, whose GLB is a fitted variant rather
    than the ABC turned, moves from its props.json height by the lift. native: the project's LithTech -> native
    transform."""
    index = entry.get("source_object")
    if binding is None or binding.get("z_offset") or not isinstance(index, int) or not 0 <= index < len(objects):
        return None
    obj = objects[index]
    properties = obj["properties"]
    if str(properties.get("Name", "")).lower() != dat_name(entry).lower() or properties.get("MoveToFloor", 0):
        return None
    if not Path(str(binding["model"])).name.lower().startswith("mm9") or properties.get("Pos") is None:
        return None
    rise = lift(properties, obj["class"])
    if obj["class"].lower() not in LIFT_CLASSES or model_box(properties) is None:
        return None
    result = np.asarray(position, float) + np.array([0.0, 0.0, rise])
    pitch, _, roll = (list(properties.get("Rotation") or [0, 0, 0]) + [0, 0, 0])[:3]
    if abs(float(pitch)) < UPRIGHT and abs(float(roll)) < UPRIGHT:
        mesh = mm9_mesh(properties, native(np.asarray(properties["Pos"], float)) + np.array([0.0, 0.0, rise]))
        if mesh is not None:
            lowest = float(binding_points(binding)[:, 2].min())   # a split prop's parts (a bell) may hang lowest
            result[2] = float(mesh[:, 2].min()) - lowest
    return tuple(float(v) for v in result)


_mesh_cache = {}


def _node_matrix(node: dict) -> np.ndarray:
    if "matrix" in node:
        return np.array(node["matrix"], float).reshape(4, 4).T
    m = np.eye(4)
    x, y, z, w = node.get("rotation", [0, 0, 0, 1])
    m[:3, :3] = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                 [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                 [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    m[:3, :3] = m[:3, :3] * np.array(node.get("scale", [1, 1, 1]))
    m[:3, 3] = node.get("translation", [0, 0, 0])
    return m


def glb_mesh(model: str):
    """(points, triangles) of a GLB's LOD0 meshes in glTF axes, node transforms applied (LOD nodes `*_LOD1..` skipped)."""
    if model in _mesh_cache:
        return _mesh_cache[model]
    path = ROOT / "assets_source" / model
    data = path.read_bytes()
    length = int.from_bytes(data[12:16], "little")
    doc = json.loads(data[20:20 + length])
    binary = data[20 + length + 8:]

    def accessor(index):
        a = doc["accessors"][index]
        view = doc["bufferViews"][a["bufferView"]]
        start = view.get("byteOffset", 0) + a.get("byteOffset", 0)
        width = {"SCALAR": 1, "VEC3": 3}[a["type"]]
        dtype = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a["componentType"]]
        size = np.dtype(dtype).itemsize * width
        stride = view.get("byteStride", size)
        raw = np.frombuffer(binary, np.uint8, count=stride * (a["count"] - 1) + size, offset=start)
        rows = np.lib.stride_tricks.as_strided(raw, (a["count"], size), (stride, 1)).copy()
        return rows.view(dtype).reshape(a["count"], width)

    points, triangles = [], []
    scene = doc["scenes"][doc.get("scene", 0)]

    def walk(index, parent):
        node = doc["nodes"][index]
        world = parent @ _node_matrix(node)
        name = str(node.get("name", ""))
        if "mesh" in node and "_lod" not in name.lower():
            for primitive in doc["meshes"][node["mesh"]]["primitives"]:
                p = accessor(primitive["attributes"]["POSITION"]).astype(float)
                p = p @ world[:3, :3].T + world[:3, 3]
                base = sum(len(x) for x in points)
                if "indices" in primitive:
                    t = accessor(primitive["indices"]).reshape(-1, 3).astype(int)
                else:
                    t = np.arange(len(p)).reshape(-1, 3)
                points.append(p)
                triangles.append(t + base)
        for child in node.get("children", []):
            walk(child, world)

    for index in scene["nodes"]:
        walk(index, np.eye(4))
    _mesh_cache[model] = (np.concatenate(points), np.concatenate(triangles))
    return _mesh_cache[model]

def decoration_mesh(binding: dict, yaw: float):
    """(points, triangles): a decoration's GLB (all LOD0 meshes) placed as the engine places it at the origin: glTF
    (x, y, z) -> native (-x, z, y), scaled to the binding height (the bounds' height), turned by yaw degrees, lifted
    by the binding's z_offset."""
    points, triangles = glb_mesh(binding["model"])
    scale = float(binding["height"]) / max(float(np.ptp(points[:, 1])), 1e-6)
    native = np.stack([-points[:, 0], points[:, 2], points[:, 1]], 1) * scale
    native = native @ _rotation(yaw).T + np.array([0.0, 0.0, float(binding.get("z_offset", 0))])
    return native, triangles


def up_triangles(points: np.ndarray, triangles: np.ndarray) -> np.ndarray:
    """The triangles of a placed mesh facing up (normal z over 0.7): the surfaces things rest on."""
    t = points[triangles]
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    length = np.linalg.norm(n, axis=1)
    keep = length > 1e-9
    keep[keep] = n[keep, 2] / length[keep] > 0.7
    return t[keep]


def surface_heights(tris: np.ndarray, xy: np.ndarray, z_max: float) -> np.ndarray:
    """Per plan point the highest point of the triangles over it at or below z_max (nan where none)."""
    best = np.full(len(xy), np.nan)
    if not len(tris):
        return best
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    for i, (x, y) in enumerate(xy):
        d0 = (b[:, 0] - a[:, 0]) * (y - a[:, 1]) - (b[:, 1] - a[:, 1]) * (x - a[:, 0])
        d1 = (c[:, 0] - b[:, 0]) * (y - b[:, 1]) - (c[:, 1] - b[:, 1]) * (x - b[:, 0])
        d2 = (a[:, 0] - c[:, 0]) * (y - c[:, 1]) - (a[:, 1] - c[:, 1]) * (x - c[:, 0])
        inside = ((d0 >= -1e-6) & (d1 >= -1e-6) & (d2 >= -1e-6)) | ((d0 <= 1e-6) & (d1 <= 1e-6) & (d2 <= 1e-6))
        t = tris[inside]
        if not len(t):
            continue
        n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        t, n = t[np.abs(n[:, 2]) > 1e-9], n[np.abs(n[:, 2]) > 1e-9]
        z = t[:, 0, 2] - (n[:, 0] * (x - t[:, 0, 0]) + n[:, 1] * (y - t[:, 0, 1])) / n[:, 2]
        z = z[z <= z_max]
        if len(z):
            best[i] = z.max()
    return best


def footprint(points: np.ndarray) -> np.ndarray:
    """Plan samples under a placed mesh's lowest part: its vertices within 2 units of its bottom (at most 24), drawn
    in a fifth towards their centre (a lip over its support's edge does not hold it up), and that centre. Only the
    lowest part: a seated figure rests on its feet in front of the bench, not on the bench under its middle."""
    low = points[points[:, 2] <= points[:, 2].min() + 2.0][:, :2]
    if len(low) > 24:
        low = low[np.linspace(0, len(low) - 1, 24).astype(int)]
    centre = (low.min(0) + low.max(0)) / 2
    return np.vstack([centre + (low - centre) * 0.8, centre])


def move_to_floor(items: list[dict], floor_at) -> dict:
    """LithTech's MoveToFloor for the decorations of a map: each MoveToFloor item drops from its DAT height until its
    base rests on the first surface under its footprint, the map's floors (floor_at(x, y, z_max) -> native height or
    None) or the top of a decoration placed before it. Items: {key, points (native, placed at the origin), triangles,
    position (native x, y, z), move_to_floor, dat_z}. The other decorations stay where they are and are supports from
    the start; the dropped ones drop lowest dat_z first (then by key) and are supports for the ones above. Sets each
    dropped item's `stood` (it found a surface). Returns key -> the new position z of each dropped item that found a
    surface."""
    surfaces = []
    for item in items:
        if not item["move_to_floor"]:
            placed = item["points"] + np.asarray(item["position"], float)
            surfaces.append(up_triangles(placed, item["triangles"]))
    dropped = {}
    for item in sorted((i for i in items if i["move_to_floor"]), key=lambda i: (i["dat_z"], i["key"])):
        x, y = float(item["position"][0]), float(item["position"][1])
        local = item["points"]
        samples = footprint(local) + np.array([x, y])
        top = float(item["dat_z"]) + 1.0
        lo, hi = samples.min(0) - 1.0, samples.max(0) + 1.0
        near = [t for t in surfaces if len(t) and np.all(t.max((0, 1))[:2] >= lo) and np.all(t.min((0, 1))[:2] <= hi)]
        heights = surface_heights(np.concatenate(near), samples, top) if near else np.full(len(samples), np.nan)
        for k, (sx, sy) in enumerate(samples):
            floor = floor_at(float(sx), float(sy), top)
            if floor is not None and not (heights[k] >= floor):
                heights[k] = floor
        item["stood"] = bool(np.isfinite(heights).any())
        if item["stood"]:
            z = float(np.nanmax(heights)) - float(local[:, 2].min())
            dropped[item["key"]] = z
            item["position"] = (x, y, z)
        surfaces.append(up_triangles(local + np.asarray(item["position"], float), item["triangles"]))
    return dropped
