"""Where a ladder's error sits, per Kira part: two-way distances (candidate vertices -> source surface, labelled by the nearest source
face's part; source vertices -> candidate surface, labelled by their own faces' part) at the given frames, p99 and max per part, plus
the worst 5 points with positions. Usage: blender -b -P part_error.py -- <ladder blend> <Cand_NN,...> <clip:frame,...>"""
import sys, bpy, bmesh
import numpy as np
from mathutils.bvhtree import BVHTree
blend, cands, frames = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
info = np.load('work/faces_info.npz'); part = info['part']
src.data.calc_loop_triangles(); tri_part = part  # loop triangles = dump order
vpart = np.zeros(len(src.data.vertices), int)
for t in src.data.loop_triangles:
    for v in t.vertices: vpart[v] = part[t.index]
NAMES = {0: 'hands', 1: 'armour', 5: 'legs', 7: 'skirt', 9: 'belt', 10: 'medal', 11: 'kneecop', 12: 'lames', 13: 'tasset', 20: 'face', 21: 'hair', 22: 'eyes', 23: 'braid'}
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); return b
for spec in frames.split(','):
    clip, f = spec.split(':'); rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(int(f))
    bs = ev(src); bs.faces.ensure_lookup_table()
    # bmesh faces of an all-triangle mesh keep the polygon order = loop triangle order
    ts = BVHTree.FromBMesh(bs)
    for cn in cands.split(','):
        bc = ev(bpy.data.objects[cn]); tc = BVHTree.FromBMesh(bc)
        d1, p1, pos1 = [], [], []
        for v in bc.verts:
            co, _, fi, dist = ts.find_nearest(v.co); d1.append(dist); p1.append(part[fi]); pos1.append(tuple(v.co))
        d2 = np.array([tc.find_nearest(v.co)[3] for v in bs.verts])
        d1, p1, pos1 = np.array(d1) * 1000, np.array(p1), np.array(pos1); d2 *= 1000
        row = []
        for p in sorted(NAMES):
            a = np.r_[d1[p1 == p], d2[vpart == p]]
            if len(a) and a.max() > 1.0:
                row.append(f'{NAMES[p]} p99 {np.percentile(a, 99):.1f} max {a.max():.1f}')
        print(f'{spec} {cn}: ' + ' | '.join(row))
        for i in np.argsort(-d1)[:5]:
            print('   cand->src', round(float(d1[i]), 1), 'mm', NAMES[int(p1[i])], np.round(pos1[i], 3).tolist())
        bc.free()
    bs.free()
