#!/usr/bin/env python3
"""Finish this batch's models: work/<prop>_export.glb -> material settings (alpha mode, double-sided, unlit; per-output
material factors such as the pedestal orb colours) -> tools/link_static_model_lods.py -> validation (one mesh node,
LOD chain, triangle budgets, COLOR_0 on every primitive, base on the ground) -> work/mm7_deco_<decoration>.glb (named after the decoration it serves); with
--install each output goes through tools/install_model.py --engine.
Usage: finish.py <prop> [--install]"""
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'tools'))
import link_static_model_lods as link  # noqa: E402

FLAME = {'alpha': 'BLEND', 'double': True, 'unlit': True}
CAGE = {'alpha': 'MASK', 'cutoff': 0.5, 'double': True}
HALO = {'alpha': 'BLEND', 'double': True, 'unlit': True}
FIRE = {'Flame': FLAME, 'Halo': HALO}       # 'Flame' also covers the off-axis cards FlameA, FlameB, FlameC


def linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


# Magic pedestal orbs: native orb colours of all eight frames (sRGB 10th and 50th luminance percentiles). The orb
# texture is pale grey (linear mean 0.843); its baseColorFactor is the deep (10th percentile) colour, so the lit glass
# keeps the sprite's saturation, and the emission (the native orbs read self-lit) is the median colour at ORB_GLOW.
ORBS = {
    'pearl': ('dec64', (173, 151, 134), (217, 196, 176)), 'amber': ('dec65', (147, 121, 100), (194, 164, 140)),
    'white': ('dec66', (206, 206, 206), (250, 251, 250)), 'green': ('dec67', (65, 175, 81), (100, 225, 139)),
    'blue': ('dec68', (4, 161, 255), (92, 185, 255)), 'crimson': ('dec69', (84, 35, 44), (177, 36, 43)),
    'orange': ('dec70', (255, 104, 50), (245, 168, 132)), 'pink': ('dec71', (217, 155, 187), (251, 208, 229)),
    'purple': ('dec72', (108, 50, 195), (162, 96, 243)), 'red': ('dec73', (215, 34, 43), (255, 86, 74)),
    'silver': ('dec74', (167, 166, 165), (210, 210, 209)), 'yellow': ('dec75', (177, 178, 74), (216, 222, 115))}
ORB_TEXTURE_MEAN = 0.843
ORB_GLOW = 0.22
ORB_HALO = 0.45


def orb_factors(deep, median):
    return {'Orb': {'base': [round(min(1.0, linear(c) / ORB_TEXTURE_MEAN), 4) for c in deep] + [1.0],
                    'emissive': [round(linear(c) * ORB_GLOW, 4) for c in median]},
            # The additive halo (white texture): the median orb colour, faint.
            'Halo': {'base': [round(linear(c) * ORB_HALO, 4) for c in median] + [1.0]}}


FINISH = {
    'beacon_stone_blue': {'outputs': {'mm7_deco_dec60.glb': {}}, 'budget': [2500, 1000, 400],
                          'materials': FIRE},
    'beacon_stone_orange': {'outputs': {'mm7_deco_dec62.glb': {}}, 'budget': [2500, 1000, 400],
                            'materials': FIRE},
    'beacon_stone_white': {'outputs': {'mm7_deco_dec63.glb': {}}, 'budget': [2500, 1000, 400],
                           'materials': FIRE},
    'beacon_gold': {'outputs': {'mm7_deco_dec61.glb': {}}, 'budget': [3500, 2000, 1000, 400],
                    'materials': FIRE},
    'pedestal': {'outputs': {f'mm7_deco_{decoration}.glb': orb_factors(deep, median)
                             for decoration, deep, median in ORBS.values()},
                 'budget': [2500, 1100, 300], 'materials': {'Halo': HALO}},
    'buoy': {'outputs': {'mm7_deco_7dec33.glb': {}}, 'budget': [3000, 1300, 450], 'materials': {}},
    'lantern': {'outputs': {'mm7_deco_torch02.glb': {}}, 'budget': [1500, 700, 300],
                'materials': {'Cage': CAGE, 'Halo': HALO}},
    'lantern_free': {'outputs': {'mm7_deco_torch02_free.glb': {}}, 'budget': [1500, 700, 300],
                     'materials': {'Cage': CAGE, 'Halo': HALO}},
    'burnedfire': {'outputs': {'mm7_deco_dec24x.glb': {}}, 'budget': [1500, 600, 250], 'materials': {}},
    # The lit signal fire (v77dec24): dec24x's logs plus flame cards and an ember bed.
    'litfire': {'outputs': {'mm7_deco_v77dec24.glb': {}}, 'budget': [1500, 600, 250], 'materials': FIRE},
}


def finish(document, spec, overrides):
    for material in document['materials']:
        settings = next((value for key, value in spec['materials'].items() if material['name'].startswith(key)), {})
        material.pop('alphaMode', None)
        material.pop('alphaCutoff', None)
        if settings.get('alpha'):
            material['alphaMode'] = settings['alpha']
            if settings['alpha'] == 'MASK':
                material['alphaCutoff'] = settings.get('cutoff', 0.5)
        material['doubleSided'] = settings.get('double', False)
        if settings.get('unlit'):
            material.setdefault('extensions', {})['KHR_materials_unlit'] = {}
            document.setdefault('extensionsUsed', [])
            if 'KHR_materials_unlit' not in document['extensionsUsed']:
                document['extensionsUsed'].append('KHR_materials_unlit')
        factors = overrides.get(material['name'], {})
        if 'base' in factors:
            material.setdefault('pbrMetallicRoughness', {})['baseColorFactor'] = factors['base']
        if 'emissive' in factors:
            material['emissiveFactor'] = factors['emissive']
    link.link(document)


def validate(path, budget):
    document, _ = link.read_glb(path)
    problems = []
    base = [node for node in document['nodes'] if 'mesh' in node]
    if len(base) != 1:
        problems.append(f'{len(base)} mesh nodes')
    chain = [base[0]['mesh']] + document['meshes'][base[0]['mesh']].get('extras', {}).get('openyamm_lods', [])
    triangles = [sum(document['accessors'][p['indices']]['count'] // 3 for p in document['meshes'][i]['primitives'])
                 for i in chain]
    if len(chain) < 3:
        problems.append('LOD chain shorter than 3')
    for count, limit in zip(triangles, budget):
        if count > limit:
            problems.append(f'{count} triangles over {limit}')
    lowest, highest = 1e9, -1e9
    for index in chain:
        for primitive in document['meshes'][index]['primitives']:
            if 'COLOR_0' not in primitive['attributes']:
                problems.append('missing COLOR_0')
            accessor = document['accessors'][primitive['attributes']['POSITION']]
            lowest = min(lowest, accessor['min'][1])
            highest = max(highest, accessor['max'][1])
    if abs(lowest) > 0.03:
        problems.append(f'base at y {lowest:.3f}')
    materials = {m['name']: (m.get('alphaMode', 'OPAQUE'),
                             'unlit' if 'KHR_materials_unlit' in m.get('extensions', {}) else '', m.get('extras', {}))
                 for m in document['materials']}
    return triangles, round(highest * 81.7, 1), materials, problems


def main():
    prop = sys.argv[1]
    spec = FINISH[prop]
    failed = False
    for output, overrides in spec['outputs'].items():
        document, binary = link.read_glb(HERE / 'work' / f'{prop}_export.glb')
        finish(document, spec, overrides)
        out = HERE / 'work' / output
        link.write_glb(out, document, binary)
        triangles, top, materials, problems = validate(out, spec['budget'])
        print('VALID' if not problems else 'INVALID', output, 'triangles', triangles, 'top (units)', top,
              'bytes', os.path.getsize(out), problems)
        print('   materials', json.dumps(materials))
        failed = failed or bool(problems)
        if not problems and '--install' in sys.argv:
            subprocess.run([sys.executable, str(REPO / 'tools' / 'install_model.py'), str(out), '--engine',
                            '--name', output], check=True)
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
