"""Replace the dragonfly's vertex-group weights in a blend with work/weights.npz (rig_plan.py), keeping UVs and
clips. Args: blend (relative to the project, saved in place)."""
import bpy, os, sys
import numpy as np
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
blend = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, blend))
mesh = bpy.data.objects['Dragonfly']
d = np.load(os.path.join(P, 'work/weights.npz')); W, names = d['W'], [str(n) for n in d['names']]
assert len(mesh.data.vertices) == len(W)
for g in list(mesh.vertex_groups): mesh.vertex_groups.remove(g)
for j, n in enumerate(names):
    g = mesh.vertex_groups.new(name=n)
    for v in np.nonzero(W[:, j] > 1e-5)[0]: g.add([int(v)], float(W[v, j]), 'REPLACE')
bpy.ops.wm.save_mainfile()
print('REWEIGHTED', blend)
