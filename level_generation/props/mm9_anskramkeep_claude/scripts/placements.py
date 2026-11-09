#!/usr/bin/env python3
"""Writes level_generation/projects/mm9r_anskramkeep/props.json: every keep prop and chest placement in the native
frame (the old bmodel_world map's frame, which the BLV keeps: no offset), and checks each end to end: the finished
GLB's LOD0, placed the way the engine places a decoration model (glTF (x, y, z) -> OpenYAMM (-x, z, y), scaled by
binding height / bounds height, turned by the facing, at the entity position), against the old map's baked BModel of
the same object (MM9_static_prop_<object>_<name>, MM9_chest_<object>_<name>); median vertex distance printed.

Positions are the asset origin (base centre) of the old bake, which includes the transcoder's floor drop for
MoveToFloor objects. Wall torches also name the BLV light MM9 placed beside each (lights.json of the map project:
the nearest kept light; the torch's own row has no light).
Usage: placements.py"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

import props_table

sys.path.insert(0, str(props_table.ISLE / 'scripts'))
from glbio import array, read_glb, world_positions  # noqa: E402

REPO = props_table.REPO
PROJECT = REPO / 'level_generation/projects/mm9r_anskramkeep'
CLASS_KIND = {'Prop': 'prop', 'WallTorch': 'torch', 'Barrel': 'barrel', 'BonePile': 'bone_pile',
              'TreasureChest': 'chest'}


def rot(yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def bmodels():
    sys.path.insert(0, str(REPO))
    from util.map_export import parse_odm_file
    payload = parse_odm_file(REPO / 'assets_editor_dev/worlds/mm9/maps/anskramkeep.odm')['payload']
    return {b['name']: np.array([[a['x'], a['y'], a['z']] for a in b['vertices']], float) for b in payload['bmodels']}


def glb_lod0(path):
    document, binary = read_glb(path)
    node = next(n for n in document['nodes'] if 'mesh' in n)
    return np.concatenate([array(document, binary, p['attributes']['POSITION'])
                           for p in document['meshes'][node['mesh']]['primitives']])


def main():
    baked = bmodels()
    plan = json.loads((props_table.HERE / 'work/decorations_plan.json').read_text())
    raw = {o['index']: o for o in props_table.objects()}
    lights = [l for l in json.loads((PROJECT / 'work/lights.json').read_text()) if l['kept']]
    light_points = np.array([l['position'] for l in lights], float)
    entries, worst = [], 0.0
    for idx, prop in props_table.placements():
        o = raw[idx]
        if o['class'] == 'PropDamager':       # the spike pits: not in the old map; the map project places them
            continue
        p = o['props']
        s = float(p.get('Scale', 1.0))
        ry = float(p['Rotation'][1])
        pos_old = np.array([p['Pos'][0], p['Pos'][2], p['Pos'][1]]) * 2.56
        meta = json.loads((props_table.HERE / f'work/{prop}_meta.json').read_text())
        variant = next(d for d in plan if d['prop'] == prop and abs(d['scale'] - s) < 1e-3)
        g = world_positions(props_table.HERE / f'work/raw/{prop}/{prop}.glb') \
            + np.array(props_table.binding_origin(prop)) * 2.56
        local = np.stack([g[:, 0], g[:, 2], g[:, 1]], 1)
        inst = (local * s) @ rot(-ry).T + pos_old
        prefix = 'MM9_chest' if o['class'] == 'TreasureChest' else 'MM9_static_prop'
        bake = baked[f"{prefix}_{idx}_{p['Name']}"]
        extra = (bake.min(0) + bake.max(0)) / 2 - (inst.min(0) + inst.max(0)) / 2
        position = pos_old + extra + rot(-ry) @ (np.array(meta['origin_local_units']) * s)
        a = glb_lod0(props_table.HERE / f'work/mm9_deco_{prop}.glb')
        engine_scale = variant['height'] / (a[:, 1].max() - a[:, 1].min())
        placed = np.stack([-a[:, 0], a[:, 2], a[:, 1]], 1) * engine_scale @ rot(-ry).T + position
        if meta.get('flame_head_m'):          # the flame cards are not in the bake
            placed = placed[a[:, 1] * engine_scale < (meta['flame_head_m'][2] * 81.7 * engine_scale) - 1]
        d, _ = cKDTree(bake).query(placed)
        fit = float(np.median(d))
        worst = max(worst, fit)
        entry = {'source_object': idx, 'source_name': p['Name'], 'class': o['class'], 'kind': CLASS_KIND[o['class']],
                 'source_model': p['Filename'], 'source_skin': p.get('Skin'), 'prop': prop,
                 'decoration': variant['decoration'], 'x': round(float(position[0]), 1),
                 'y': round(float(position[1]), 1), 'z': round(float(position[2]), 1),
                 'yaw_degrees': round(math.degrees(-ry) % 360.0, 2), 'fit_median_units': round(fit, 2)}
        if o['class'] == 'WallTorch':
            distance = np.linalg.norm(light_points - pos_old, axis=1)
            nearest = int(distance.argmin())
            entry['light'] = {'name': lights[nearest]['name'], 'distance': round(float(distance[nearest])),
                              'radius': lights[nearest]['radius'], 'colour': lights[nearest]['colour']}
        entries.append(entry)
    (PROJECT / 'props.json').write_text(json.dumps(entries, indent=1) + '\n')
    fits = np.array([e['fit_median_units'] for e in entries])
    print('WROTE', PROJECT / 'props.json', len(entries), 'entries; fit median of medians', round(float(np.median(fits)), 2),
          'worst', round(worst, 2))
    for e in sorted(entries, key=lambda e: -e['fit_median_units'])[:5]:
        print('  ', e['source_object'], e['source_name'], e['prop'], e['fit_median_units'])


if __name__ == '__main__':
    main()
