"""Collapsed-UV patch faces take a skin texel (face pass 2026-11-02): cheek_patch.py / bridge_hole.py give a new face one texel
per UV layer (the centre of the nearest old face); where that face was the beard sheet the patch showed as a white sliver on
the cheek. Every head face whose HeadUV area is ~0 takes, on HeadUV, the centre UV of the nearest face (within 2.5 cm, real
UV area) whose centre texel in the head colour map is skin (r > g > b, saturation 0.25-0.8, luminance > 90).
Args: <in blend> <out blend> <head basecolor png>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
img = bpy.data.images.load(a[2]); W, H = img.size
px = np.array(img.pixels[:]).reshape(H, W, 4)[..., :3] * 255     # bottom row first
def texel(uv):
    x = int(min(max(uv.x, 0), 0.9999) * W); y = int(min(max(uv.y, 0), 0.9999) * H)
    return px[y, x]
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
L = bm.loops.layers.uv['HeadUV']; hd = bm.faces.layers.int.get('head')
def area(f):
    u = [l[L].uv for l in f.loops]
    return abs((u[1] - u[0]).cross(u[2] - u[0])) / 2 if len(u) == 3 else 1
cands = []
for f in bm.faces:
    if hd and not f[hd]:
        continue
    if area(f) < 1e-9:
        continue
    cu = sum((l[L].uv for l in f.loops), Vector((0, 0))) / len(f.loops)
    c = texel(cu); mx, mn = c.max(), c.min(); sat = (mx - mn) / max(mx, 1); lum = c @ [0.299, 0.587, 0.114]
    if c[0] > c[1] > c[2] and 0.25 < sat < 0.8 and lum > 90:
        cands.append((f.calc_center_median(), cu))
kd = KDTree(len(cands))
for i, (p, _) in enumerate(cands):
    kd.insert(p, i)
kd.balance()
fixed = 0
for f in bm.faces:
    if (hd and not f[hd]) or area(f) >= 1e-9:
        continue
    hit = kd.find(f.calc_center_median())
    if hit[0] is None or hit[2] > 0.025:
        continue
    for l in f.loops:
        l[L].uv = cands[hit[1]][1]
    fixed += 1
bm.to_mesh(me); me.update()
print('PATCH_UV fixed', fixed, 'skin candidates', len(cands))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
