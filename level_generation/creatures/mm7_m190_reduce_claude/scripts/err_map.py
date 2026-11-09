"""Per source vertex error of one ladder candidate: source vertex -> candidate surface distance over every 3rd frame of
every clip (and the rest frame Standing 0 separately) -> work/err_<cand>.npz (p95 over frames, max, rest).
Usage: blender -b -P err_map.py -- <ladder blend> <Cand_NN>"""
import os, sys, bpy, bmesh, numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', args[0]))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; c = bpy.data.objects[args[1]]
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); return b
D, tags = [], []
for act in bpy.data.actions:
    rig.animation_data.action = act; f0, f1 = (int(x) for x in act.frame_range)
    for fr in range(f0, f1 + 1, 3):
        sc.frame_set(fr); bs, bc = ev(src), ev(c); tc = BVHTree.FromBMesh(bc)
        D.append([tc.find_nearest(v.co)[3] for v in bs.verts]); tags.append(f'{act.name}:{fr}'); bs.free(); bc.free()
D = np.array(D); rest = D[tags.index('Standing:0')]
np.savez(os.path.join(HERE, 'work', f'err_{args[1]}.npz'), p95=np.percentile(D, 95, 0), max=D.max(0), rest=rest,
         worst=np.array(tags)[D.argmax(0)])
print('ERRMAP', args[1], 'p99 all', round(float(np.percentile(D, 99)) * 1000, 2), 'p99 rest', round(float(np.percentile(rest, 99)) * 1000, 2),
      'verts with rest > 4 mm', int((rest > .004).sum()), 'with p95 > 4 mm', int((np.percentile(D, 95, 0) > .004).sum()))
