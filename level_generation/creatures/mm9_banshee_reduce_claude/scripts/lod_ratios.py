#!/usr/bin/env python3
"""Per-material LOD ratios for build_lods.py: LOD1 keeps the default 0.5; LOD2 and LOD3 are never coarser than the
installed model's LODs of the same primitive (outer triangles, lining excluded), within 0.18-0.45 and 0.06-0.2. With the
default 0.18 / 0.06 of the reduced LOD0, LOD3 lost the hem's lowest 16 mm and the torso's shoulders (38 triangles).
Usage: lod_ratios.py <reduced runtime_lod0.glb> <installed.glb> <out.json>"""
import json, sys
import glbpack as G, glbio
r, rb = G.read(sys.argv[1]); i, ib = G.read(sys.argv[2])
LINED = ('BansheeSkirt', 'BansheeCape', 'BansheeWingL', 'BansheeWingR')
n0 = {p['material']: len(p['T']) for p in glbio.prims(r, bytes(rb), 0)}
inst = {}
for li in (2, 3):
    for p in glbio.prims(i, bytes(ib), li):
        base = p['material'].rsplit('_', 1)[0]
        inst[(base, li)] = len(p['T']) // (2 if base in LINED else 1)
out = {}
for m, n in n0.items():
    r2 = min(0.45, max(0.18, inst[(m, 2)] / n)); r3 = min(0.2, max(0.06, inst[(m, 3)] / n))
    out[m] = [0.5, round(r2, 4), round(r3, 4)]
json.dump(out, open(sys.argv[3], 'w'), indent=1)
print('LOD RATIOS', out)
