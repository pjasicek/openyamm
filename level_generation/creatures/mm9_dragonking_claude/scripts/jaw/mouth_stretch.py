"""Mouth cavity stretch over the clips: per mouth triangle, edge-length ratio and sqrt(area) ratio against the bind
pose, at every 30 fps frame of the clips that open the mouth. Args: -- <anim blend> <out json>"""
import bpy, bmesh, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
sc = bpy.context.scene
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.find_armature() == rig)
me = body.data
mouth = np.zeros(len(me.polygons), np.int32); me.attributes['mouth'].data.foreach_get('value', mouth)
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces[:])
ml = bm.faces.layers.int['mouth']
T = np.array([[v.index for v in f.verts] for f in bm.faces if f[ml]]); bm.free()


def posed():
    dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); m = ev.to_mesh()
    P = np.array([tuple(v.co) for v in m.vertices]); ev.to_mesh_clear(); return P


def metrics(P):
    e = np.stack([np.linalg.norm(P[T[:, i]] - P[T[:, (i + 1) % 3]], axis=1) for i in range(3)], 1)
    ar = 0.5 * np.linalg.norm(np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]), axis=1)
    return e, ar


rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
e0, a0 = metrics(posed())
ok = a0 > 1e-7
out = {}
for clip in ('Fidget', 'Cast', 'AttackRanged', 'AttackMelee', 'Hit', 'Taunt', 'Death', 'Land'):
    act = bpy.data.actions[clip]; rig.animation_data.action = act
    worst = None
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
        sc.frame_set(f)
        e, ar = metrics(posed())
        er = (e / np.maximum(e0, 1e-6))[ok].max(1)
        sr = np.sqrt(ar[ok] / a0[ok])
        rec = {'frame': f, 's': round(f / 30, 3), 'edge_p99': round(float(np.percentile(er, 99)), 2), 'edge_max': round(float(er.max()), 2),
               'area_sqrt_p99': round(float(np.percentile(sr, 99)), 2), 'area_sqrt_max': round(float(sr.max()), 2),
               'over2_edge_tris': int((er > 2).sum())}
        if worst is None or rec['edge_p99'] > worst['edge_p99']:
            worst = rec
    out[clip] = worst
    print(clip, worst)
out['mouth_triangles'] = int(ok.sum())
json.dump(out, open(a[1], 'w'), indent=1)
# where: centroids (bind) of the triangles over 2x at the worst Death frame, binned by y
if '--where' in a:
    rig.animation_data.action = bpy.data.actions['Death']; sc.frame_set(out['Death']['frame'])
    e, ar = metrics(posed()); er = (e / np.maximum(e0, 1e-6)).max(1)
    rig.animation_data.action = None
    for b in rig.pose.bones: b.matrix_basis.identity()
    bpy.context.view_layer.update(); P0 = posed()
    C = P0[T].mean(1); bad = (er > 2) & ok
    upw_ = {}
    vg = {g.index: g.name for g in body.vertex_groups}
    U = {'Xheadpiv', 'Xhead', 'Xjawbase', 'Xtopfinpiv', 'Xtopfinpiv01', 'Xfinpiv', 'Xfinpiv01'}
    uw = np.array([sum(g.weight for g in v.groups if vg[g.group] in U) for v in me.vertices])
    tw = uw[T]
    print('BAD', int(bad.sum()), 'y hist', np.histogram(C[bad, 1], bins=[-5.4, -4.5, -4.0, -3.6, -3.4, -3.2, -3.0, -2.8])[0].tolist())
    print('BAD weight spread (max-min upper w per tri) mean', float((tw.max(1) - tw.min(1))[bad].mean()), 'all', float((tw.max(1) - tw.min(1))[ok].mean()))
    for c, r, w in sorted(zip(C[bad].round(3).tolist(), er[bad].round(2).tolist(), tw[bad].round(2).tolist()), key=lambda x: -x[1])[:12]:
        print(' ', c, r, w)
