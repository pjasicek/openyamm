"""Source vertices the candidate misses: over every 2nd frame of every clip, the distance from each posed source
vertex to the posed candidate (REA_CAND in work/ladder.blend); vertices over REA_ERR_MM keep the source faces within
REA_LOCK_R metres (rest pose) exactly in the next ladder. Usage: blender -b -P err_lock.py -- <base keep .npy> <out .npy>"""
import os, sys, bpy, bmesh, numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
base, out = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
cand = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_74')]
T = float(os.environ.get('REA_ERR_MM', '15')) / 1000; R = float(os.environ.get('REA_LOCK_R', '0.03'))
worst = np.zeros(len(src.data.vertices)); where = [''] * len(worst)
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world); return b
for act in bpy.data.actions:
    rig.animation_data.action = act; f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1, 2):
        sc.frame_set(f); bs, bc = ev(src), ev(cand); tc = BVHTree.FromBMesh(bc)
        d = np.array([tc.find_nearest(v.co)[3] for v in bs.verts])
        upd = d > worst; worst[upd] = d[upd]
        for i in np.flatnonzero(upd):
            where[i] = f'{act.name}:{f}'
        bs.free(); bc.free()
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
np.save(os.path.join(HERE, 'work', f'worst_{cand.name}.npy'), worst)
m = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); rest = m['verts']; faces = m['faces']
bad = np.flatnonzero(worst > T)
names = {g.index: g.name for g in src.vertex_groups}
for i in bad[np.argsort(-worst[bad])][:15]:
    g = max([g for g in src.data.vertices[i].groups if names[g.group] != 'ReduceProtect'], key=lambda g: g.weight)
    print(f'MISS {worst[i]*1000:.1f}mm at rest {np.round(rest[i], 3)} {names[g.group]} {where[i]}')
keep = np.load(base).copy(); n0 = int(keep.sum())
if len(bad):
    from mathutils.kdtree import KDTree
    t = KDTree(len(bad))
    for k, i in enumerate(bad):
        t.insert(rest[i], k)
    t.balance()
    near = np.array([t.find(p)[2] < R for p in rest])
    lock = near[faces].any(1)
    if os.environ.get('REA_LOCK_LABELS'):  # hydra: lock only body faces (label 0); locks inside the head groups
        g = np.load(os.path.join(HERE, 'work', 'groups.npy'))  # fragment them and raise their error
        lock &= np.isin(g, [int(x) for x in os.environ['REA_LOCK_LABELS'].split(',')])
    keep |= lock
np.save(os.path.join(HERE, out), keep); print('ERRLOCK', len(bad), 'vertices over', T * 1000, 'mm; kept', n0, '->', int(keep.sum()))
