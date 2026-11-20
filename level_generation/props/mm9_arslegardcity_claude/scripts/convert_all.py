#!/usr/bin/env python3
"""Converts every Arslegard City prop built here to raw GLBs with tools/mm9_import_discovery/convert_abc_model.py
(rigid export, MM9 skins as PNG): LOD 0 in work/raw/<prop>/<prop>.glb and each native ABC LOD n in
work/raw/<prop>/lod<n>/. A tilted variant (the claws, the toppled chairs and stool) converts its upright source model
into work/raw/<variant>/; build.py bakes the tilt. A model with two skins binds skin k to ABC material k (texture ids
<prop> and <prop>_<k>). Posed props (props_table.POSES) are exported in full. A HidePiece variant (props_table.HIDDEN)
then has its hidden pieces' meshes dropped from every raw GLB (Bathhouse's strip_pieces.py): the build never sees them.
Uses the isle props project's venv (pygltflib). Usage: convert_all.py [prop ...]"""
import json
import os
import struct
import subprocess
import sys
from pathlib import Path

import props_table

PY = props_table.ISLE / 'work/venv/bin/python'
TOOL = props_table.REPO / 'tools/mm9_import_discovery'


def convert(prop):
    """Rigid export; a model with deforming pieces is exported in full and its bind pose is baked in Blender
    (work/raw/<prop>/mode.txt says which)."""
    model, skins = props_table.source(prop)
    model = props_table.resolve(model)
    textures = []
    for k, skin in enumerate(skins):
        texture_id = prop if k == 0 else f'{prop}_{k}'
        textures += ['--texture', f'{k}={props_table.resolve(skin)}', '--texture-id', f'{k}={texture_id}']
    out = props_table.HERE / 'work/raw' / prop
    for mode in (('full',) if prop in props_table.POSES else ('rigid', 'full')):
        script = 'convert_abc_model.py' if prop not in props_table.LIBRARY else \
            str(props_table.HERE / 'scripts/convert_library_pose.py')
        base = [str(PY), script, str(model), '--id', prop, '--export-mode', mode] + textures
        result = subprocess.run(base[:3] + [str(out)] + base[3:], cwd=TOOL, capture_output=True, env=env(prop))
        if result.returncode == 0:
            break
    else:
        raise SystemExit(f'{prop}: {result.stderr.decode()[-500:]}')
    (out / 'mode.txt').write_text(mode + '\n')
    for lod in (1, 2, 3):
        result = subprocess.run(base[:3] + [str(out / f'lod{lod}')] + base[3:] + ['--lod', str(lod)], cwd=TOOL,
                                capture_output=True, env=env(prop))
        if result.returncode != 0:
            break
    if prop in props_table.HIDDEN:
        for path in sorted(out.rglob(f'{prop}.glb')):
            dropped = strip(path, props_table.HIDDEN[prop])
            wild = [p for p in props_table.HIDDEN[prop] if p.endswith('*')]
            if (dropped != len(props_table.HIDDEN[prop])) if not wild else dropped < len(props_table.HIDDEN[prop]):
                raise SystemExit(f'{path}: dropped {dropped} of {props_table.HIDDEN[prop]}')
    print('CONVERTED', prop, model.name, [s.name for s in skins], mode)


def env(prop):
    """The library animation a LIBRARY prop's export adds (scripts/convert_library_pose.py)."""
    out = dict(os.environ)
    if prop in props_table.LIBRARY:
        library, animation = props_table.LIBRARY[prop]
        path = props_table.resolve(props_table.EXTRACTED / 'MODELS/MODELS' / library)
        out['LIBRARY_POSE'] = f'{path}|{animation}'
    return out


def strip(path: Path, pieces) -> int:
    """Drop the meshes of the nodes named like the pieces (case-insensitive; a trailing * matches a prefix) from a raw
    GLB."""
    data = path.read_bytes()
    full = path.with_name(path.stem + '_full.glb')      # the unstripped export: placements.py fits against MM9's bake
    full.write_bytes(data)
    length = struct.unpack('<I', data[12:16])[0]
    gltf = json.loads(data[20:20 + length])
    names = {p.lower() for p in pieces if not p.endswith('*')}
    prefixes = tuple(p[:-1].lower() for p in pieces if p.endswith('*'))

    def hidden(name):
        name = name.split('.')[0].lower()
        return name in names or (prefixes and name.startswith(prefixes))
    drop = {i for i, n in enumerate(gltf['nodes']) if hidden(n.get('name', '')) and 'mesh' in n}
    for index in drop:                  # the node stays (an empty); its mesh goes (Blender imports orphan nodes too)
        gltf['nodes'][index].pop('mesh', None)
        gltf['nodes'][index].pop('skin', None)
    text = json.dumps(gltf, separators=(',', ':')).encode()
    text += b' ' * (-len(text) % 4)
    rest = data[20 + length:]
    out = data[:12] + struct.pack('<I', len(text)) + data[16:20] + text + rest
    out = out[:8] + struct.pack('<I', len(out)) + out[12:]
    path.write_bytes(out)
    return len(drop)


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
