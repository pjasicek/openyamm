"""Create MeshyNoSkin (skin-coloured faces removed by base-colour sample) inside work/meshy_fitted.blend."""
import bpy, bmesh, sys, os, colorsys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
m = bpy.data.objects['MeshyDetail']
for o in list(bpy.data.objects):
    if o.name.startswith('MeshyNoSkin'): bpy.data.objects.remove(o, do_unlink=True)
img = bpy.data.images.load(os.path.join(common.PROJECT, 'meshy/detail_source_v1/texture_urls_0_base_color.png'))
W, H = img.size
px = np.array(img.pixels[:], dtype=np.float32).reshape(H, W, 4)[:, :, :3]
me = m.data
uv = me.uv_layers.active.data
n = len(me.polygons)
loop_uv = np.zeros(len(me.loops) * 2, dtype=np.float32); uv.foreach_get('uv', loop_uv); loop_uv = loop_uv.reshape(-1, 2)
starts = np.zeros(n, dtype=np.int32); me.polygons.foreach_get('loop_start', starts)
cu = (loop_uv[starts] + loop_uv[starts + 1] + loop_uv[starts + 2]) / 3
xi = np.clip((cu[:, 0] % 1) * W, 0, W - 1).astype(int); yi = np.clip((cu[:, 1] % 1) * H, 0, H - 1).astype(int)
rgb = px[yi, xi] ** (1 / 2.2)  # linear -> approx sRGB
r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
mx = rgb.max(1); mn = rgb.min(1); sat = (mx - mn) / np.maximum(mx, 1e-4)
skin = (r > g) & (g > b) & (mx > 0.55) & (sat > 0.18) & (sat < 0.62) & ((r - g) > 0.06)
print('SKIN faces', skin.sum(), 'of', n)
dup = m.copy(); dup.data = m.data.copy(); dup.name = 'MeshyNoSkin'
bpy.context.scene.collection.objects.link(dup)
bm = bmesh.new(); bm.from_mesh(dup.data); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.faces[i] for i in np.nonzero(skin)[0]], context='FACES')
bm.to_mesh(dup.data); bm.free()
dup.hide_render = False; m.hide_render = True
bpy.ops.wm.save_mainfile()
common.workbench_clay(bpy.context.scene)
common.render_views(os.path.join(common.REVIEW, 'meshy_noskin'), 0.8, 1.7, views=('front', 'left'), resolution=(600, 600))
