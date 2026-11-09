"""Plot a thin slab section of 'Body' (|axis - value| < half) as a PNG with the given bones' heads marked.
Args: <blend> <out png> <axis x|y|z> <value> <half> <u0,u1,v0,v1 window> [bone,bone...]"""
import bpy, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
from PIL import Image, ImageDraw
b = bpy.data.objects['Body']; me = b.data
co = np.array([tuple(b.matrix_world @ v.co) for v in me.vertices])
pc = np.array([d.value for d in me.attributes['piece'].data]) if 'piece' in me.attributes else np.zeros(len(co), int)
ax = 'xyz'.index(argv[2]); val = float(argv[3]); half = float(argv[4])
u0, u1, v0, v1 = [float(x) for x in argv[5].split(',')]
other = [i for i in range(3) if i != ax]
S = 800
img = Image.new('RGB', (S, int(S * (v1 - v0) / (u1 - u0))), (30, 30, 36))
d = ImageDraw.Draw(img)
def px(u, v):
    return ((u - u0) / (u1 - u0) * S, img.height - (v - v0) / (v1 - v0) * img.height)
me.calc_loop_triangles()
for t in me.loop_triangles:
    p = co[list(t.vertices)]
    s = p[:, ax] - val
    if s.min() > 0 or s.max() < 0:
        continue
    pts = []
    for a, c in ((0, 1), (1, 2), (2, 0)):
        if (s[a] > 0) != (s[c] > 0):
            f = s[a] / (s[a] - s[c])
            q = p[a] + f * (p[c] - p[a])
            pts.append(px(q[other[0]], q[other[1]]))
    if len(pts) == 2:
        col = (255, 200, 80) if pc[t.vertices[0]] else (220, 220, 220)
        d.line(pts, fill=col, width=2)
arm = bpy.data.objects.get('MM9_Rig')
if arm and len(argv) > 6:
    for n in argv[6].split(','):
        h = arm.matrix_world @ arm.data.bones[n].head_local
        x, y = px(h[other[0]], h[other[1]])
        d.ellipse((x - 4, y - 4, x + 4, y + 4), outline=(255, 60, 60)); d.text((x + 5, y - 5), n, fill=(255, 90, 90))
# grid every 0.05
g = 0.05
import math
for k in range(int(math.floor(u0 / g)), int(math.ceil(u1 / g)) + 1):
    x, _ = px(k * g, v0); d.line([(x, 0), (x, img.height)], fill=(60, 60, 70)); d.text((x + 2, 2), '%.2f' % (k * g), fill=(120, 120, 140))
for k in range(int(math.floor(v0 / g)), int(math.ceil(v1 / g)) + 1):
    _, y = px(u0, k * g); d.line([(0, y), (S, y)], fill=(60, 60, 70)); d.text((2, y + 2), '%.2f' % (k * g), fill=(120, 120, 140))
img.save(argv[1])
print('SECTION', argv[1])
