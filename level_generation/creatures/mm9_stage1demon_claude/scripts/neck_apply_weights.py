"""Neck pass: write neck_weights.py's result (npz: fi, W, gn) into the blend's vertex groups. Args: <in blend> <npz> <out blend>"""
import bpy, sys, numpy as np
IN, NPZ, OUT = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=IN)
o = bpy.data.objects['Body']; d = np.load(NPZ); fi = [int(i) for i in d['fi']]; W = d['W']; gn = [str(x) for x in d['gn']]
for nm in gn[len(o.vertex_groups):]: o.vertex_groups.new(name=nm)
assert gn == [g.name for g in o.vertex_groups]
for g in o.vertex_groups: g.remove(fi)
for k, i in enumerate(fi):
    for j in np.nonzero(W[k])[0]: o.vertex_groups[int(j)].add([i], float(W[k, j]), 'REPLACE')
print('APPLIED', len(fi))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
