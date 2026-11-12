"""Dump the v3 master (mm6_pfem_claude/work/final_v3_head_repaired.blend, the body the user called good) at rest to an npz:
co (world, Blender frame), tri, per-triangle part / head / material / colour (base colour sampled at the centroid UV), per-vertex v3 weights
(top 4), v3 joint heads. Args: <master blend> <out npz>"""
import bpy, sys, json
import numpy as np
SRC, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=SRC)
o = bpy.data.objects['Peasant']; rig = bpy.data.objects['Peasant_Rig']
for m in o.modifiers: m.show_viewport = False
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = o.data; me.calc_loop_triangles()
mw = np.array(o.matrix_world)
co = np.array([v.co[:] for v in me.vertices]); co = co @ mw[:3, :3].T + mw[:3, 3]
lt = me.loop_triangles
tri = np.array([t.vertices[:] for t in lt]); tp = np.array([t.polygon_index for t in lt])
fpart = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fpart)
fhead = np.zeros(len(me.polygons), int); me.attributes['head'].data.foreach_get('value', fhead)
fmat = np.array([p.material_index for p in me.polygons])
uvl = me.uv_layers['UVMap'].data
uv = np.array([[uvl[l].uv[:] for l in t.loops] for t in lt])          # (T, 3, 2)
imgs = {}
for k, mat in enumerate(me.materials):
    node = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    lk = node.inputs['Base Color'].links if node else []
    im = None
    while lk:
        n = lk[0].from_node
        if n.type == 'TEX_IMAGE': im = n.image; break
        lk = next((i.links for i in n.inputs if i.links), [])
    if im is not None:
        w, h = im.size; px = np.array(im.pixels[:]).reshape(h, w, 4)
        imgs[k] = px; print('IMG', k, mat.name, im.name, w, h)
col = np.zeros((len(tri), 3))
for k, px in imgs.items():
    m = fmat[tp] == k; h, w = px.shape[:2]
    for bary in ((1/3, 1/3, 1/3), (0.6, 0.2, 0.2), (0.2, 0.6, 0.2), (0.2, 0.2, 0.6)):
        u = (uv[m] * np.array(bary)[None, :, None]).sum(1)
        x = np.clip((u[:, 0] % 1) * w, 0, w - 1).astype(int); y = np.clip((u[:, 1] % 1) * h, 0, h - 1).astype(int)
        col[m] += px[y, x, :3] / 4
bones = [g.name for g in o.vertex_groups]
W = np.zeros((len(co), 4), np.float32); WI = np.zeros((len(co), 4), np.int32)
for v in me.vertices:
    gs = sorted(((g.weight, g.group) for g in v.groups), reverse=True)[:4]
    for k, (w, gi) in enumerate(gs): W[v.index, k] = w; WI[v.index, k] = gi
J = {b.name: list(rig.matrix_world @ b.head_local) for b in rig.data.bones}
JT = {b.name: list(rig.matrix_world @ b.tail_local) for b in rig.data.bones}
np.savez(OUT, co=co, tri=tri, part=fpart[tp], head=fhead[tp], mat=fmat[tp], col=col, uv=uv, W=W, WI=WI, bones=np.array(bones),
         joints=json.dumps(J), tails=json.dumps(JT), parts=bpy.context.scene['pfem_parts'])
print('EXTRACT', len(co), len(tri), 'bounds', co.min(0).round(3).tolist(), co.max(0).round(3).tolist())
