#!/usr/bin/env python3
"""Writes level_generation/projects/mm9r_thjoradmine/props.json: every Thjorad Mine prop and chest placement in the native
frame (the old bmodel_world map's frame, which the BLV keeps: no offset), and checks each end to end as the Anskram
props project does: the finished GLB's LOD0, placed the way the engine places a decoration model (glTF (x, y, z) ->
OpenYAMM (-x, z, y), scaled by binding height / bounds height, turned by the facing, at the entity position),
against the old map's baked BModel of the same object (MM9_static_prop_<object>_<name>, MM9_chest_<object>_<name>);
median vertex distance printed. Objects the old import did not bake (the herb bags and jars it skipped as pickups,
BonePile1's broken model) are placed by the transcoder's rule alone (fit null).
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

sys.path.insert(0, str(props_table.REPO / 'level_generation/projects/mm9r_common'))
from dungeon.source import floor_below  # noqa: E402

REPO = props_table.REPO
PROJECT = REPO / 'level_generation/projects/mm9r_thjoradmine'
# Placements whose bake is another model (BonePile1: MM9's lever model) keep the transcoder's position.
OTHER_MODEL = set()
# Posed props (PropAnim.scr "onside", built posed by their owners): the old bake is the ABC's bind pose, so neither its
# box nor its fit apply; the posed base lies on the floor under the DAT position (the pickaxes lie 7 LT over it, the
# beds MoveToFloor), as Tasar Academy's pickaxes and Verhoffin's beds.
POSED = {'dwarfaxeonside', 'bedmedium2onside'}
CLASS_KIND = {'Prop': 'prop', 'Barrel': 'barrel', 'BonePile': 'bone_pile', 'TreasureChest': 'chest',
              'Brazier': 'brazier', 'DestructableProp': 'prop', 'WallTorch': 'torch', 'CandleProp': 'torch'}


def tilt_oy(local, pitch, roll):
    """The transcoder's object pitch (about x) then roll (about y), in OpenYAMM-local axes (the isle's placements)."""
    cx, sx, cy, sy = math.cos(pitch), math.sin(pitch), math.cos(roll), math.sin(roll)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ryy = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    return local @ (ryy @ rx).T


def rot(yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


_floors = None


def floors():
    """The Thjorad Mine's static polygons (the shared dungeon converter's source) for floor queries."""
    global _floors
    if _floors is None:
        from dungeon.source import Project, Source, classify_models
        project = Project.load(PROJECT, install=False)
        source = Source(project)
        plan = classify_models(source)
        _floors = [poly for name in plan['static'] for poly in source.polygons(name)]
    return _floors


def bmodels():
    sys.path.insert(0, str(REPO))
    from util.map_export import parse_odm_file
    payload = parse_odm_file(REPO / 'assets_editor_dev/worlds/mm9/maps/thjoradmine.odm')['payload']
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


def main():
    baked = bmodels()
    plan = json.loads((props_table.HERE / 'work/decorations_plan.json').read_text())
    raw = {o['index']: o for o in props_table.objects()}
    entries, worst, unbaked = [], 0.0, []
    # Decoration rows that carry a light (the isle's cook pot over its fire): the map counts them in its light check.
    row_lights = {cells[1].strip(): int(cells[6]) for cells in
                  (line.split('\t') for line in (REPO / 'assets_dev/worlds/mm9/data_tables/decoration_data.txt')
                   .read_text(encoding='latin-1').splitlines()) if cells[0].strip().isdigit()}
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
        prefix = 'MM9_chest' if o['class'] == 'TreasureChest' else 'MM9_static_prop'
        bake = baked.get(f"{prefix}_{idx}_{p['Name']}") if props_table.anchor(idx, prop, p['Name']) == p['Name'] else None
        if prop in POSED:
            bake = None
        extra = np.zeros(3) if bake is None else (bake.min(0) + bake.max(0)) / 2 - (inst.min(0) + inst.max(0)) / 2
        position = pos_old + extra + rot(-ry) @ (np.array(meta['origin_local_units']) * s)
        if prop in POSED:
            position[2] = floor_below(floors(), p['Pos']) * 2.56
        elif bake is None and p.get('MoveToFloor'):      # dropped to the floor (or shelf) under it, as MM9 does
            floor = floor_below(floors(), p['Pos'])
            if floor is not None:
                position[2] = floor * 2.56
        a = glb_lod0(finished_glb(prop))
        engine_scale = variant['height'] / (a[:, 1].max() - a[:, 1].min())
        placed = np.stack([-a[:, 0], a[:, 2], a[:, 1]], 1) * engine_scale @ rot(-ry).T + position
        if meta.get('flame_head_m'):          # flame cards are not in the bake
            placed = placed[a[:, 1] * engine_scale < (meta['flame_head_m'][2] * 81.7 * engine_scale) - 1]
        fit = None
        if bake is not None and prop not in OTHER_MODEL:
            # centre the footprint on the bake's (the quarter-turned models' raw centres differ from their assets')
            shift = (bake.min(0) + bake.max(0)) / 2 - (placed.min(0) + placed.max(0)) / 2
            shift[2] = 0.0
            position, placed = position + shift, placed + shift
        if bake is not None:
            d, _ = cKDTree(bake).query(placed)
            fit = round(float(np.median(d)), 2)
            worst = max(worst, fit)
        else:
            unbaked.append(p['Name'])
        entries.append({'source_object': idx, 'source_name': props_table.anchor(idx, prop, p['Name']), 'class': o['class'],
                        'kind': CLASS_KIND[o['class']], 'source_model': p['Filename'], 'source_skin': p.get('Skin'),
                        'prop': prop, 'decoration': variant['decoration'], 'x': round(float(position[0]), 1),
                        'y': round(float(position[1]), 1), 'z': round(float(position[2]), 1),
                        'yaw_degrees': round(math.degrees(-ry) % 360.0, 2), 'fit_median_units': fit,
                        'script': p.get('ScriptName') or None, 'script_params': p.get('ScriptParams') or None,
                        'light_radius': row_lights.get(variant['decoration'], 0)})
    for e in entries:                       # extra placements name their own model and skin
        if e['source_name'] != raw[e['source_object']]['props']['Name']:
            model, skins = next(k for k, v in props_table.MODELS.items() if v == e['prop'])
            e['source_model'], e['source_skin'] = model, skins
    (PROJECT / 'props.json').write_text(json.dumps(entries, indent=1) + '\n')
    fits = np.array([e['fit_median_units'] for e in entries if e['fit_median_units'] is not None])
    print('WROTE', PROJECT / 'props.json', len(entries), 'entries; fit median of medians', round(float(np.median(fits)), 2),
          'worst', round(worst, 2), 'not baked in the old map:', unbaked)
    for e in sorted([e for e in entries if e['fit_median_units'] is not None], key=lambda e: -e['fit_median_units'])[:12]:
        print('  ', e['source_object'], e['source_name'], e['prop'], e['fit_median_units'])


if __name__ == '__main__':
    main()
