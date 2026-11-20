"""Per-region error of one ladder candidate: source vertex -> candidate surface distance, max over every 3rd frame of
every clip, grouped by the source vertex's dominant bone (and its head/hand/foot set). Writes work/verr_<cand>.npy.
Usage: blender -b -P region_error.py -- <ladder blend> <Cand_name>"""
import os, sys, bpy, bmesh, numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
blend, cn = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, blend))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; c = bpy.data.objects[cn]
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); return b
err = np.zeros(len(src.data.vertices)); where = [''] * len(err)
ONLY = os.environ.get('REA_ONLY')  # e.g. Standing:0 for the rest error alone
for act in bpy.data.actions:
    rig.animation_data.action = act
    f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1, 3):
        if ONLY and f'{act.name}:{f}' not in ONLY.split(','):
            continue
        sc.frame_set(f); bs, bc = ev(src), ev(c); tc = BVHTree.FromBMesh(bc)
        e = np.array([tc.find_nearest(v.co)[3] for v in bs.verts])
        upd = e > err; err[upd] = e[upd]
        for i in np.flatnonzero(upd): where[i] = f'{act.name}:{f}'
        bs.free(); bc.free()
np.save(os.path.join(HERE, 'work', f'verr_{cn}.npy'), err)
names = {g.index: g.name for g in src.vertex_groups}
gs = lambda v: [g for g in v.groups if names[g.group] != 'ReduceProtect']
dom = np.array([names[max(gs(v), key=lambda g: g.weight).group] if gs(v) else '-' for v in src.data.vertices])
print(f'ALL p99 {np.percentile(err, 99) * 1000:.2f} max {err.max() * 1000:.2f}')
rows = []
for b in np.unique(dom):
    m = dom == b; rows.append((np.percentile(err[m], 99) * 1000, b, m.sum(), err[m].max() * 1000))
for p, b, n, mx in sorted(rows, reverse=True)[:20]:
    print(f'REGION {b:16s} verts {n:5d} p99 {p:6.2f} max {mx:6.2f}')
top = np.argsort(-err)[:12]
for i in top:
    co = src.data.vertices[i].co
    print(f'TOP {err[i] * 1000:6.2f} mm {dom[i]:14s} at ({co.x:.3f},{co.y:.3f},{co.z:.3f}) {where[i]}')
