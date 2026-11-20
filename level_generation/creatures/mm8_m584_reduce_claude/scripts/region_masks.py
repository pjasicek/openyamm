"""Per-face region labels of the rest mesh (work/source.blend, face order of dump_mesh.py) from the skin weights:
wings (Wing_/Feather_ bones: 2 closed wing cores, 36 flight feathers, 144 coverts; the production LODs kept them
whole because feather shells open gaps at any cut), hands and fingers (fitted grip on the polearm shaft), feet and
toes (talons). Writes work/region.npy (0 rest, 1 wing, 2 hand, 3 foot) and prints counts."""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
o = bpy.data.objects['Body']; me = o.data; me.calc_loop_triangles()
name = {g.index: g.name for g in o.vertex_groups}
def share(pred):
    return np.array([sum(g.weight for g in v.groups if pred(name[g.group])) for v in me.vertices])
wing = share(lambda n: n.startswith(('Wing_', 'Feather_')))
hand = share(lambda n: 'Hand' in n and not n.startswith('Wing_') or 'Finger' in n)
foot = share(lambda n: 'Foot' in n or 'Toe' in n)
tri = np.array([t.vertices[:] for t in me.loop_triangles])
lab = np.zeros(len(tri), np.int32)
lab[foot[tri].mean(1) > .5] = 3
lab[hand[tri].mean(1) > .5] = 2
lab[wing[tri].mean(1) > .5] = 1
np.save(os.path.join(HERE, 'work', 'region.npy'), lab)
print('REGION', {k: int((lab == k).sum()) for k in range(4)})
