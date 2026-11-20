#!/usr/bin/env python3
"""Converts every Lich Lab prop's ABC to raw GLBs with tools/mm9_import_discovery/convert_abc_model.py (rigid export,
MM9 skins as PNG): LOD 0 in work/raw/<prop>/<prop>.glb and each native ABC LOD n in work/raw/<prop>/lod<n>/. A model
with two skins (the skeleton statue and its base, the herb bag) binds skin k to ABC material k, texture ids <prop> and
<prop>_<k>. Uses the isle props project's venv (pygltflib). Usage: convert_all.py [prop ...]"""
import subprocess
import sys

import props_table

PY = props_table.ISLE / 'work/venv/bin/python'
TOOL = props_table.REPO / 'tools/mm9_import_discovery'
SANITIZE = {'flayingbench'}         # NaN UVs on a few faces: scripts/convert_sanitized.py


def convert(prop):
    """Rigid export; a model with deforming pieces is exported in full and its bind pose is baked in Blender
    (work/raw/<prop>/mode.txt says which)."""
    model, skins = props_table.source(prop)
    model = props_table.resolve(model)
    textures = []
    for k, skin in enumerate(skins):
        textures += ['--texture', f'{k}={props_table.resolve(skin)}', '--texture-id', f"{k}={prop if k == 0 else f'{prop}_{k}'}"]
    out = props_table.HERE / 'work/raw' / prop
    for mode in ('rigid', 'full'):
        script = 'convert_abc_model.py' if prop not in SANITIZE else str(props_table.HERE / 'scripts/convert_sanitized.py')
        base = [str(PY), script, str(model), '--id', prop, '--export-mode', mode] + textures
        result = subprocess.run(base[:3] + [str(out)] + base[3:], cwd=TOOL, capture_output=True)
        if result.returncode == 0:
            break
    else:
        raise SystemExit(f'{prop}: {result.stderr.decode()[-500:]}')
    (out / 'mode.txt').write_text(mode + '\n')
    for lod in (1, 2, 3):
        result = subprocess.run(base[:3] + [str(out / f'lod{lod}')] + base[3:] + ['--lod', str(lod)], cwd=TOOL,
                                capture_output=True)
        if result.returncode != 0:
            break
    print('CONVERTED', prop, model.name, [s.name for s in skins], mode)


def main():
    failed = []
    for prop in sys.argv[1:] or props_table.built_props():
        try:
            convert(prop)
        except SystemExit as error:
            failed.append(prop)
            print('FAILED', str(error)[-300:])
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
