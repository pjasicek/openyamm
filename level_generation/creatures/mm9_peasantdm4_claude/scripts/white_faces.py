"""List faces of the master's head set whose texels (HeadUV, sampled at corners and centroid) are near white
(diagnostic, 2026-11-02: white triangles on the cap). Args (Blender): <blend> <head basecolor png> [lum 225] [zmin 0.45]"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
im = bpy.data.images.load(a[1]); W, H = im.size
img = np.array(im.pixels[:]).reshape(H, W, 4)[::-1, :, :3] * 255.0
lum_t = float(a[2]) if len(a) > 2 else 225; zmin = float(a[3]) if len(a) > 3 else 0.45
ob = bpy.data.objects['Body']; bm = bmesh.new(); bm.from_mesh(ob.data)
hl = bm.faces.layers.int.get('head'); uv = bm.loops.layers.uv['HeadUV']
out = []
for f in bm.faces:
    if f[hl] != 1: continue
    c = f.calc_center_median()
    if c.z < zmin: continue
    uvs = [l[uv].uv for l in f.loops]
    pts = uvs + [sum(uvs, uvs[0] * 0) / len(uvs)]
    ls = []
    for p in pts:
        x = min(W - 1, max(0, int(p.x * W))); y = min(H - 1, max(0, int((1 - p.y) * H)))
        ls.append(img[y, x] @ [0.2126, 0.7152, 0.0722])
    area = abs((uvs[1] - uvs[0]).cross(uvs[2] - uvs[0])) / 2 * W * H
    if max(ls) > lum_t:
        out.append((f.index, round(c.x, 3), round(c.y, 3), round(c.z, 3), [round(v) for v in ls], round(area, 1)))
for o in out: print('WHITE', o)
print('WHITE n', len(out))
