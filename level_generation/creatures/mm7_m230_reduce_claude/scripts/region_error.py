"""Two-way surface error per source region for one ladder candidate over every 4th frame of every clip: each source
vertex's distance to the candidate and each candidate vertex's distance to the source, labelled by the region of the
nearest source vertex (work/lab_sets_p.npy per source face: 0 body, 1 face skin, 2 head rest, 3 gloves, 4 kept).
Prints p99 / max mm per region and the overall p99. Usage: blender -b -P region_error.py -- <Cand_NN> <labels .npy>"""
import os, sys, bpy, bmesh
import numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; cand = bpy.data.objects[a[0]]
d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); lab_f = np.load(os.path.join(HERE, a[1]))
vl = np.zeros((len(d['verts']), 5))
for k in range(3):
    np.add.at(vl, (d['faces'][:, k], lab_f), 1)
vlab = vl.argmax(1)
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); return b
errs = {r: [] for r in range(5)}
for act in bpy.data.actions:
    rig.animation_data.action = act
    if rig.animation_data.action_slot is None and act.slots:
        rig.animation_data.action_slot = act.slots[0]
    for fr in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 4):
        sc.frame_set(fr); bs = ev(src); bc = ev(cand); ts = BVHTree.FromBMesh(bs); tc = BVHTree.FromBMesh(bc)
        for v in bs.verts:
            errs[vlab[v.index]].append(tc.find_nearest(v.co)[3])
        for v in bc.verts:
            hit = ts.find_nearest(v.co)
            fi = hit[2]; errs[int(lab_f[fi])].append(hit[3])
        bs.free(); bc.free()
allv = np.concatenate([np.array(e) for e in errs.values() if e]) * 1000
print('REGION all p99 %.2f max %.2f' % (np.percentile(allv, 99), allv.max()))
for r, e in errs.items():
    if e:
        e = np.array(e) * 1000; print('REGION', r, 'n', len(e), 'p99 %.2f max %.2f share>p99 %.3f' % (np.percentile(e, 99), e.max(), (e > np.percentile(allv, 99)).sum() / max((allv > np.percentile(allv, 99)).sum(), 1)))
