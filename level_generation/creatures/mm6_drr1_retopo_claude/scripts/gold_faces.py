"""Faces of the installed master whose texture colour (body set, at the face centre UV) is gold, on the legs/flanks
(|x| > 3 cm, 4-22 cm high): position, area, and the face's UV island size."""
import os, bpy, bmesh, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(os.path.dirname(HERE), 'mm6_drr1_claude')
bpy.ops.wm.open_mainfile(filepath=os.path.join(W, 'export', 'mm6_wyrm.blend'))
o = bpy.data.objects['Wyrm']; me = o.data
img = bpy.data.images.load(os.path.join(W, 'textures', 'wyrm_basecolor.png'))
n = img.size[0]; px = np.array(img.pixels[:], np.float32).reshape(n, n, 4)
uv = me.uv_layers.active.data
out = []
for p in me.polygons:
    if p.material_index != 0: continue
    c = p.center
    if abs(c.x) < .03 or not (.04 < c.z < .22): continue
    u = sum((uv[l].uv for l in p.loop_indices), uv[p.loop_indices[0]].uv * 0) / len(p.loop_indices)
    col = px[min(n - 1, int(u.y * n)), min(n - 1, int(u.x * n)), :3]
    r, g, b = col
    if r > .35 and g > .3 and b < .6 * g and r > .7 * g:      # gold/yellow
        out.append((round(c.x, 3), round(c.y, 3), round(c.z, 3), round(p.area * 1e4, 2), tuple(round(float(x), 2) for x in col)))
print('GOLDFACES', len(out))
for r in sorted(out, key=lambda t: t[1])[:60]: print('GF', r)
