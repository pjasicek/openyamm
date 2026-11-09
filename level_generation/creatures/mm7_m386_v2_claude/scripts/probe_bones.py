"""Ladder error by bone: for each candidate (REA_CANDS) and frame (REA_FRAMES, 'rest' = bind pose), two-way vertex ->
surface distances, grouped by the dominant bone of the (nearest) source vertex: count over 3 mm, p99 and max.
Usage: blender -b -P probe_bones.py (work/ladder.blend)"""
import os, bpy, bmesh
import numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import kdtree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', os.environ.get('REA_BLEND', 'ladder.blend')))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
names = {g.index: g.name for g in src.vertex_groups}
dom = [names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '-' for v in src.data.vertices]
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); return b
for fr in os.environ.get('REA_FRAMES', 'rest,Hit:3').split(','):
    if fr == 'rest':
        rig.animation_data.action = None
        for b in rig.pose.bones: b.matrix_basis.identity()
        bpy.context.view_layer.update()
    else:
        c, f = fr.split(':'); rig.animation_data.action = bpy.data.actions[c]; sc.frame_set(int(f))
    bs = ev(src); ts = BVHTree.FromBMesh(bs); kd = kdtree.KDTree(len(bs.verts))
    for v in bs.verts: kd.insert(v.co, v.index)
    kd.balance()
    for cn in os.environ.get('REA_CANDS', 'Cand_50').split(','):
        bc = ev(bpy.data.objects[cn]); tc = BVHTree.FromBMesh(bc)
        rows = [(tc.find_nearest(v.co)[3], dom[v.index]) for v in bs.verts]
        rows += [(ts.find_nearest(v.co)[3], dom[kd.find(v.co)[1]]) for v in bc.verts]
        by = {}
        for d, b in rows: by.setdefault(b, []).append(d * 1000)
        out = sorted(((k, len(v), int((np.array(v) > 3).sum()), float(np.percentile(v, 99)), float(max(v))) for k, v in by.items()), key=lambda x: -x[2])
        print('PROBE', fr, cn, ' | '.join(f'{k} n{n} >3mm:{o} p99 {p:.1f} max {m:.1f}' for k, n, o, p, m in out[:9]), flush=True)
        bc.free()
    bs.free()
