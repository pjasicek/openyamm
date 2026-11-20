"""Design 2 (PeasantDF2b, one row) paints body and head in ONE 4K Meshy retexture (budget: 10 credits instead of 20).
Upload = the whole master with one UV layer: body and hand faces at their texture-pass UVMap scaled 0.5 into the
lower-left quadrant (Blender UV space), head faces (head = 1, hand = 0) at their head-upload UV (HeadUV / 0.8) scaled
0.5 into the lower-right quadrant. A 4K return thus holds the body paint at 2K on exactly the body upload's layout and
the head paint at 2K on exactly the head upload's layout (split_combined.py cuts them apart for the usual compose
scripts). Args: <texpass_head blend> <out upload glb>"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data; n = len(me.polygons)
hd = np.zeros(n, np.int32); hn = np.zeros(n, np.int32)
me.attributes['head'].data.foreach_get('value', hd); me.attributes['hand'].data.foreach_get('value', hn)
head = (hd == 1) & (hn == 0)
dup = body.copy(); dup.data = me.copy(); dup.modifiers.clear(); dup.parent = None
dup.matrix_world = body.matrix_world
bpy.context.scene.collection.objects.link(dup)
dm = dup.data
bu = dm.uv_layers['UVMap'].data; hu = dm.uv_layers['HeadUV'].data
new = []
for p in dm.polygons:
    for li in p.loop_indices:
        if head[p.index]:
            u, v = hu[li].uv; new.append((li, 0.5 + 0.5 * u / 0.8, 0.5 * v / 0.8))
        else:
            u, v = bu[li].uv; new.append((li, 0.5 * u, 0.5 * v))
for li, u, v in new:
    bu[li].uv = (u, v)
for name in [l.name for l in dm.uv_layers if l.name != 'UVMap']:
    dm.uv_layers.remove(dm.uv_layers[name])
dup.vertex_groups.clear()
for o in bpy.data.objects: o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=a[1], use_selection=True, export_format='GLB', export_yup=True, export_skins=False,
                          export_animations=False, export_materials='NONE', export_attributes=False)
print('COMBINED faces', n, 'head', int(head.sum()))
