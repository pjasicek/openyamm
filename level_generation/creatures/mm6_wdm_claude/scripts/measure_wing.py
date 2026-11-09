"""Measure wing landmarks on the raw Smart Topology mesh (left wing, +x): wrist (top of the leading edge), boundary
tips (local maxima of distance from the wrist along the wing outline) and the root strip. Prints numbers only."""
import bpy, bmesh, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
o = next(o for o in bpy.data.objects if o.type == 'MESH'); bpy.context.view_layer.objects.active = o; o.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([tuple(v.co) for v in o.data.vertices]); wing = np.load(os.path.join(HERE, 'work', 'wing_mask.npy'))
L = wing & (co[:, 0] > 0)
w = co[L]
top = w[np.argsort(-w[:, 2])[:8]]
print('TOPZ', top.round(3).tolist())
wrist = w[np.argmax(w[:, 2])]
print('WRIST', wrist.round(3))
# boundary of the wing region: vertices of L with a neighbour outside L or on open edges
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
idx = np.nonzero(L)[0]
bnd = [i for i in idx if any(not L[e.other_vert(bm.verts[i]).index] for e in bm.verts[i].link_edges) or bm.verts[i].is_boundary]
B = co[bnd]
d = np.linalg.norm(B - wrist, axis=1)
ang = np.arctan2(-(B[:, 2] - wrist[2]), B[:, 0] - wrist[0])
order = np.argsort(ang)
prof = list(zip(ang[order], d[order], B[order]))
# local maxima of distance over angle bins
bins = np.linspace(ang.min(), ang.max(), 60)
best = []
for a0, a1 in zip(bins[:-1], bins[1:]):
    m = (ang >= a0) & (ang < a1)
    if m.sum():
        j = np.argmax(np.where(m, d, -1)); best.append((float(ang[j]), float(d[j]), B[j]))
for i in range(1, len(best) - 1):
    if best[i][1] > best[i - 1][1] and best[i][1] >= best[i + 1][1] and best[i][1] > 0.12:
        print('TIP ang %.2f dist %.3f' % (best[i][0], best[i][1]), best[i][2].round(3))
inner = w[w[:, 0] < 0.08]
print('ROOT x', inner[:, 0].min().round(3), 'z range', inner[:, 2].min().round(3), inner[:, 2].max().round(3), 'y', inner[:, 1].min().round(3), inner[:, 1].max().round(3))
print('EXTENT', w.min(0).round(3), w.max(0).round(3))
