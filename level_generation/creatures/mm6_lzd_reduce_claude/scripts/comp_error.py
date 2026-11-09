"""Per source component (work/comp.npy, faces of work/mesh_in.npz) error of a ladder candidate: source vertex ->
candidate surface distance at REA_FRAMES (default Standing:0,Attack:14,Death:9). Prints the worst components with
size, centre and dominant bone. Usage: REA_CAND=Cand_60 blender -b -P comp_error.py"""
import os, bpy, bmesh, numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
cand = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_60')]
d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); comp = np.load(os.path.join(HERE, 'work', 'comp.npy'))
vcomp = np.zeros(len(d['verts']), int); vcomp[d['faces'].reshape(-1)] = np.repeat(comp, 3)
names = {g.index: g.name for g in src.vertex_groups}
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); return b
err = np.zeros(len(d['verts']))
for spec in os.environ.get('REA_FRAMES', 'Standing:0,Attack:14,Death:9').split(','):
    clip, f = spec.split(':'); rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(int(f))
    bs, bc = ev(src), ev(cand); tc = BVHTree.FromBMesh(bc)
    err = np.maximum(err, [tc.find_nearest(v.co)[3] for v in bs.verts]); bs.free(); bc.free()
rows = []
for k in np.unique(vcomp):
    m = vcomp == k; e = err[m] * 1000
    vi = np.where(m)[0][np.argmax(e)]
    g = max(src.data.vertices[vi].groups, key=lambda g: g.weight)
    rows.append((np.percentile(e, 95), e.max(), k, int((comp == k).sum()), np.round(d['verts'][m].mean(0), 2), names[g.group]))
for r in sorted(rows, key=lambda r: -r[1])[:25]:
    print(f'COMP {r[2]:3d} faces {r[3]:5d} p95 {r[0]:5.1f} max {r[1]:5.1f} mm  cen {r[4]}  worst bone {r[5]}')
