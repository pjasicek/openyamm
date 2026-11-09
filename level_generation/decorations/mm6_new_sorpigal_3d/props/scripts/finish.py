#!/usr/bin/env python3
"""Finish one prop: work/<prop>_export.glb -> material settings from FINISH[prop] (alpha mode, double-sided, unlit,
emissive, extras) -> tools/link_static_model_lods.py -> validation (LOD chain, triangle budgets, COLOR_0 on every
primitive, base on the ground) -> work/<output>.glb, installed (0664) with --install.
Usage: finish.py <prop> [--install]"""
import json, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'tools'))
import link_static_model_lods as link

FINISH = {
    'cauldron': {'output': 'mm6_deco_cauldron.glb', 'budget': [3000, 1200, 400],
                 'materials': {'Fire': {'alpha': 'BLEND', 'double': True, 'unlit': True},
                               'Glow': {'unlit': True},
                               'Char': {'emissive': [0.05, 0.010, 0.002], 'extras': {'openyamm_pulse': [0.35, 1.3]}}}},
    # Revision 3 (2026-10-09): translucent flowing water falling into the map's pool (primitive order solid, streams).
    'fountain': {'output': 'mm6_deco_fountain.glb', 'budget': [8000, 3000, 1000],
                 'materials': {'Water': {'alpha': 'BLEND'}}},
    # One placement per map and seen up close: the sword's blade, quillons, wrapped grip and pommel get a hero budget.
    'swordstone': {'output': 'mm6_deco_swordstone.glb', 'budget': [4800, 1500, 450], 'materials': {}},
    'swordstone_empty': {'output': 'mm6_deco_swordstone_empty.glb', 'budget': [3000, 1200, 300], 'materials': {}},
    'surfrock_a': {'output': 'mm6_deco_surfrock_a.glb', 'budget': [2500, 1000, 300],
                   'materials': {'Foam': {'alpha': 'BLEND', 'double': True}}},
    'surfrock_b': {'output': 'mm6_deco_surfrock_b.glb', 'budget': [2500, 1000, 300],
                   'materials': {'Foam': {'alpha': 'BLEND', 'double': True}}},
    'buoy': {'output': 'mm6_deco_buoy.glb', 'budget': [2500, 1000, 300], 'materials': {}},
    'flag': {'output': 'mm6_deco_flag.glb', 'budget': [600, 250, 80], 'materials': {'Cloth': {'double': True}}},
    # Silver Cove, Misty Islands, Castle Ironfist and Eel Infested Waters (2026-10-09).
    'campfire': {'output': 'mm6_deco_campfire.glb', 'budget': [2000, 900, 300],
                 'materials': {'Fire': {'alpha': 'BLEND', 'double': True, 'unlit': True},
                               'Glow': {'unlit': True},
                               'Char': {'emissive': [0.05, 0.010, 0.002], 'extras': {'openyamm_pulse': [0.35, 1.3]}}}},
    'burningrock': {'output': 'mm6_deco_burningrock.glb', 'budget': [3000, 1200, 400],
                    'materials': {'Fire': {'alpha': 'BLEND', 'double': True, 'unlit': True},
                                  'Lava': {'alpha': 'MASK', 'cutoff': 0.5, 'unlit': True}}},
    # Dungeon log-pile fire dec04 (2026-10-09): planks and split logs, flame cards and a smoke flipbook card.
    'logfire': {'output': 'mm6_deco_logfire.glb', 'budget': [900, 400, 200],
                'materials': {'Fire': {'alpha': 'BLEND', 'double': True, 'unlit': True},
                              'Smoke': {'alpha': 'BLEND', 'double': True, 'unlit': True},
                              'Glow': {'unlit': True}, 'Embers': {'unlit': True},
                              'Char': {'emissive': [0.025, 0.006, 0.001], 'extras': {'openyamm_pulse': [0.35, 1.3]}}}},
    'flag1': {'output': 'mm6_deco_flag1.glb', 'budget': [900, 300, 80], 'materials': {'Cloth': {'double': True}}},
    'skullpile': {'output': 'mm6_deco_skullpile.glb', 'budget': [23000, 7000, 3200, 300], 'materials': {}},
    # outd2 (2026-10-09): pedestal, food bowl, keg and the impaled corpses.
    'pedestal': {'output': 'mm6_deco_pedestal.glb', 'budget': [2000, 700, 300], 'materials': {}},
    'foodbowl': {'output': 'mm6_deco_foodbowl.glb', 'budget': [1700, 600, 200], 'materials': {}},
    'keg': {'output': 'mm6_deco_keg.glb', 'budget': [2000, 900, 400], 'materials': {}},
    'corpse05': {'output': 'mm6_deco_corpse05.glb', 'budget': [6000, 2500, 900, 300], 'materials': {}},
    'corpse16': {'output': 'mm6_deco_corpse16.glb', 'budget': [4000, 1600, 600, 200], 'materials': {}},
    'corpse04': {'output': 'mm6_deco_corpse04.glb', 'budget': [6000, 2500, 900, 300], 'materials': {}},
    'corpse06': {'output': 'mm6_deco_corpse06.glb', 'budget': [6000, 2500, 900, 300], 'materials': {}},
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
    report = link.link(document)
    out = HERE / 'work' / spec['output']
    link.write_glb(out, document, binary)
    # validation on the written file
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
    lowest = 1e9
    for index in chain:
        for primitive in document['meshes'][index]['primitives']:
            if 'COLOR_0' not in primitive['attributes']:
                problems.append('missing COLOR_0')
            lowest = min(lowest, document['accessors'][primitive['attributes']['POSITION']]['min'][1])
    if abs(lowest) > 0.03:
        problems.append(f'base at y {lowest:.3f}')
    materials = {m['name']: (m.get('alphaMode', 'OPAQUE'), m.get('doubleSided', False),
                             'unlit' if 'KHR_materials_unlit' in m.get('extensions', {}) else '', m.get('extras', {}))
                 for m in document['materials']}
    size = os.path.getsize(out)
    print('VALID' if not problems else 'INVALID', spec['output'], 'triangles', triangles, 'materials', materials,
          'bytes', size, problems)
    if problems:
        sys.exit(1)
    if '--install' in sys.argv:
        destination = REPO / 'assets_dev' / 'worlds' / 'mm6' / 'models' / spec['output']
        subprocess.run(['install', '-m', '0664', str(out), str(destination)], check=True)
        print('INSTALLED', destination)


if __name__ == '__main__':
    main()
