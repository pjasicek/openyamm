"""Section of 'Body' (rest pose) by planes through the legs and forearms, for the boot-top and cuff investigation.
Each face cut by the plane gives a segment, labelled by kind: hand (hand attribute), and for body faces the region mask
at the face's UV (R tunic, G trousers, B boots, A belt) -> json for a PIL plot (section_plot.py).
Args (Blender): <blend> <region mask png> <out json>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
mw = body.matrix_world
img = bpy.data.images.load(a[1])
W, H = img.size
MK = np.array(img.pixels[:], np.float32).reshape(H, W, 4)
bm = bmesh.new(); bm.from_mesh(body.data); bm.faces.ensure_lookup_table()
lh, lk = bm.faces.layers.int['head'], bm.faces.layers.int['hand']
uvb = bm.loops.layers.uv['UVMap']
B = lambda n: rig.matrix_world @ rig.data.bones[n].head_local


def kind(f):
    if f[lk]:
        return 'hand'
    if f[lh]:
        return 'head'
    uv = sum((Vector(tuple(l[uvb].uv)) for l in f.loops), Vector((0, 0))) / len(f.loops)
    m = MK[min(H - 1, int(uv.y * H)), min(W - 1, int(uv.x * W))]
    return 'RGBA'[int(np.argmax(m))] if m.max() > 0.3 else 'none'


out = {}
planes = {}
for S in 'LR':
    k, c, ft = B(f'Bip01 {S} Calf'), B(f'Bip01 {S} Calf'), B(f'Bip01 {S} Foot')
    th = B(f'Bip01 {S} Thigh')
    planes[f'leg {S} sagittal'] = (k, Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)))
    planes[f'leg {S} frontal'] = (k, Vector((0, 1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1)))
    e, w = B(f'Bip01 {S} Forearm'), B(f'Bip01 {S} Hand')
    ax = (w - e).normalized()
    n1 = ax.cross(Vector((0, 0, 1))).normalized()
    planes[f'arm {S} a'] = (w, n1, ax, ax.cross(n1).normalized())
    planes[f'arm {S} b'] = (w, ax.cross(n1).normalized(), ax, n1)
for name, (o, n, u, v) in planes.items():
    segs = []
    for f in bm.faces:
        P = [mw @ x.co for x in f.verts]
        d = [(p - o).dot(n) for p in P]
        pts = []
        for i in range(len(P)):
            j = (i + 1) % len(P)
            if (d[i] > 0) != (d[j] > 0):
                t = d[i] / (d[i] - d[j])
                q = P[i].lerp(P[j], t)
                pts.append([(q - o).dot(u), (q - o).dot(v)])
        if len(pts) == 2:
            c = sum(P, Vector()) / len(P)
            if (c - o).length < 0.35:
                segs.append({'p': pts, 'k': kind(f), 'n': [round((mw.to_3x3() @ f.normal).dot(u), 3),
                                                           round((mw.to_3x3() @ f.normal).dot(v), 3)]})
    out[name] = segs
json.dump(out, open(a[2], 'w'))
print('SECTION', {k: len(v) for k, v in out.items()})
