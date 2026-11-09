#!/usr/bin/env python3
"""Finish one isle prop: work/<prop>_export.glb -> materials (alpha mode, double-sided, unlit, emission, extras) ->
tools/link_static_model_lods.py -> checks (one mesh node, LOD triangles decreasing, COLOR_0 on every primitive, base
on the ground, check_winding.py: 0 inverted closed parts) -> work/mm9_deco_<prop>.glb; --install hands it to
tools/install_model.py --world mm9 (source in assets_source/engine/models/, cooked runtime copy in assets_dev).
Usage: finish.py <prop>... [--install]"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / 'tools'))
import link_static_model_lods as link  # noqa: E402

# A flame card turns about its own centre ("card"): a plain billboard drops the model's depth and stands on the model's
# vertical axis, which puts the flame of a torch whose head leans off that axis over the bracket.
FIRE = {'alpha': 'BLEND', 'double': True, 'unlit': True,
        'extras': {'openyamm_billboard': 'card', 'openyamm_flipbook': [16, 4, 30], 'openyamm_specular': 0.0}}
ORB = {'emissive': [0.30, 0.03, 0.02], 'extras': {'openyamm_pulse': [0.35, 2.5], 'openyamm_uv_scroll': [0.04, 0.0]}}
PROPS = ['book', 'coatrack', 'cookpot', 'cot', 'dresser', 'logsburning', 'podium', 'roundtable', 'shipwreck', 'skull',
         'statstone', 'stonedebris02', 'stonedebris03', 'stool', 'vikingship', 'well']
CUTOUT = {'cookpot'}
CHECK_WINDING = REPO / 'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py'


def settings(prop, name):
    if name == 'Fire':
        return FIRE
    if name == f'{prop}_orb':
        return ORB
    out = {'alpha': 'MASK', 'cutoff': 0.5} if prop in CUTOUT else {}
    if name.endswith('_2s'):
        out = dict(out, double=True)
    return out


def finish(prop, install):
    document, binary = link.read_glb(HERE / 'work' / f'{prop}_export.glb')
    for material in document['materials']:
        spec = settings(prop, material['name'])
        material.pop('alphaMode', None); material.pop('alphaCutoff', None)
        if spec.get('alpha'):
            material['alphaMode'] = spec['alpha']
            if spec['alpha'] == 'MASK':
                material['alphaCutoff'] = spec.get('cutoff', 0.5)
        material['doubleSided'] = spec.get('double', False)
        if spec.get('unlit'):
            material.setdefault('extensions', {})['KHR_materials_unlit'] = {}
            used = document.setdefault('extensionsUsed', [])
            if 'KHR_materials_unlit' not in used:
                used.append('KHR_materials_unlit')
        if spec.get('emissive'):
            material['emissiveFactor'] = spec['emissive']
        if spec.get('extras'):
            material.setdefault('extras', {}).update(spec['extras'])
    if any(n.get('name', '').endswith('_LOD1') for n in document['nodes']):
        link.link(document)
    out = HERE / 'work' / f'mm9_deco_{prop}.glb'
    link.write_glb(out, document, binary)
    document, _ = link.read_glb(out)
    problems = []
    base = [n for n in document['nodes'] if 'mesh' in n]
    if len(base) != 1:
        problems.append(f'{len(base)} mesh nodes')
    mesh = document['meshes'][base[0]['mesh']]
    chain = [base[0]['mesh']] + mesh.get('extras', {}).get('openyamm_lods', [])
    triangles = [link.triangles(document, i) for i in chain]
    if any(b >= a for a, b in zip(triangles, triangles[1:])):
        problems.append(f'LOD triangles not decreasing {triangles}')
    lowest, highest = 1e9, -1e9
    for index in chain:
        for primitive in document['meshes'][index]['primitives']:
            if 'COLOR_0' not in primitive['attributes']:
                problems.append('missing COLOR_0')
            accessor = document['accessors'][primitive['attributes']['POSITION']]
            lowest = min(lowest, accessor['min'][1]); highest = max(highest, accessor['max'][1])
    if abs(lowest) > 0.003:
        problems.append(f'base at y {lowest:.4f}')
    check = subprocess.run([sys.executable, str(CHECK_WINDING), str(out)], capture_output=True, text=True)
    inverted = [line for line in check.stdout.splitlines() if line.startswith('INVERTED')]
    if inverted or check.returncode not in (0, 1):
        problems.append(f'{len(inverted)} inverted closed parts')
    materials = {m['name']: (m.get('alphaMode', 'OPAQUE'), 'double' if m.get('doubleSided') else 'single')
                 for m in document['materials']}
    print('VALID' if not problems else 'INVALID', out.name, 'triangles', triangles, 'height_m',
          round(highest - lowest, 4), materials, 'bytes', os.path.getsize(out), problems)
    if problems:
        return False
    if install:
        subprocess.run([sys.executable, str(REPO / 'tools/install_model.py'), str(out), '--world', 'mm9', '--name',
                        out.name], check=True, cwd=REPO)
        print('INSTALLED', out.name)
    return True


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    ok = all([finish(prop, '--install' in sys.argv) for prop in (args or PROPS)])
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
