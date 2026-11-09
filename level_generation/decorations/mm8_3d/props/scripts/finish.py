#!/usr/bin/env python3
"""Finish one MM8 prop: work/<prop>_export.glb -> material settings from FINISH[prop] (alpha mode, double-sided,
unlit, emissive, extras) -> tools/link_static_model_lods.py -> validation (LOD chain, triangle budgets, COLOR_0 on
every primitive, base on the ground) -> work/<output>, installed with --install through
tools/install_model.py --engine --name <output> (source in assets_source/engine/models/, cooked runtime copy).
Usage: finish.py <prop> [--install]"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'tools'))
import link_static_model_lods as link  # noqa: E402

FLAME = {'alpha': 'BLEND', 'double': True, 'unlit': True}
RUNE = {'alpha': 'MASK', 'cutoff': 0.4, 'emissive': [0.55, 0.03, 0.02], 'extras': {'openyamm_pulse': [0.3, 3.0]}}
ROOTS = {'alpha': 'MASK', 'cutoff': 0.5, 'double': True}
FINISH = {
    'skeleton': {'output': 'mm8_deco_skeleton.glb', 'budget': [2500, 1100, 650], 'materials': {}},
    'bonepile': {'output': 'mm8_deco_bonepile.glb', 'budget': [2500, 1200, 500], 'materials': {}},
    'carcass': {'output': 'mm8_deco_carcass.glb', 'budget': [3500, 1600, 650], 'materials': {}},
    'carrion': {'output': 'mm8_deco_carrion.glb', 'budget': [4000, 1800, 700], 'materials': {}},
    'barrel': {'output': 'mm8_deco_barrel.glb', 'budget': [1300, 700, 300], 'materials': {}},
    'runepost13': {'output': 'mm8_deco_runepost13.glb', 'budget': [1500, 700, 260], 'materials': {'Rune': RUNE,
                   'Rose': {'double': True}, 'Roots': ROOTS}},
    'runepost14': {'output': 'mm8_deco_runepost14.glb', 'budget': [1500, 700, 260], 'materials': {'Rune': RUNE}},
    'runepost15': {'output': 'mm8_deco_runepost15.glb', 'budget': [1500, 700, 260], 'materials': {'Rune': RUNE,
                   'Roots': ROOTS}},
    'runepost16': {'output': 'mm8_deco_runepost16.glb', 'budget': [1500, 700, 260], 'materials': {'Rune': RUNE,
                   'Roots': ROOTS}},
    'runepost17': {'output': 'mm8_deco_runepost17.glb', 'budget': [900, 450, 200],
                   'materials': {'Rune': RUNE, 'Roots': ROOTS}},
    'elfstatue': {'output': 'mm8_deco_elfstatue.glb', 'budget': [6000, 2500, 900], 'materials': {}},
    'metalbowls': {'output': 'mm8_deco_metalbowls.glb', 'budget': [1500, 850, 450], 'materials': {}},
    'woodplate': {'output': 'mm8_deco_woodplate.glb', 'budget': [600, 300, 150], 'materials': {}},
    'woodplates': {'output': 'mm8_deco_woodplates.glb', 'budget': [1500, 850, 450], 'materials': {}},
    'metalplates': {'output': 'mm8_deco_metalplates.glb', 'budget': [1800, 1000, 560], 'materials': {}},
    'cauldron': {'output': 'mm7_deco_cauldron.glb', 'budget': [3500, 1500, 500],
                 'materials': {'Fire': FLAME, 'Glow': {'unlit': True}, 'Brew': {'unlit': True},
                               'Char': {'emissive': [0.05, 0.010, 0.002], 'extras': {'openyamm_pulse': [0.35, 1.3]}},
                               'Coals': {'emissive': [0.30, 0.06, 0.01], 'extras': {'openyamm_pulse': [0.35, 1.7]}}}},
    'trashheap': {'output': 'mm7_deco_trash_heap.glb', 'budget': [3000, 1300, 450],
                  'materials': {'Bark': {'double': True}}},
    'goblet': {'output': 'mm7_deco_goblet.glb', 'budget': [300, 150, 60], 'materials': {}},
    'fruitbowl': {'output': 'mm7_deco_fruit_bowl.glb', 'budget': [3000, 1400, 550],
                  'materials': {'Leaves': {'double': True}}},
}


def main():
    prop = sys.argv[1]
    spec = FINISH[prop]
    document, binary = link.read_glb(HERE / 'work' / f'{prop}_export.glb')
    for material in document['materials']:
        settings = spec['materials'].get(material['name'], {})
        material.pop('alphaMode', None); material.pop('alphaCutoff', None)
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
        if settings.get('emissive'):
            material['emissiveFactor'] = settings['emissive']
        if settings.get('extras'):
            material.setdefault('extras', {}).update(settings['extras'])
    link.link(document)
    out = HERE / 'work' / spec['output']
    link.write_glb(out, document, binary)
    document, _ = link.read_glb(out)
    problems = []
    base = [n for n in document['nodes'] if 'mesh' in n]
    if len(base) != 1:
        problems.append(f'{len(base)} mesh nodes')
    mesh = document['meshes'][base[0]['mesh']]
    chain = [base[0]['mesh']] + mesh.get('extras', {}).get('openyamm_lods', [])
    triangles = [sum(document['accessors'][p['indices']]['count'] // 3 for p in document['meshes'][i]['primitives'])
                 for i in chain]
    if len(chain) < 3:
        problems.append('LOD chain shorter than 3')
    for count, budget in zip(triangles, spec['budget']):
        if count > budget:
            problems.append(f'{count} triangles over {budget}')
    lowest, highest = 1e9, -1e9
    for index in chain:
        for primitive in document['meshes'][index]['primitives']:
            if 'COLOR_0' not in primitive['attributes']:
                problems.append('missing COLOR_0')
            accessor = document['accessors'][primitive['attributes']['POSITION']]
            lowest = min(lowest, accessor['min'][1]); highest = max(highest, accessor['max'][1])
    if abs(lowest) > 0.03:
        problems.append(f'base at y {lowest:.3f}')
    materials = {m['name']: (m.get('alphaMode', 'OPAQUE'), m.get('doubleSided', False),
                             'unlit' if 'KHR_materials_unlit' in m.get('extensions', {}) else '', m.get('extras', {}))
                 for m in document['materials']}
    check = subprocess.run([sys.executable, str(REPO / 'level_generation' / 'decorations' / 'mm8_3d' / 'animated' /
                            'scripts' / 'check_winding.py'), str(out)], capture_output=True, text=True)
    inverted = [line for line in check.stdout.splitlines() if line.startswith('INVERTED')]
    if inverted:
        problems.append(f'{len(inverted)} inverted closed parts')
    size = os.path.getsize(out)
    print('VALID' if not problems else 'INVALID', spec['output'], 'triangles', triangles, 'height',
          round(highest - lowest, 4), 'materials', materials, 'bytes', size, problems)
    if problems:
        sys.exit(1)
    if '--install' in sys.argv:
        subprocess.run([sys.executable, str(REPO / 'tools' / 'install_model.py'), str(out), '--engine', '--name',
                        spec['output']], check=True, cwd=REPO)
        print('INSTALLED', spec['output'])


if __name__ == '__main__':
    main()
