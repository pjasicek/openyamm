#!/usr/bin/env python3
"""Converts every keep prop's ABC to raw GLBs with tools/mm9_import_discovery/convert_abc_model.py (rigid export, MM9
skin as PNG): LOD 0 in work/raw/<prop>/<prop>.glb and each native ABC LOD n in work/raw/<prop>/lod<n>/. Uses the isle
props project's venv (pygltflib). Usage: convert_all.py [prop ...]"""
import subprocess
import sys

import props_table

PY = props_table.ISLE / 'work/venv/bin/python'
TOOL = props_table.REPO / 'tools/mm9_import_discovery'


def convert(prop):
    """Rigid export; a model with deforming pieces (the weapon rack) is exported in full and its bind pose is baked
    in Blender (work/raw/<prop>/mode.txt says which)."""
    model, skin = (props_table.resolve(p) for p in props_table.source(prop))
    for mode in ('rigid', 'full'):
        base = [str(PY), 'convert_abc_model.py', str(model), '--id', prop, '--export-mode', mode, '--texture',
                f'0={skin}']
        result = subprocess.run(base[:3] + [str(props_table.HERE / 'work/raw' / prop)] + base[3:], cwd=TOOL,
                                capture_output=True)
        if result.returncode == 0:
            break
    else:
        raise SystemExit(f'{prop}: {result.stderr.decode()[-500:]}')
    (props_table.HERE / f'work/raw/{prop}/mode.txt').write_text(mode + '\n')
    for lod in (1, 2, 3):
        out = props_table.HERE / f'work/raw/{prop}/lod{lod}'
        result = subprocess.run(base[:3] + [str(out)] + base[3:] + ['--lod', str(lod)], cwd=TOOL, capture_output=True)
        if result.returncode != 0:
            break
    print('CONVERTED', prop, model.name, skin.name, mode)


def main():
    for prop in sys.argv[1:] or sorted(set(props_table.MODELS.values())):
        convert(prop)


if __name__ == '__main__':
    main()
