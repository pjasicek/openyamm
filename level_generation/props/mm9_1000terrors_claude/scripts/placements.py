#!/usr/bin/env python3
"""Writes level_generation/projects/mm9r_1000terrors/props.json: every Prop, Torch, Brazier, CandleProp and TreasureChest
placement of the Thousand Terrors in the native frame (the old bmodel_world map's frame, which the BLV keeps: no
offset), and checks each end to end as Lindisfarne Monastery's placements do: the finished GLB's LOD0, placed the way
the engine places a decoration model (glTF (x, y, z) -> OpenYAMM (-x, z, y), scaled by binding height / bounds height,
turned by the facing, at the entity position), against the old map's baked BModel of the same object
(MM9_static_prop_<object>_<name>, matched by object index: BModel names stop at 32 characters); median vertex distance
printed. Reused decorations are checked with their owning project's raw GLB, meta and installed model.

Positions are the asset origin (base centre) of the old bake, which includes the transcoder's floor drop for
MoveToFloor objects. A model without flame cards is centred on its bake's box where that lowers the median (Klusos
House's rule). The raised coffins with PropAnim.scr "ns" are checked as baked (Static_Model), then turned a quarter
about their DAT origin (props_table.POSE_TURN): MM9 loops their NS animation, whose root turns the coffin a quarter
(the root TREASURECHUTENS.abc carries in its own animation; the treasurechutens check below proves the direction).
The Sorceress statues are built in fidget2's last frame (props_table.POSES); the old map baked the T-pose bind, so
their fit to the bake is reported apart from their fit to the posed points. Torches, braziers and TerrorLights name
the nearest MM9 Light (DAT Light objects; their rows carry no light). Every entry keeps its DAT name (source_name),
script and params. The objects not placed (invisible candles, LeverHand) are in work/not_placed.json.
Usage: placements.py [--verbose] [--preview: write work/props_preview.json instead]"""
import json
import math
import sys

import numpy as np
from scipy.spatial import cKDTree

import props_table

sys.path.insert(0, str(props_table.ISLE / 'scripts'))
from glbio import array, read_glb, world_positions  # noqa: E402

REPO = props_table.REPO
PROJECT = props_table.PROJECT
CLASS_KIND = {'Prop': 'prop', 'Torch': 'torch', 'CandleProp': 'torch', 'Brazier': 'brazier', 'TreasureChest': 'chest'}
QUEST = {'scrollp90'}          # ChessNote0, BootGive.scr 598: the party takes the note (giveitem 598, removeobject)
ON_TOP = {}
LIT = ('Torch', 'Brazier', 'CandleProp')


def dat_lights():
    """MM9's Light objects: name, native position, radius x 2.56, colour, BrightScale."""
    out = []
    for o in props_table.objects():
        if o['class'] != 'Light':
            continue
        p = o['props']
        out.append({'name': p['Name'], 'position': [p['Pos'][0] * 2.56, p['Pos'][2] * 2.56, p['Pos'][1] * 2.56],
                    'radius': round(float(p.get('LightRadius', 0)) * 2.56),
                    'colour': [int(c) for c in p.get('LightColor', [255, 255, 255])],
                    'bright_scale': round(float(p.get('BrightScale', 1.0)), 2)})
    return out


def rot(yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def bmodels():
    sys.path.insert(0, str(REPO))
    from util.map_export import parse_odm_file
    payload = parse_odm_file(props_table.ODM)['payload']
    return {b['name']: np.array([[a['x'], a['y'], a['z']] for a in b['vertices']], float) for b in payload['bmodels']}


def glb_lod0(path):
    document, binary = read_glb(path)
    node = next(n for n in document['nodes'] if 'mesh' in n)
    return np.concatenate([array(document, binary, p['attributes']['POSITION'])
                           for p in document['meshes'][node['mesh']]['primitives']])


def finished_glb(prop):
    if prop in props_table.REUSED:
        return REPO / f'assets_source/worlds/mm9/models/mm9_deco_{prop}.glb'
    return props_table.HERE / f'work/mm9_deco_{prop}.glb'


def raw_glb(prop):
    """The raw converter GLB, build meta and binding origin of a prop, from the project that built it."""
    home = props_table.home(prop)
    origins = json.loads((home / 'work/binding_origins.json').read_text())
    return (home / f'work/raw/{prop}/{prop}.glb', json.loads((home / f'work/{prop}_meta.json').read_text()),
            origins[props_table.source_prop(prop)] if props_table.source_prop(prop) in origins else origins[prop])


def quaternion_matrix(t):
    x, y, z, w = t.rotation
    m = np.eye(4)
    m[:3, :3] = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                 [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                 [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    m[:3, 3] = t.translation
    return m


def posed_points(prop):
    """LOD0 vertices of a POSES prop in its animation pose (LT model space, as the raw GLB's bind-pose coordinates):
    each vertex skinned by its node weights (global pose x inverse global bind)."""
    sys.path.insert(0, str(REPO / 'tools/mm9_import_discovery'))
    from convert_abc_model import read_abc, source_animation_pose
    model = read_abc(props_table.resolve(props_table.source(prop)[0]))
    name, frame = props_table.POSES[prop]
    animation = next(a for a in model.animations if a.name.lower() == name.lower())
    pose = source_animation_pose(model, animation, frame / 24.0)     # the glTF import's 24 fps
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


def pose_turn(prop, p):
    """Extra turn (LT radians about y, added to ry after the bake check) of an animated pose PropAnim.scr loops, of a
    model's first animation root (props_table.ANIM_TURN) or of a model built with that root (BUILT_TURN), else 0."""
    turn = math.radians(props_table.ANIM_TURN.get(props_table.key(p.get('Filename')), 0.0)
                        + props_table.BUILT_TURN.get(prop, 0.0))
    if 'propanim' not in (p.get('ScriptName') or '').lower():
        return turn
    return turn + math.radians(props_table.POSE_TURN.get((p.get('ScriptParams') or '').strip(), {}).get(prop, 0.0))


def water_orbs(report):
    """The 117 translucent water orbs (DAT WorldObjects, not props; scripts/build_waterorb.py): one entry each under
    its WorldObject name, kind prop, yaw 0, at its box centre's x/y with z at the box bottom (a decoration's origin is
    its base centre), checked against the DAT model's own points."""
    orbs = props_table.HERE / 'work/waterorb'
    centres = json.loads((orbs / 'centres.json').read_text())
    points = np.load(orbs / 'points_native.npz')
    a = glb_lod0(props_table.HERE / 'work/mm9_deco_waterorb.glb')
    height = 41.0
    model = np.stack([-a[:, 0], a[:, 2], a[:, 1]], 1) * height / (a[:, 1].max() - a[:, 1].min())
    out = []
    for name, c in centres.items():
        x, y, z = c['native']
        position = np.array([x, y, z - height / 2])
        d, _ = cKDTree(points[name]).query(model + position)
        fit = round(float(np.median(d)), 2)
        out.append({'source_object': None, 'source_name': name, 'class': 'WorldObject', 'kind': 'prop',
                    'source_model': None, 'source_skin': 'Sprites\\Water\\water123.spr', 'prop': 'waterorb',
                    'decoration': 'mm9_waterorb', 'x': round(float(position[0]), 1), 'y': round(float(position[1]), 1),
                    'z': round(float(position[2]), 1), 'yaw_degrees': 0.0, 'fit_median_units': fit,
                    'script': None, 'script_params': None, 'alpha': c['alpha']})
        report.append(f"{name} waterorb: fit median {fit}, worst vertex {round(float(d.max()), 1)}")
    return out


def main():
    baked = bmodels()
    plan = json.loads((props_table.HERE / 'work/decorations_plan.json').read_text())
    raw = {o['index']: o for o in props_table.objects()}
    lights = dat_lights()
    light_points = np.array([light['position'] for light in lights], float)
    entries, report, unbaked, tops = [], [], [], {}
    for idx, prop in props_table.placements():
        o = raw[idx]
        p = o['props']
        s = float(p.get('Scale', 1.0))
        ry_dat = float(p['Rotation'][1])
        # a model built with its first animation's root is checked turned back to the bind pose the old map baked
        ry = ry_dat - math.radians(props_table.BUILT_TURN.get(prop, 0.0))
        pos_old = np.array([p['Pos'][0], p['Pos'][2], p['Pos'][1]]) * 2.56
        raw_path, meta, origin = raw_glb(prop)
        variant = next(d for d in plan if d['prop'] == prop and abs(d['scale'] - s) < 1e-3)
        g = world_positions(raw_path) + np.array(origin) * 2.56
        local = np.stack([g[:, 0], g[:, 2], g[:, 1]], 1)
        inst = (local * s) @ rot(-ry_dat).T + pos_old
        bake = next((v for k, v in baked.items() if k.startswith('MM9_') and f'_{idx}_' in k), None)
        extra = np.zeros(3) if bake is None else (bake.min(0) + bake.max(0)) / 2 - (inst.min(0) + inst.max(0)) / 2
        position = pos_old + extra + rot(-ry) @ (np.array(meta['origin_local_units']) * s)
        a = glb_lod0(finished_glb(prop))
        engine_scale = variant['height'] / (a[:, 1].max() - a[:, 1].min())
        placed = np.stack([-a[:, 0], a[:, 2], a[:, 1]], 1) * engine_scale @ rot(-ry).T + position
        if meta.get('flame_head_m'):          # the flame cards are not in the bake
            placed = placed[a[:, 1] * engine_scale < (meta['flame_head_m'][2] * 81.7 * engine_scale) - 1]
        fit, worst, pose_fit = None, None, None
        if prop in props_table.POSES:
            # built in its animation pose: centre it on that pose's points, placed as the bind pose was matched to
            # the bake (the old map baked the bind pose); the fit to the bake then measures the bake's pose error
            q = posed_points(prop) * 2.56 + np.array(origin) * 2.56
            expected = (np.stack([q[:, 0], q[:, 2], q[:, 1]], 1) * s) @ rot(-ry).T + pos_old + extra
            shift = (expected.min(0) + expected.max(0)) / 2 - (placed.min(0) + placed.max(0)) / 2
            position, placed = position + shift, placed + shift
            pose_fit = round(float(np.median(cKDTree(expected).query(placed)[0])), 2)
        if bake is not None:
            tree = cKDTree(bake)
            if not meta.get('flame_head_m') and prop not in props_table.POSES:
                shift = (bake.min(0) + bake.max(0)) / 2 - (placed.min(0) + placed.max(0)) / 2
                if np.median(tree.query(placed + shift)[0]) < np.median(tree.query(placed)[0]):
                    position, placed = position + shift, placed + shift
            d, _ = tree.query(placed)
            fit, worst = round(float(np.median(d)), 2), float(d.max())
        else:
            unbaked.append(p['Name'])
        yaw = math.degrees(-ry)
        turn = pose_turn(prop, p)
        if turn:
            # the NS pose turns the model about its DAT origin: ry -> ry + turn, i.e. the placement about pos_old
            r = rot(-turn)
            position = np.array([*(r[:2, :2] @ (position[:2] - pos_old[:2]) + pos_old[:2]), position[2]])
            yaw -= math.degrees(turn)
        entry = {'source_object': idx, 'source_name': p['Name'], 'class': o['class'],
                 'kind': 'quest' if prop in QUEST else CLASS_KIND[o['class']],
                 'source_model': p['Filename'], 'source_skin': p.get('Skin'), 'prop': prop,
                 'decoration': variant['decoration'], 'x': round(float(position[0]), 1),
                 'y': round(float(position[1]), 1), 'z': round(float(position[2]), 1),
                 'yaw_degrees': round(yaw % 360.0, 2), 'fit_median_units': fit,
                 'script': p.get('ScriptName') or None, 'script_params': p.get('ScriptParams') or None}
        if pose_fit is not None:
            entry['pose'] = props_table.POSES[prop][0]
            entry['fit_pose_units'] = pose_fit
        if turn:
            entry['pose_turn_degrees'] = round(-math.degrees(turn), 1)
        if o['class'] in LIT:
            distance = np.linalg.norm(light_points - pos_old, axis=1)
            nearest = int(distance.argmin())
            entry['light'] = {'name': lights[nearest]['name'], 'distance': round(float(distance[nearest])),
                              'radius': lights[nearest]['radius'], 'colour': lights[nearest]['colour'],
                              'bright_scale': lights[nearest]['bright_scale']}
        entries.append(entry)
        tops[p['Name']] = float(placed[:, 2].max())
        report.append(f"{idx} {p['Name']} {prop}: fit median {fit}, worst vertex "
                      f"{'-' if worst is None else round(worst, 1)}"
                      f"{' turned %.0f' % -math.degrees(turn) if turn else ''}"
                      f"{'' if pose_fit is None else f' (fit to its {props_table.POSES[prop][0]} pose {pose_fit})'}")
    for entry in entries:
        if entry['source_name'] in ON_TOP:
            below = ON_TOP[entry['source_name']]
            report.append(f"{entry['source_name']}: base {entry['z']} in the bake (the floor), lifted onto {below}'s "
                          f"top "
                          f"{tops[below]:.1f}")
            entry['z'] = round(tops[below], 1)
            # the bake stands inside the pillar: its check (model and footprint, at the floor) is kept apart
            entry['fit_as_baked_units'], entry['fit_median_units'] = entry['fit_median_units'], None
    entries += water_orbs(report)
    out = props_table.HERE / 'work/props_preview.json' if '--preview' in sys.argv else PROJECT / 'props.json'
    out.write_text(json.dumps(entries, indent=1) + '\n')
    fits = np.array([e['fit_median_units'] for e in entries if e['fit_median_units'] is not None])
    if '--verbose' in sys.argv:
        print('\n'.join(report))
    print('WROTE', out, len(entries), 'entries; fit median of medians',
          round(float(np.median(fits)), 2), 'worst', round(float(fits.max()), 2), 'not baked in the old map:', unbaked)
    checked = [e for e in entries if e['fit_median_units'] is not None]
    for e in sorted(checked, key=lambda e: -e['fit_median_units'])[:10]:
        print('  ', e['source_object'], e['source_name'], e['prop'], e['fit_median_units'])
    for prop in sorted({e['prop'] for e in entries}):
        f = [e['fit_median_units'] for e in entries if e['prop'] == prop and e['fit_median_units'] is not None]
        print(f'   {prop}: {len(f)} baked, fit median {np.median(f) if f else None}')
    lit = [e['light']['distance'] for e in entries if 'light' in e]
    names = [e['light']['name'] for e in entries if 'light' in e]
    print('lights: distance', min(lit), '-', max(lit), 'units;', len(set(names)), 'distinct of', len(names))


if __name__ == '__main__':
    main()
