"""UV parity of the two Meshy returns against the master (enable_original_uv): every upload corner must come back at
the same position with the same UV. In: work/master_r45.blend, meshy/{body,head}_texture_r45/model_urls_glb.glb.
Out: work/texture_uv_parity.json (asserts: no unmatched corner, < 0.2 % changed)."""
import bpy, json, os
import numpy as np
from mathutils import Vector, kdtree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'master_r45.blend'))
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
o = bpy.data.objects['Body']; me = o.data; T = [o.matrix_world @ v.co for v in me.vertices]
head = [a.value for a in me.attributes['head'].data]; report = {}
me.calc_loop_triangles()
body_layer = 'UVMeshy' if 'UVMeshy' in me.uv_layers else 'UVMap'   # the Meshy layout survives a re-pack (tex_relayout.py)
for label, layer, keep in [('body', body_layer, lambda f: True), ('head', 'HeadUV', lambda f: head[f] == 1)]:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy', f'{label}_texture_r45', 'model_urls_glb.glb'))
    src = next(x for x in bpy.data.objects if x not in before and x.type == 'MESH'); sm = src.data
    S = np.array([src.matrix_world @ v.co for v in sm.vertices]); U = np.array([t[:] for i, t in enumerate(T)])
    ids = sorted({vi for t in me.loop_triangles if keep(t.polygon_index) for vi in t.vertices}); U = U[ids]
    scale = np.ptp(U, 0).max() / np.ptp(S, 0).max(); S = S * scale + (U.max(0) + U.min(0)) / 2 - (S.max(0) + S.min(0)) / 2 * scale
    tree = kdtree.KDTree(len(sm.loops)); uv = sm.uv_layers.active.data
    for li, loop in enumerate(sm.loops): tree.insert(Vector(S[loop.vertex_index]), li)
    tree.balance(); count = unmatched = changed = 0; worst = 0
    for t in me.loop_triangles:
        if not keep(t.polygon_index): continue
        for li, vi in zip(t.loops, t.vertices):
            old = me.uv_layers[layer].data[li].uv; near = tree.find_range(T[vi], 2e-4)
            if not near: unmatched += 1; continue
            _, j, d = min(near, key=lambda q: (uv[q[1]].uv - old).length); worst = max(worst, (uv[j].uv - old).length)
            changed += (uv[j].uv - old).length > 1e-3; count += 1
    report[label] = {'corners': count, 'unmatched': unmatched, 'changed': changed, 'max_uv_delta': worst}
    for x in list(bpy.data.objects):
        if x not in before: bpy.data.objects.remove(x, do_unlink=True)
json.dump(report, open(os.path.join(HERE, 'work', 'texture_uv_parity.json'), 'w'), indent=1); print('UV_PARITY', report)
for k, r in report.items():
    assert r['unmatched'] == 0 and r['changed'] < .002 * r['corners'], (k, r)
