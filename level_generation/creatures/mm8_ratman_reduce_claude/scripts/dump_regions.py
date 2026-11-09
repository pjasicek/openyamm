"""Per-face weight regions of work/source.blend -> work/regions.npz: finger weight (sum of B_*_Finger* groups) and
hand weight (B_*_Hand) averaged over the face's vertices, in the loop-triangle order of dump_mesh.py."""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
src = bpy.data.objects['Body']; me = src.data; me.calc_loop_triangles()
def wsum(pred):
    idx = {g.index for g in src.vertex_groups if pred(g.name)}
    return np.array([sum(g.weight for g in v.groups if g.group in idx) for v in me.vertices])
fing = wsum(lambda n: 'Finger' in n); hand = wsum(lambda n: n.endswith('_Hand')); tail = wsum(lambda n: n.startswith('Tail'))
tri = np.array([t.vertices[:] for t in me.loop_triangles])
np.savez(os.path.join(HERE, 'work', 'regions.npz'), finger=fing[tri].mean(1), hand=hand[tri].mean(1), tail=tail[tri].mean(1))
print('REGIONS finger>.5', int((fing[tri].mean(1) > .5).sum()), 'hand+finger>.5', int(((fing + hand)[tri].mean(1) > .5).sum()),
      'tail>.5', int((tail[tri].mean(1) > .5).sum()))
