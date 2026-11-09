"""Slice the full Smart Topology mesh in the rig frame (x2.8566, +0.9 m z; ground 0, height 1.8) to place joints:
torso midline per height, arm and leg centroids per height on both sides (main island, wing vertices excluded)."""
import bpy, bmesh, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
o = next(o for o in bpy.data.objects if o.type == 'MESH'); bpy.context.view_layer.objects.active = o; o.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([tuple(v.co) for v in o.data.vertices]) * 2.8566 + np.array([0, 0, 0.8996])
wing = np.load(os.path.join(HERE, 'work', 'wing_mask.npy'))
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
seen = np.zeros(len(co), bool); comps = []
for v in bm.verts:
    if seen[v.index]: continue
    st = [v]; c = []; seen[v.index] = True
    while st:
        a = st.pop(); c.append(a.index)
        for e in a.link_edges:
            b = e.other_vert(a)
            if not seen[b.index]: seen[b.index] = True; st.append(b)
    comps.append(c)
main = np.zeros(len(co), bool); main[max(comps, key=len)] = True
B = co[main & ~wing]
print('MAIN', main.sum(), 'body', len(B))
for z in np.arange(1.80, 0.95, -0.05):
    t = B[(np.abs(B[:, 2] - z) < 0.02) & (np.abs(B[:, 0]) < 0.13)]
    if len(t) > 3:
        print('TORSO z %.2f x[%.3f %.3f] mid %.3f y[%.3f %.3f] mid %.3f' % (z, t[:, 0].min(), t[:, 0].max(), (t[:, 0].min() + t[:, 0].max()) / 2, t[:, 1].min(), t[:, 1].max(), (t[:, 1].min() + t[:, 1].max()) / 2))
for side, sg in (('L', 1), ('R', -1)):
    for z in np.arange(1.60, 0.55, -0.05):
        t = B[(np.abs(B[:, 2] - z) < 0.025) & (sg * B[:, 0] > 0.17)]
        if len(t) > 3:
            print('ARM%s z %.2f n %3d cx %.3f cy %.3f x[%.3f %.3f]' % (side, z, len(t), t[:, 0].mean(), t[:, 1].mean(), t[:, 0].min(), t[:, 0].max()))
    for z in np.arange(1.05, 0.10, -0.05):
        t = B[(np.abs(B[:, 2] - z) < 0.025) & (sg * B[:, 0] > 0.0) & (sg * B[:, 0] < 0.17)]
        if len(t) > 3:
            print('LEG%s z %.2f n %3d cx %.3f cy %.3f w %.3f' % (side, z, len(t), t[:, 0].mean(), t[:, 1].mean(), t[:, 0].max() - t[:, 0].min()))
