#!/usr/bin/env python3
"""Writes level_generation/projects/mm9r_yanmirsfort/props.json: every Prop, DestructableProp, TreasureChest and
CandleProp placement of Yanmir's Fort in the native frame (the old bmodel_world map's frame, which the BLV keeps: no
offset), each under its DAT object name (the map project attaches click events and cogs by it), and checks each end to
end as Lindisfarne Monastery's and Tasar Academy's placements do: the finished GLB's LOD0 (without its flame cards),
placed the way the engine places a decoration model (glTF (x, y, z) -> OpenYAMM (-x, z, y), scaled by binding height /
bounds height, turned by the facing, at the entity position), against the old map's baked BModel of the same object
(MM9_*_<object index>_*); median vertex distance printed. Reused decorations are checked with their owning project's
raw GLB, meta and installed model; tilted ones (the claws, the toppled chairs and stool) with their pitch and roll
applied to the raw (upright) import, as the transcoder baked them.

Positions are the asset origin (base centre) of the old bake, which includes the transcoder's floor drop for
MoveToFloor objects. A model is centred on its bake's box where that lowers the median (Klusos House's rule). The
posed props (props_table.POSES: the beds' PropAnim.scr "onside", Verhoffin's bedmedium2onside; the key's Static_Model,
which lays it flat: the Temple of Honk's key2) cannot be checked against the bake (the old import baked the bind pose):
as Verhoffin's beds, they stand with their base on the floor under their DAT position (MoveToFloor 1), centred across
on MM9's own pose (ABC skinned at the animation's first key, placed at the DAT position and turned by its facing), and
their fit to that pose (bottoms aligned) is fit_pose_units. The claws name the nearest light (the map project's
work/lights.json kept lights, else the DAT Light objects; their rows carry no light). Repeated unscripted DAT names
get _<object index> from their second occurrence (dat_name keeps the DAT's).
Usage: placements.py [--verbose] [--preview: write work/props_preview.json instead]"""
import json
import math
import sys
from collections import Counter

import numpy as np
from scipy.spatial import cKDTree

import props_table

sys.path.insert(0, str(props_table.ISLE / 'scripts'))
from glbio import array, read_glb, world_positions  # noqa: E402

REPO = props_table.REPO
PROJECT = props_table.PROJECT
CLASS_KIND = {'Prop': 'prop', 'DestructableProp': 'prop', 'TreasureChest': 'chest', 'CandleProp': 'torch'}
# YanmirKey.scr: the party takes Yanmir's key (a click and a cog to hide it; the map project wires both)
QUEST = {"Yanmir'sKey"}
LIT = {'CandleProp'}


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


def floor_below(bmodels, point):
    """Highest upward face of the world geometry (not the MM9_ props, chests, pickups) under point, at or below it + 8
    (Verhoffin's placements)."""
    best = None
    for b in bmodels:
        if b['name'].startswith('MM9_'):
            continue
        verts = np.array([[a['x'], a['y'], a['z']] for a in b['vertices']], float)
        lo, hi = verts.min(0), verts.max(0)
        if not (lo[0] - 1 <= point[0] <= hi[0] + 1 and lo[1] - 1 <= point[1] <= hi[1] + 1 and lo[2] <= point[2] + 8):
            continue
        for f in b['faces']:
            poly = verts[f['vertex_indices'][:f['vertex_count']]]
            for k in range(1, len(poly) - 1):
                a, bb, c = poly[0], poly[k], poly[k + 1]
                n = np.cross(bb - a, c - a)
                if abs(n[2]) < 1e-6 or n[2] / np.linalg.norm(n) < 0.7:
                    continue
                d0 = np.cross(bb - a, point - a)[2] * n[2]
                d1 = np.cross(c - bb, point - bb)[2] * n[2]
                d2 = np.cross(a - c, point - c)[2] * n[2]
                if min(d0, d1, d2) < 0:
                    continue
                z = a[2] - (n[0] * (point[0] - a[0]) + n[1] * (point[1] - a[1])) / n[2]
                if z <= point[2] + 8 and (best is None or z > best):
                    best = z
    return best


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
    name, _ = props_table.POSES[prop]
    animation = next(a for a in model.animations if a.name.lower() == name.lower())
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


def light_list(raw):
    """The map project's kept lights (work/lights.json), else the DAT Light objects."""
    path = PROJECT / 'work/lights.json'
    if path.exists():
        return [light for light in json.loads(path.read_text()) if light['kept']], 'lights.json'
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
        g = world_positions(raw_path) + np.array(origin) * 2.56
        local = np.stack([g[:, 0], g[:, 2], g[:, 1]], 1)
        if prop in props_table.TILTS:
            local = tilt_oy(local, *props_table.TILTS[prop])
        inst = (local * s) @ rot(-ry).T + pos_old
        bake = next((v for k, v in baked.items() if k.startswith('MM9_') and f'_{idx}_' in k), None)
        posed = prop in props_table.POSES
        extra = np.zeros(3) if bake is None or posed else \
            (bake.min(0) + bake.max(0)) / 2 - (inst.min(0) + inst.max(0)) / 2
        position = pos_old + extra + rot(-ry) @ (np.array(meta['origin_local_units']) * s)
        full, a = glb_lod0(finished_glb(prop))
        engine_scale = variant['height'] / (full[:, 1].max() - full[:, 1].min())
        placed = np.stack([-a[:, 0], a[:, 2], a[:, 1]], 1) * engine_scale @ rot(-ry).T + position
        fit, worst, pose_fit, note = None, None, None, ''
        if posed:
            # MM9's onside pose at the DAT position; the model's box centred on it across, its base on the floor
            q = posed_points(prop) * 2.56 + np.array(origin) * 2.56
            expected = (np.stack([q[:, 0], q[:, 2], q[:, 1]], 1) * s) @ rot(-ry).T + pos_old
            floor = floor_below(bmodels, pos_old + np.array([0, 0, 40]))
            expected[:, 2] += floor - expected[:, 2].min()
            shift = (expected.min(0) + expected.max(0)) / 2 - (placed.min(0) + placed.max(0)) / 2
            shift[2] = floor - placed[:, 2].min()
            position, placed = position + shift, placed + shift
            pose_fit = round(float(np.median(cKDTree(expected).query(placed)[0])), 2)
            note = (f' (posed: base on the floor at {floor:.1f}, DAT z {pos_old[2]:.1f}; fit to its '
                    f'{props_table.POSES[prop][0]} pose {pose_fit})')
        elif bake is not None:
            tree = cKDTree(bake)
            shift = (bake.min(0) + bake.max(0)) / 2 - (placed.min(0) + placed.max(0)) / 2
            if np.median(tree.query(placed + shift)[0]) < np.median(tree.query(placed)[0]):
                position, placed = position + shift, placed + shift
            d, _ = tree.query(placed)
            fit, worst = round(float(np.median(d)), 2), float(d.max())
        entry = {'source_object': idx, 'source_name': p['Name'], 'class': o['class'],
                 'kind': 'quest' if p['Name'] in QUEST else CLASS_KIND[o['class']],
                 'source_model': p['Filename'], 'source_skin': p.get('Skin'), 'prop': prop,
                 'decoration': variant['decoration'], 'x': round(float(position[0]), 1),
                 'y': round(float(position[1]), 1), 'z': round(float(position[2]), 1),
                 'yaw_degrees': round(math.degrees(-ry) % 360.0, 2), 'fit_median_units': fit,
                 'script': p.get('ScriptName') or None, 'script_params': p.get('ScriptParams') or None}
        if prop in props_table.TILTS:
            entry['tilt_degrees'] = [round(math.degrees(v), 1) for v in props_table.TILTS[prop]]
        if posed:
            entry['pose'] = props_table.POSES[prop][0]
            entry['fit_pose_units'] = pose_fit
        if o['class'] in LIT:
            distance = np.linalg.norm(light_points - pos_old, axis=1)
            nearest = int(distance.argmin())
            entry['blue'] = bool(p.get('Blue'))
            entry['light'] = {'name': lights[nearest]['name'], 'distance': round(float(distance[nearest])),
                              'radius': lights[nearest]['radius'], 'colour': lights[nearest]['colour']}
        entries.append(entry)
        if fit is None:
            unchecked.append(f"{idx} {p['Name']} {prop}{note}")
        else:
            report.append(f"{idx} {p['Name']} {prop}: fit median {fit}, worst vertex {round(worst, 1)}")
    # The DAT repeats two unscripted names (RdTable x3, Bench0 x2); the converter makes one entity and one DECOR_<name>
    # marker node per source_name, so a repeat would share the first one's node: later repeats get _<object index>.
    seen = set()
    for entry in entries:
        if entry['source_name'] in seen:
            if entry['script']:
                sys.exit(f"{entry['source_name']}: a scripted object's name repeats")
            entry['dat_name'] = entry['source_name']
            entry['source_name'] = f"{entry['source_name']}_{entry['source_object']}"
            report.append(f"renamed repeated DAT name {entry['dat_name']} -> {entry['source_name']}")
        seen.add(entry['source_name'])
    # A DAT name that is also a decoration's name ("Bucket") would resolve as that decoration (the converter refuses
    # it, DUNGEON_PLAYBOOK "Entity names"): it gets _<object index> too (map agent, 2026-10-31).
    for entry in entries:
        if entry['source_name'].lower() in ('bucket',) and not entry['script']:
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
    lit = [e['light']['distance'] for e in entries if 'light' in e]
    names = [e['light']['name'] for e in entries if 'light' in e]
    print('lights (' + light_source + '): distance', min(lit), '-', max(lit), 'units;', len(set(names)), 'distinct of',
          len(names))


if __name__ == '__main__':
    main()
