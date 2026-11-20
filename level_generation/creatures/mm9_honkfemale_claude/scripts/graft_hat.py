"""Replace Meshy's own hat (a thin stalk for the goose) by the dedicated goose hat mesh (hats in ../mm9_honkmale_claude): old hat part deleted,
new one decimated, scaled to the old brim width, seated on the old brim, 100 % on Bip01 Head. Faces keep Body's layers.
Args (Blender): <in blend> <hat glb> <out blend> <report json> [hat_tris=2000] [z_min=0.72]"""
import bpy, bmesh, json, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
opt = dict(x.split('=', 1) for x in a[4:])
bpy.ops.wm.open_mainfile(filepath=a[0])
b = bpy.data.objects['Body']; me = b.data; M = b.matrix_world; rig = b.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
CO = np.array([tuple(M @ v.co) for v in me.vertices])
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = -np.ones(len(bm.verts), np.int32); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0: comp[y.index] = cid; st.append(y)
    cid += 1
zm = float(opt.get('z_min', 0.72))
hat = [k for k in range(cid) if np.median(CO[comp == k, 2]) > zm and (comp == k).sum() > 100 and CO[comp == k, 2].max() > 0.9]
assert len(hat) == 1, hat
m = comp == hat[0]
lo, hi = CO[m].min(0), CO[m].max(0)
# the brim: widest ring in the lower quarter of the hat
low = m & (CO[:, 2] < lo[2] + 0.25 * (hi[2] - lo[2]))
w = np.ptp(CO[low, 0]); d = np.ptp(CO[low, 1]); c = 0.5 * (CO[low].min(0) + CO[low].max(0))
rep = {'old_hat': {'lo': lo.round(3).tolist(), 'hi': hi.round(3).tolist(), 'brim_w': float(w), 'brim_d': float(d), 'verts': int(m.sum())}}
bmesh.ops.delete(bm, geom=[v for v in bm.verts if m[v.index]], context='VERTS')
bm.to_mesh(me); bm.free()
ex = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=a[1])
new = [o for o in bpy.data.objects if o not in ex]
h = next(o for o in new if o.type == 'MESH')
for o in new:
    if o is not h:
        for ch in o.children:
            mt = ch.matrix_world.copy(); ch.parent = None; ch.matrix_world = mt
        bpy.data.objects.remove(o)
for o in bpy.data.objects: o.select_set(o == h)
bpy.context.view_layer.objects.active = h
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
tris = sum(len(p.vertices) - 2 for p in h.data.polygons)
dm = h.modifiers.new('D', 'DECIMATE'); dm.ratio = min(1, float(opt.get('hat_tris', 2000)) / tris); dm.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier=dm.name)
hc = np.array([tuple(v.co) for v in h.data.vertices])
s = max(w, d) / max(np.ptp(hc[:, 0]), np.ptp(hc[:, 1]) * 0.98) if False else w / np.ptp(hc[:, 0])
hc2 = hc * s
hc2 += np.array([c[0], c[1], lo[2]]) - np.array([0.5 * (hc2[:, 0].min() + hc2[:, 0].max()), 0.5 * (hc2[:, 1].min() + hc2[:, 1].max()), hc2[:, 2].min()])
Mi = M.inverted()
for v, p in zip(h.data.vertices, hc2):
    v.co = Mi @ Vector(p.tolist())
h.vertex_groups.clear()
g = h.vertex_groups.new(name='Bip01 Head'); g.add(list(range(len(h.data.vertices))), 1.0, 'REPLACE')
h.data.materials.clear()
for ln in [l.name for l in h.data.uv_layers]:
    h.data.uv_layers.remove(h.data.uv_layers[ln])
rep['new_hat'] = {'scale': float(s), 'tris': sum(len(p.vertices) - 2 for p in h.data.polygons), 'lo': hc2.min(0).round(3).tolist(), 'hi': hc2.max(0).round(3).tolist()}
for o in bpy.data.objects: o.select_set(o in (h, b))
bpy.context.view_layer.objects.active = b
h.matrix_world = M.copy()
bpy.ops.object.join()
json.dump(rep, open(a[3], 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=a[2])
print('GRAFTHAT', json.dumps(rep))
