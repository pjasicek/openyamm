#!/usr/bin/env python3
"""Drop vertices no triangle uses from every primitive (preserve_wing_lods.py merges the wing triangles with the whole
LOD0 vertex set into each LOD: LOD3 carried 13,402 vertices for 5,034 triangles), then compact the buffer.
Usage: prune_vertices.py <glb> (in place)"""
import subprocess, sys
from pathlib import Path
import numpy as np
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from merge_head_material import read_glb, write_glb, accessor_array, append_accessor  # noqa: E402
path = Path(sys.argv[1]); d, b = read_glb(path); b = bytearray(b)
for mesh in d['meshes']:
    for p in mesh['primitives']:
        idx = accessor_array(d, b, p['indices']).ravel()
        n = d['accessors'][p['attributes']['POSITION']]['count']
        used = np.unique(idx)
        if len(used) == n:
            continue
        remap = np.full(n, -1, np.int64); remap[used] = np.arange(len(used))
        for sem, a in list(p['attributes'].items()):
            tmpl = d['accessors'][a]
            p['attributes'][sem] = append_accessor(d, b, accessor_array(d, b, a)[used], tmpl, 34962)
        p['indices'] = append_accessor(d, b, remap[idx].astype(np.uint32), {'componentType': 5125, 'type': 'SCALAR'}, 34963)
        print('PRUNED', mesh['name'], n, '->', len(used))
write_glb(path, d, b)
subprocess.run([sys.executable, str(P / 'scripts/compact_glb.py'), str(path)], check=True)
