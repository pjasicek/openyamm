#!/usr/bin/env python3
"""Writes level_generation/projects/mm9r_thjorgardcity/props.json: every Prop, CandleProp, Torch, DestructableProp,
Clover and WellMMIX placement of Thjorgard City in the native frame (the old bmodel_world map's frame, which the BLV
keeps: no offset), each under its DAT object name (source_name; the map project attaches click events by it), with its
script and script parameters, and checks each end to end as Sturmford City's placements do: the finished GLB's LOD0
(without flame cards), placed the way the engine places a decoration model (glTF (x, y, z) -> OpenYAMM (-x, z, y),
scaled by binding height / bounds height, turned by the facing, at the entity position), against the old map's baked
BModel of the same object (MM9_*_<object index>_*); median vertex distance printed. Reused decorations are checked with
their owning project's raw GLB, meta and installed model.

Positions are the asset origin (base centre) of the old bake, which includes the transcoder's floor drop for
MoveToFloor objects. A model is centred on its bake's box where that lowers the median (Klusos House's rule), across
only for the HidePiece variants (the bake keeps their hidden pieces). Posed
models (props_table.POSES: the BedMedium beds in MM9's EW pose; PLACE_POSES: Tasar Academy's pickaxes `onside`; the old
import baked their bind pose) are placed on MM9's own pose at the DAT position (ABC skinned at the animation's first
key); with MoveToFloor their base stands on the floor under them, else at the DAT position; fit_pose_units is their
fit to that pose. The object the old import did not bake (BookKey) stands by the transcoder's rule, on the floor under
it (MoveToFloor). Kinds: prop (Prop, DestructableProp, Clover, WellMMIX), torch (CandleProp and Torch: each names the
nearest DAT Light, `light`; `blue` for a CandleProp with Blue 1). A DAT name that repeats or is a decoration's name
gets _<object index> (dat_name keeps the DAT's).
Usage: placements.py [--verbose] [--preview: write work/props_preview.json instead]"""
import json
import math
import struct
import sys
from collections import Counter

import numpy as np
from scipy.spatial import cKDTree

import props_table

sys.path.insert(0, str(props_table.ISLE / 'scripts'))
from glbio import array, read_glb, world_positions  # noqa: E402

REPO = props_table.REPO
PROJECT = props_table.PROJECT
CLASS_KIND = {'Prop': 'prop', 'CandleProp': 'torch', 'Torch': 'torch', 'DestructableProp': 'prop', 'Clover': 'prop',
              'WellMMIX': 'prop'}
QUEST = set()
NPC = set()
STAND_IN = {}
LIT = {'Torch', 'CandleProp'}
LIGHT_MAX = 400.0          # units: a lamp's or torch's own MM9 Light stands near it


def rot(yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def tilt_oy(local, pitch, roll):
    """The transcoder's object pitch (about x) then roll (about y), in OpenYAMM-local axes (the isle's placements)."""
    cx, sx, cy, sy = math.cos(pitch), math.sin(pitch), math.cos(roll), math.sin(roll)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ryy = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    return local @ (ryy @ rx).T


def load_map():
    sys.path.insert(0, str(REPO))
    from util.map_export import parse_odm_file
    return parse_odm_file(props_table.ODM)['payload']['bmodels']


class WorldTriangles:
    """The world geometry's triangles (not the MM9_ props, chests, pickups: Verhoffin's placements) in plan cells, for
    the floor and wall lookups. Testing every face in Python took 1.3 s a lookup (Thjorgard City: 167 795 faces, the
    placements 22 minutes); the cells narrow a lookup to the triangles over its point, tested together."""
    CELL = 256.0
    PAD = 8.0       # units: a triangle is filed under every cell its plan box, grown by this, overlaps

    def __init__(self, bmodels):
        corners = []
        for b in bmodels:
            if b['name'].startswith('MM9_'):
                continue
            verts = np.array([[a['x'], a['y'], a['z']] for a in b['vertices']], float)
            for f in b['faces']:
                poly = verts[f['vertex_indices'][:f['vertex_count']]]
                for k in range(1, len(poly) - 1):
                    corners.append((poly[0], poly[k], poly[k + 1]))
        self.a, self.b, self.c = (np.array([t[i] for t in corners]) for i in range(3))
        self.n = np.cross(self.b - self.a, self.c - self.a)
        low = np.floor((np.minimum(np.minimum(self.a, self.b), self.c)[:, :2] - self.PAD) / self.CELL).astype(int)
        high = np.floor((np.maximum(np.maximum(self.a, self.b), self.c)[:, :2] + self.PAD) / self.CELL).astype(int)
        cells = {}
        for index in range(len(self.a)):
            for cx in range(low[index, 0], high[index, 0] + 1):
                for cy in range(low[index, 1], high[index, 1] + 1):
                    cells.setdefault((cx, cy), []).append(index)
        self.cells = {key: np.array(value) for key, value in cells.items()}

    def near(self, point):
        return self.cells.get((int(np.floor(point[0] / self.CELL)), int(np.floor(point[1] / self.CELL))),
                              np.zeros(0, int))


_world = {}


def world_triangles(bmodels):
    if id(bmodels) not in _world:
        _world[id(bmodels)] = WorldTriangles(bmodels)
    return _world[id(bmodels)]


def floor_below(bmodels, point):
    """Highest upward face of the world geometry (not the MM9_ props, chests, pickups) under point, at or below it + 8
    (Verhoffin's placements)."""
    world = world_triangles(bmodels)
    index = world.near(point)
    a, b, c, n = world.a[index], world.b[index], world.c[index], world.n[index]
    length = np.linalg.norm(n, axis=1)
    up = (np.abs(n[:, 2]) >= 1e-6) & (n[:, 2] >= 0.7 * length)

    def side(p, q):
        return ((q[:, 0] - p[:, 0]) * (point[1] - p[:, 1]) - (q[:, 1] - p[:, 1]) * (point[0] - p[:, 0])) * n[:, 2]

    inside = (side(a, b) >= 0) & (side(b, c) >= 0) & (side(c, a) >= 0)
    keep = up & inside
    if not keep.any():
        return None
    a, n = a[keep], n[keep]
    z = a[:, 2] - (n[:, 0] * (point[0] - a[:, 0]) + n[:, 1] * (point[1] - a[:, 1])) / n[:, 2]
    z = z[z <= point[2] + 8]
    return float(z.max()) if len(z) else None


WALL_HUNG_REACH = 8.0       # units: a MoveToFloor prop this near a wall, well over its floor, hangs on the wall
WALL_HUNG_HEIGHT = 24.0


def wall_distance(bmodels, point, reach):
    """Distance from point to the nearest wall (a steep face of the world geometry, not the MM9_ props) within reach,
    else None."""
    world = world_triangles(bmodels)
    if reach > WorldTriangles.PAD:
        raise ValueError(f'wall reach {reach} is over the cells\' pad {WorldTriangles.PAD}')
    index = world.near(point)
    a, b, c, n = world.a[index], world.b[index], world.c[index], world.n[index]
    length = np.linalg.norm(n, axis=1)
    steep = (length >= 1e-6) & (np.abs(n[:, 2]) <= 0.3 * np.maximum(length, 1e-12))
    a, b, c, n = a[steep], b[steep], c[steep], n[steep] / length[steep, None]
    depth = np.einsum('ij,ij->i', n, point - a)
    near = np.abs(depth) <= reach
    a, b, c, n, depth = a[near], b[near], c[near], n[near], depth[near]
    q = point - depth[:, None] * n

    def side(p, r):
        return np.einsum('ij,ij->i', np.cross(r - p, q - p), n)

    inside = (side(a, b) >= -1e-6) & (side(b, c) >= -1e-6) & (side(c, a) >= -1e-6)
    return float(np.abs(depth[inside]).min()) if inside.any() else None


def glb_lod0(path):
    """LOD0 vertex positions of a finished GLB without its flame cards (material 'Fire': not in the bake)."""
    document, binary = read_glb(path)
    node = next(n for n in document['nodes'] if 'mesh' in n)
    primitives = document['meshes'][node['mesh']]['primitives']
    solid = [p for p in primitives if document['materials'][p['material']]['name'] != 'Fire']
    full = np.concatenate([array(document, binary, p['attributes']['POSITION']) for p in primitives])
    return full, np.concatenate([array(document, binary, p['attributes']['POSITION']) for p in solid])


def finished_glb(prop):
    if prop in props_table.REUSED:
        return REPO / f'assets_source/worlds/mm9/models/mm9_deco_{prop}.glb'
    return props_table.HERE / f'work/mm9_deco_{prop}.glb'


def raw_glb(prop):
    """The raw converter GLB, build meta and binding origin of a prop, from the project that built it."""
    home = props_table.home(prop)
    origins = json.loads((home / 'work/binding_origins.json').read_text())
    origin = origins[prop] if prop in origins else origins[props_table.source_prop(prop)]
    return home / f'work/raw/{prop}/{prop}.glb', json.loads((home / f'work/{prop}_meta.json').read_text()), origin


def quaternion_matrix(t):
    x, y, z, w = t.rotation
    m = np.eye(4)
    m[:3, :3] = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                 [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                 [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    m[:3, 3] = t.translation
    return m


def posed_points(prop):
    """LOD0 vertices of a POSES prop in its animation pose at its first key (LT model space): each vertex skinned by
    its node weights (global pose x inverse global bind), Lindisfarne's bell check."""
    sys.path.insert(0, str(REPO / 'tools/mm9_import_discovery'))
    from convert_abc_model import read_abc, source_animation_pose
    model = read_abc(props_table.resolve(props_table.source(prop)[0]))
    name, _ = pose_of(prop)
    animations = model.animations
    if prop in props_table.LIBRARY:
        animations = read_abc(props_table.resolve(props_table.EXTRACTED / 'MODELS/MODELS' /
                                                  props_table.LIBRARY[prop][0])).animations
    animation = next(a for a in animations if a.name.lower() == name.lower())
    pose = source_animation_pose(model, animation, 0.0)
    parents = {c: i for i, n in enumerate(model.nodes) for c in n.children}
    world = []
    for i in range(len(model.nodes)):
        local = quaternion_matrix(pose[i])
        world.append(local if i not in parents else world[parents[i]] @ local)
    skin = [w @ np.linalg.inv(n.bind_matrix) for w, n in zip(world, model.nodes)]
    out = []
    for piece in model.pieces:
        for v in piece.lods[0].vertices:
            q = sum(w.bias * (skin[w.node_index] @ np.append(v.position, 1.0)) for w in v.weights)
            out.append(q[:3])
    return np.array(out)


FIRST_POSE_DEVIATION = 2.0      # units: a model whose first animation's pose moves a vertex further is drawn posed
_first_pose_cache = {}


def first_pose_points(prop):
    """(bind, posed) LOD0 vertices (LT model space) of the prop's model in its first animation at its first key, as MM9
    draws a Static_Model prop; (bind, None) when the model has no animation."""
    if prop in _first_pose_cache:
        return _first_pose_cache[prop]
    sys.path.insert(0, str(REPO / 'tools/mm9_import_discovery'))
    from convert_abc_model import read_abc, source_animation_pose
    model = read_abc(props_table.resolve(props_table.source(prop)[0]))
    bind = np.array([v.position for piece in model.pieces for v in piece.lods[0].vertices], float)
    if not model.animations:
        _first_pose_cache[prop] = (bind, None)
        return _first_pose_cache[prop]
    pose = source_animation_pose(model, model.animations[0], 0.0)
    parents = {c: i for i, n in enumerate(model.nodes) for c in n.children}
    world = []
    for i in range(len(model.nodes)):
        local = quaternion_matrix(pose[i])
        world.append(local if i not in parents else world[parents[i]] @ local)
    skin = [w @ np.linalg.inv(n.bind_matrix) for w, n in zip(world, model.nodes)]
    posed = np.array([sum(w.bias * (skin[w.node_index] @ np.append(v.position, 1.0)) for w in v.weights)[:3]
                      for piece in model.pieces for v in piece.lods[0].vertices])
    _first_pose_cache[prop] = (bind, posed)
    return _first_pose_cache[prop]


def pose_turn(prop, placed, position, s, ry, pos_old, origin):
    """The quarter turn MM9's first animation pose gives a model whose GLB is its bind mesh (the `*NS` props: their
    pose turns the mesh 90 degrees about the vertical; 2026-11-01, Thjorgard's library bookcases stood through its
    wall). The placed vertices are tried at 0, 90, 180 and 270 degrees more about the placement's vertical, each
    centred on MM9's posed mesh at the DAT position; the best is kept when it fits that mesh clearly better.
    Returns (degrees, shift, fit before, fit after)."""
    bind, posed = first_pose_points(prop)
    if posed is None or np.abs(posed - bind).max() * 2.56 <= FIRST_POSE_DEVIATION:
        return 0, np.zeros(3), None, None
    q = posed * 2.56 + np.array(origin) * 2.56
    expected = (np.stack([q[:, 0], q[:, 2], q[:, 1]], 1) * s) @ rot(-ry).T + pos_old
    tree = cKDTree(expected[:, :2])
    results = []
    for degrees in (0, 90, 180, 270):
        turned = (placed - position) @ rot(math.radians(degrees)).T + position
        shift = np.zeros(3)
        shift[:2] = (expected[:, :2].min(0) + expected[:, :2].max(0)) / 2 \
            - (turned[:, :2].min(0) + turned[:, :2].max(0)) / 2
        if degrees == 0:
            shift[:] = 0.0
        results.append((float(np.median(tree.query((turned + shift)[:, :2])[0])), degrees, shift))
    before = results[0][0]
    after, degrees, shift = min(results, key=lambda r: r[0])
    if degrees == 0 or after > 0.6 * before:
        return 0, np.zeros(3), round(before, 2), None
    return degrees, shift, round(before, 2), round(after, 2)


def pose_of(prop):
    return props_table.POSES.get(prop) or props_table.PLACE_POSES.get(prop) or props_table.CHECK_POSES[prop]


def light_list(raw):
    """The DAT Light objects (the map agent's request: each torch names its nearest DAT Light; the map project's
    work/lights.json is being written at the same time, so it is not read)."""
    out = []
    for o in raw.values():
        p = o['props']
        if o['class'] == 'Light':
            out.append({'name': p['Name'], 'position': [p['Pos'][0] * 2.56, p['Pos'][2] * 2.56, p['Pos'][1] * 2.56],
                        'radius': int(round(float(p.get('LightRadius', 0)) * 2.56)),
                        'colour': [int(v) for v in p.get('LightColor', [255, 255, 255])]})
    return out, 'DAT Light objects'


def main():
    bmodels = load_map()
    baked = {b['name']: np.array([[a['x'], a['y'], a['z']] for a in b['vertices']], float) for b in bmodels}
    plan = json.loads((props_table.HERE / 'work/decorations_plan.json').read_text())
    raw = {o['index']: o for o in props_table.objects()}
    lights, light_source = light_list(raw)
    light_points = np.array([light['position'] for light in lights], float)
    entries, report, unchecked = [], [], []
    for idx, prop in props_table.placements():
        o = raw[idx]
        p = o['props']
        s = float(p.get('Scale', 1.0))
        ry = float(p['Rotation'][1])
        pos_old = np.array([p['Pos'][0], p['Pos'][2], p['Pos'][1]]) * 2.56
        raw_path, meta, origin = raw_glb(prop)
        variant = next(d for d in plan if d['prop'] == prop and abs(d['scale'] - s) < 1e-3)
        # a HidePiece variant's unstripped export (the old bake has its hidden pieces) for the bake offset
        full_path = raw_path.with_name(raw_path.stem + '_full.glb')
        g = world_positions(full_path if full_path.exists() else raw_path) + np.array(origin) * 2.56
        local = np.stack([g[:, 0], g[:, 2], g[:, 1]], 1)
        if prop in props_table.TILTS:
            local = tilt_oy(local, *props_table.TILTS[prop])
        inst = (local * s) @ rot(-ry).T + pos_old
        bake = next((v for k, v in baked.items() if k.startswith('MM9_') and f'_{idx}_' in k), None)
        posed = prop in props_table.POSES or prop in props_table.PLACE_POSES
        extra = np.zeros(3) if bake is None or posed else \
            (bake.min(0) + bake.max(0)) / 2 - (inst.min(0) + inst.max(0)) / 2
        position = pos_old + extra + rot(-ry) @ (np.array(meta['origin_local_units']) * s)
        full, a = glb_lod0(finished_glb(prop))
        engine_scale = variant['height'] / (full[:, 1].max() - full[:, 1].min())
        placed = np.stack([-a[:, 0], a[:, 2], a[:, 1]], 1) * engine_scale @ rot(-ry).T + position
        fit, worst, pose_fit, note = None, None, None, ''
        turn = 0
        if posed:
            # MM9's pose at the DAT position (the model origin at Pos: the seated men's feet then reach the floor; with
            # the binding origin added they would stand 15 LT into it); MoveToFloor ones with their base on the floor
            # under them, the others at their pose's height, lifted to the floor if their feet go through it
            q = posed_points(prop) * 2.56
            expected = (np.stack([q[:, 0], q[:, 2], q[:, 1]], 1) * s) @ rot(-ry).T + pos_old
            floor = floor_below(bmodels, pos_old + np.array([0, 0, 40]))
            base = floor if p.get('MoveToFloor') or (floor is not None and expected[:, 2].min() < floor) \
                else expected[:, 2].min()
            expected[:, 2] += base - expected[:, 2].min()
            shift = (expected.min(0) + expected.max(0)) / 2 - (placed.min(0) + placed.max(0)) / 2
            shift[2] = base - placed[:, 2].min()
            position, placed = position + shift, placed + shift
            pose_fit = round(float(np.median(cKDTree(expected).query(placed)[0])), 2)
            base_delta = None if bake is None else round(float(placed[:, 2].min() - bake[:, 2].min()), 1)
            note = (f" (posed: base {'on the floor' if base == floor else 'by its pose at the DAT position'} at "
                    f"{placed[:, 2].min():.1f}, DAT z {pos_old[2]:.1f}; fit to its "
                    f"{pose_of(prop)[0]} pose {pose_fit}; base - old bake base {base_delta})")
        elif bake is None and p.get('MoveToFloor'):
            # not baked (the treasure bags): the transcoder's rule, base on the floor under the DAT position
            floor = floor_below(bmodels, pos_old + np.array([0, 0, 8]))
            if floor is not None:
                position[2] += floor - placed[:, 2].min()
                placed[:, 2] += floor - placed[:, 2].min()
                note = f' (not baked: base on the floor at {floor:.1f}, DAT z {pos_old[2]:.1f})'
        elif prop in props_table.LAID_FLAT.values() and props_table.tilt_degrees(p) == (0, 0) and bake is not None:
            # laid flat (props_table.LAID_FLAT): at the upright bake's centre, base on its base (Thronheim's route)
            shift = (bake.min(0) + bake.max(0)) / 2 - (placed.min(0) + placed.max(0)) / 2
            shift[2] = bake[:, 2].min() - placed[:, 2].min()
            position, placed = position + shift, placed + shift
            note += f' (laid flat: base on the old bake\'s base {bake[:, 2].min():.1f}, DAT z {pos_old[2]:.1f})'
        elif bake is not None:
            tree = cKDTree(bake)
            shift = (bake.min(0) + bake.max(0)) / 2 - (placed.min(0) + placed.max(0)) / 2
            # a HidePiece variant only across: the old bake keeps the hidden pieces, so its box is taller than the
            # model's (centring in height lifted the Group2 rack 11 units off the floor)
            if prop in props_table.HIDDEN:
                shift[2] = 0.0
            if np.median(tree.query(placed + shift)[0]) < np.median(tree.query(placed)[0]):
                position, placed = position + shift, placed + shift
            d, _ = tree.query(placed)
            fit, worst = round(float(np.median(d)), 2), float(d.max())
            turn, turn_shift, turn_before, turn_after = pose_turn(prop, placed, position, s, ry, pos_old, origin)
            if turn:
                placed = (placed - position) @ rot(math.radians(turn)).T + position + turn_shift
                position = position + turn_shift
                note += f' (turned {turn} to its first pose: fit to the pose {turn_before} -> {turn_after})'
            if prop in props_table.CHECK_POSES:
                q = posed_points(prop) * 2.56 + np.array(origin) * 2.56
                expected = (np.stack([q[:, 0], q[:, 2], q[:, 1]], 1) * s) @ rot(-ry).T + pos_old
                pose_fit = round(float(np.median(cKDTree(expected).query(placed)[0])), 2)
        if not posed:
            # On the floor (2026-11-01). The floor under the DAT position: a prop that MM9 sets down on it (MoveToFloor)
            # stands there when the old bake dropped it through to a lower floor (Logs7: an upper fireplace's logs in
            # the one below); a prop whose DAT position is on a floor (MoveToFloor 0: MM9's Pos is its base, the ABC
            # origin mid-height; the old bake sank beds, cabinets and dressers half their height) stands on it.
            floor = floor_below(bmodels, pos_old + np.array([0, 0, 4]))
            base = float(placed[:, 2].min())
            lift = None
            # A MoveToFloor prop at a wall, well over the floor (a notice pinned beside a door, 2026-11-02): MM9's
            # designer hung it there; the old bake dropped it to the floor. It stays at its DAT height.
            wall = None if not p.get('MoveToFloor') or floor is None or pos_old[2] - floor < WALL_HUNG_HEIGHT \
                else wall_distance(bmodels, pos_old, WALL_HUNG_REACH)
            if wall is not None:
                hang = (inst[:, 2].min() + inst[:, 2].max()) / 2 - (placed[:, 2].min() + placed[:, 2].max()) / 2
                position[2] += hang
                placed[:, 2] += hang
                note += f' (hung on the wall {wall:.1f} away at its DAT height: raised {hang:.1f})'
            elif floor is not None and p.get('MoveToFloor') and floor - base > 0.5:
                lift = floor - base
            elif floor is not None and not p.get('MoveToFloor') and -4.0 <= pos_old[2] - floor <= 12.0 \
                    and base < floor - 0.5:
                lift = floor - base
            if lift is not None:
                position[2] += lift
                placed[:, 2] += lift
                note += f' (on the floor at {floor:.1f}: lifted {lift:.1f})'
            entry_floor_lift = None if lift is None else round(float(lift), 1)
            entry_wall_hung = None if wall is None else round(float(hang), 1)
        else:
            entry_floor_lift = None
            entry_wall_hung = None
        entry = {'source_object': idx, 'source_name': p['Name'], 'class': o['class'],
                 'kind': 'quest' if p['Name'] in QUEST else 'npc' if p['Name'] in NPC else CLASS_KIND[o['class']],
                 'source_model': p['Filename'], 'source_skin': p.get('Skin'), 'prop': prop,
                 'decoration': variant['decoration'], 'x': round(float(position[0]), 1),
                 'y': round(float(position[1]), 1), 'z': round(float(position[2]), 1),
                 'yaw_degrees': round((math.degrees(-ry) + turn) % 360.0, 2), 'fit_median_units': fit,
                 'script': p.get('ScriptName') or None, 'script_params': p.get('ScriptParams') or None}
        if turn:
            entry['pose_turn_degrees'] = turn
        if entry_floor_lift is not None:
            entry['floor_lift'] = entry_floor_lift
        if entry_wall_hung is not None:
            entry['wall_hung_raise'] = entry_wall_hung
        if prop in props_table.TILTS:
            entry['tilt_degrees'] = [round(math.degrees(v), 1) for v in props_table.TILTS[prop]]
        if prop in props_table.CHECK_POSES:
            entry['pose'] = pose_of(prop)[0]
            entry['fit_pose_units'] = pose_fit
        if posed:
            entry['pose'] = pose_of(prop)[0]
            entry['fit_pose_units'] = pose_fit
            entry['floor_z'] = None if floor is None else round(float(floor), 1)
            entry['bake_base_delta'] = base_delta
        if entry['kind'] == 'npc':
            # RUDENPCId is a float stored as its bits (as the Arena's NPCNbr): 1113849856 -> 57
            raw_id = p.get('RUDENPCId')
            value = struct.unpack('<f', struct.pack('<I', raw_id))[0] if isinstance(raw_id, int) else None
            entry['rude_npc_id'] = int(value) if value is not None and value.is_integer() else None
        if p['Name'] in STAND_IN:
            entry['stand_in'] = STAND_IN[p['Name']]
        if o['class'] == 'CandleProp' and p.get('Blue'):
            entry['blue'] = True
        if o['class'] in LIT:
            distance = np.linalg.norm(light_points - pos_old, axis=1)
            nearest = int(distance.argmin())
            entry['light'] = {'name': lights[nearest]['name'], 'distance': round(float(distance[nearest])),
                              'radius': lights[nearest]['radius'], 'colour': lights[nearest]['colour']}
            if distance[nearest] > LIGHT_MAX:
                # MM9 places no Light by Brazier1 and Brazier10 (no DAT Light within 300 LT): name none
                entry['light_note'] = (f"no MM9 Light of its own (nearest DAT Light {entry['light']['name']} "
                                       f"{entry['light']['distance']} units away)")
                entry['light'] = None
        entries.append(entry)
        if fit is None:
            unchecked.append(f"{idx} {p['Name']} {prop}{note}")
        else:
            report.append(f"{idx} {p['Name']} {prop}: fit median {fit}, worst vertex {round(worst, 1)}"
                          f"{'' if pose_fit is None else f' (fit to its {pose_of(prop)[0]} pose {pose_fit})'}")
    # source_name is the DAT name (the map agent's request, 2026-10-31); this map repeats none. Should one repeat, the
    # converter's one DECOR_<name> node per name would be shared: later repeats would get _<object index>.
    seen = set()
    for entry in entries:
        if entry['source_name'] in seen:
            if entry['script']:
                sys.exit(f"{entry['source_name']}: a scripted object's name repeats")
            entry['dat_name'] = entry['source_name']
            entry['source_name'] = f"{entry['source_name']}_{entry['source_object']}"
            report.append(f"renamed repeated DAT name {entry['dat_name']} -> {entry['source_name']}")
        seen.add(entry['source_name'])
    # A DAT name that is also a decoration's name would resolve as that decoration (the converter refuses it,
    # DUNGEON_PLAYBOOK "Entity names"; the Yanmir lesson): it gets _<object index> too.
    decoration_names = set()
    for table in (REPO / 'assets_dev/engine/data_tables/decoration_data.txt',
                  REPO / 'assets_dev/worlds/mm9/data_tables/decoration_data.txt'):
        for line in table.read_text(encoding='latin-1').splitlines():
            cells = line.split('\t')
            if len(cells) > 1 and cells[0].strip().isdigit():
                decoration_names.add(cells[1].strip().lower())
    for entry in entries:
        if entry['source_name'].lower() in decoration_names:
            entry.setdefault('dat_name', entry['source_name'])
            entry['source_name'] = f"{entry['source_name']}_{entry['source_object']}"
            report.append(f"renamed DAT name {entry['dat_name']} (a decoration's name) -> {entry['source_name']}")
    out = props_table.HERE / 'work/props_preview.json' if '--preview' in sys.argv else PROJECT / 'props.json'
    out.write_text(json.dumps(entries, indent=1) + '\n')
    checked = [e for e in entries if e['fit_median_units'] is not None]
    fits = np.array([e['fit_median_units'] for e in checked])
    if '--verbose' in sys.argv:
        print('\n'.join(report))
    print('WROTE', out, len(entries), 'entries', dict(Counter(e['kind'] for e in entries)), '; checked', len(checked),
          'fit median of medians', round(float(np.median(fits)), 2), 'worst', round(float(fits.max()), 2))
    for e in sorted(checked, key=lambda e: -e['fit_median_units'])[:10]:
        print('  ', e['source_object'], e['source_name'], e['prop'], e['fit_median_units'])
    for prop in sorted({e['prop'] for e in entries}):
        f = [e['fit_median_units'] for e in entries if e['prop'] == prop and e['fit_median_units'] is not None]
        print(f'   {prop}: {len(f)} checked, fit median {round(float(np.median(f)), 2) if f else None}'
              f"{'' if not f else f', worst {max(f)}'}")
    print('not checked against a bake:\n  ' + '\n  '.join(unchecked))
    lit = [e['light']['distance'] for e in entries if e.get('light')]
    names = [e['light']['name'] for e in entries if e.get('light')]
    print('without a light of their own:', [e['source_name'] for e in entries if 'light' in e and not e['light']])
    print('lights (' + light_source + '): distance', min(lit), '-', max(lit), 'units;', len(set(names)), 'distinct of',
          len(names))


if __name__ == '__main__':
    main()
