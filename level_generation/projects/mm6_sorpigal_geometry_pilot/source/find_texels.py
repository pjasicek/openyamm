"""Which faces own given texels of the outdoor bake's building pages (replays bake_outdoor's chart packing).

  python3 source/find_texels.py <page> <y> <x> [<page> <y> <x> ...]
"""
import json
import math
import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT / 'util'))
sys.path.insert(0, str(ROOT / 'tools/lighting'))
import map_export  # noqa: E402
from bake_geometry import face_basis, pack_lightmap_charts  # noqa: E402

stage = PROJECT / 'playtest/assets_dev/worlds/mm6/maps'
native = map_export.parse_odm_file(stage / 'oute3.odm')['payload']
scene = yaml.load((stage / 'oute3.scene.yml').read_text(), Loader=yaml.CSafeLoader)
for o in scene['bmodel_faces']['interactive_faces']:
    native['bmodels'][o['bmodel_index']]['faces'][o['face_index']]['attributes'] = o['legacy_attributes']
profile = json.loads((PROJECT / 'build/profile.json').read_text())
charts, charted = [], {}
for bi, model in enumerate(native['bmodels']):
    for fi, face in enumerate(model['faces']):
        points = [tuple(model['vertices'][i][k] for k in 'xyz') for i in face['vertex_indices']]
        if len(points) < 3 or face['attributes'] & 0x2000 or not face['texture_name']:
            continue
        key = (face['texture_name'].lower(), tuple(sorted(tuple(round(c) for c in p) for p in points)))
        if key in charted:
            continue
        charted[key] = 1
        basis = face_basis(points)
        if basis is None:
            continue
        au, av = basis
        coords = [(sum(p[k] * au[k] for k in range(3)), sum(p[k] * av[k] for k in range(3))) for p in points]
        span = [max(max(c[i] for c in coords) - min(c[i] for c in coords), 1) for i in range(2)]
        spacing = profile.get('model_units_per_texel', {}).get(model['name'], profile['units_per_texel'])
        w, h = [max(4, math.ceil(v / spacing) + 1) for v in span]
        charts.append(((w, h), bi, fi, model['name'], face['texture_name']))
placements, dims = pack_lightmap_charts([c[0] for c in charts], profile['building_page_size'])
args = list(map(int, sys.argv[1:]))
for page, y, x in zip(args[0::3], args[1::3], args[2::3]):
    for chart, (pi, px, py, w, h) in zip(charts, placements):
        # bake pages are stored bottom-up in Blender's pixel order
        for yy in (y, dims[pi][1] - 1 - y):
            if pi == page and px - 4 <= x < px + w + 4 and py - 4 <= yy < py + h + 4:
                print(page, y, x, '->', chart[1:], 'chart', (px, py, w, h), 'flipped' if yy != y else '')
