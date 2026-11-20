#!/usr/bin/env python3
"""MM9 HidePiece: drop the hidden pieces' nodes from a prop's raw converter GLBs (LOD0 and work/raw/<prop>/lod<n>/), so
the build never sees them. The towel racks are MM9's CoatRack1 with HidePiece0 Hat1 (towels, no hat).
Usage: strip_pieces.py   (runs on HIDDEN)"""
import json
import struct
from pathlib import Path

import props_table

HIDDEN = {'towelrack': ['Hat1']}


def strip(path: Path, pieces) -> int:
    data = path.read_bytes()
    full = path.with_name(path.stem + '_full.glb')      # the unstripped import (placements.py fits against MM9's bake)
    if not full.exists():
        full.write_bytes(data)
    length = struct.unpack('<I', data[12:16])[0]
    gltf = json.loads(data[20:20 + length])
    drop = {i for i, n in enumerate(gltf['nodes']) if n.get('name', '').split('.')[0] in pieces and 'mesh' in n}
    if not drop:
        return 0
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
    for prop, pieces in HIDDEN.items():
        for path in sorted((props_table.HERE / 'work/raw' / prop).rglob(f'{prop}.glb')):
            print(path, 'dropped', strip(path, pieces), 'nodes')


if __name__ == '__main__':
    main()
