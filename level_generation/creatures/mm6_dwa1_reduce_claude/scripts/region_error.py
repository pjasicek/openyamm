"""Rest-pose two-way error per region: source vertices -> candidate surface, labelled by a per-face label array of the
source (REA_LABELS, default work/groups_g1.npy with kept faces as -1 from REA_KEEP). Usage: blender -b -P region_error.py"""
import os, bpy, bmesh, numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
rig = bpy.data.objects['Rig']; rig.data.pose_position = 'REST'; bpy.context.view_layer.update()
src = bpy.data.objects['Body']
cls = np.load(os.path.join(HERE, 'work/classes.npy')); hs = np.load(os.path.join(HERE, 'work/headset.npy'))
reg = np.load(os.path.join(HERE, 'work/regions.npy')); comp = np.load(os.path.join(HERE, 'work/comp.npy'))
small = np.bincount(comp)[comp] <= 80
lab = np.full(len(cls), 'body_cloth', object)
lab[(~hs) & (cls == 1)] = 'body_skin'; lab[(~hs) & (cls == 9)] = 'body_metal'
lab[(~hs) & ((reg == 2) | (reg == 3))] = 'hands'
lab[hs & (cls == 1)] = 'face'; lab[hs & (cls == 6)] = 'eyes'; lab[hs & (cls == 2)] = 'hair'; lab[hs & (cls == 9)] = 'helmet'
lab[small] = 'small'
me = src.data; me.calc_loop_triangles()
vlab = np.empty(len(me.vertices), object)
for t, l in zip(me.loop_triangles, lab):
    for v in t.vertices: vlab[v] = l
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); return b
bs = ev(src); ts = BVHTree.FromBMesh(bs)
for cn in sorted(o.name for o in bpy.data.objects if o.name.startswith('Cand_')):
    bc = ev(bpy.data.objects[cn]); tc = BVHTree.FromBMesh(bc)
    d = np.array([tc.find_nearest(v.co)[3] for v in bs.verts]) * 1000
    out = []
    for l in ['face', 'eyes', 'hair', 'helmet', 'hands', 'body_skin', 'body_metal', 'body_cloth', 'small']:
        m = vlab == l
        if m.any(): out.append(f'{l} p99 {np.percentile(d[m], 99):.1f} max {d[m].max():.1f}')
    print('REGERR', cn, len(bc.faces), ' | '.join(out), flush=True)
    bc.free()
# where the cloth error sits on one candidate (REA_WHERE=Cand_60): per component and height band
cn = os.environ.get('REA_WHERE')
if cn:
    bc = ev(bpy.data.objects[cn]); tc = BVHTree.FromBMesh(bc)
    d = np.array([tc.find_nearest(v.co)[3] for v in bs.verts]) * 1000
    vcomp = np.zeros(len(me.vertices), int)
    for t, c in zip(me.loop_triangles, comp):
        for v in t.vertices: vcomp[v] = c
    z = np.array([v.co.z for v in bs.verts])
    for c in np.unique(vcomp):
        m = vcomp == c
        if m.sum() > 50: print('WHERE comp', c, 'verts', int(m.sum()), f'p99 {np.percentile(d[m], 99):.1f} p90 {np.percentile(d[m], 90):.1f} z {z[m].mean():.2f}', 'n>4mm', int((d[m] > 4).sum()))
    hi = np.argsort(-d)[:15]
    for i in hi: print('TOP', f'{d[i]:.1f}mm', vlab[i], 'comp', vcomp[i], tuple(round(c, 3) for c in bs.verts[i].co))
