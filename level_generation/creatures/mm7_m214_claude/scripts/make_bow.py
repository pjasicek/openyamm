"""Bow and arrow meshes for m214 in prop space, modelled from the HD bow reference (references_hd/bow.png, side view,
string on image left) and textured by planar projection of that image. Writes work/props.blend with objects
BowMesh (UVMap, material 'Bow'), ArrowMesh (material 'Arrow') and prints triangle counts and bow numbers to
work/bow.json.
Bow prop space: +Y up the bow (upper limb), origin at the grip centre, bow plane = XY with the string toward -X,
+Z = the limb width. 1.15 m tip to tip (native: shoulder to below the knee of a 1.75 m archer).
Limb: per image row the limb run (not the string column) gives the centre line and the in-plane thickness
(x 0.65: the generated limbs are chunky); the width across (Z) tapers from 2.6 cm at the grip to 1.1 cm at the tips;
8-sided elliptic section, one ring per 18 px, tips closed with a small cap ring.
Arrow prop space: +Y toward the head, origin at the nock; 0.74 m shaft r 4 mm (6 sides), 7 cm steel head (4-sided
diamond), three 11 cm fletching vanes (two-sided quads). Arrow texture: textures/props/arrow.png (written here).
String endpoints (bow space) for the skinned string are stored in work/bow.json."""
import bpy, bmesh, os, json, math
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(HERE, *p)
os.makedirs(R('textures', 'props'), exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
img = bpy.data.images.load(R('references_hd', 'bow.png'))
W_, H_ = img.size
px = np.array(img.pixels[:]).reshape(H_, W_, 4)[::-1]          # row 0 = image top
al = px[:, :, 3] > 0.5
ys, xs = np.where(al)
top, bot = ys.min(), ys.max()
M = 1.15 / (bot - top)                                         # metres per pixel
GRIP_ROW = 760
cols = []
for r in range(top + 2, bot - 1, 18):
    c = np.where(al[r])[0]
    if not len(c):
        continue
    runs = np.split(c, np.where(np.diff(c) > 1)[0] + 1)
    limb = [x for x in runs if x[0] > 415 or len(x) > 14] or [max(runs, key=len)]
    run = max(limb, key=len)
    cols.append((r, (run[0] + run[-1]) / 2.0, len(run)))
GRIP_X = np.interp(GRIP_ROW, [c[0] for c in cols], [c[1] for c in cols])
STRING_X = 404.0


def to_bow(x, r):
    return Vector(((x - GRIP_X) * M, (GRIP_ROW - r) * M, 0.0))


def uv_of(x, r):
    return (x / W_, 1.0 - r / H_)


bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
SIDES = 8
pts = [to_bow(x, r) for r, x, _ in cols]
rings = []
n = len(cols)
for i, (r, x, wpx) in enumerate(cols):
    t = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]; t.normalize()
    nrm = Vector((-t.y, t.x, 0.0))                              # in-plane normal
    th = max(wpx * M * 0.65, 0.006) / 2
    d = abs((GRIP_ROW - r) * M) / 0.575                         # 0 at the grip, 1 at the tips
    wz = (0.026 - 0.015 * min(d, 1.0) ** 1.5) / 2
    ring = []
    for k in range(SIDES):
        a = 2 * math.pi * k / SIDES
        p = pts[i] + nrm * (math.cos(a) * th) + Vector((0, 0, math.sin(a) * wz))
        v = bm.verts.new(p)
        ring.append((v, uv_of(x + math.cos(a) * th / M, r)))
    rings.append(ring)
for a, b in zip(rings[:-1], rings[1:]):
    for k in range(SIDES):
        k2 = (k + 1) % SIDES
        f = bm.faces.new((a[k][0], a[k2][0], b[k2][0], b[k][0]))
        for lp, (v, uv) in zip(f.loops, (a[k], a[k2], b[k2], b[k])):
            lp[uvl].uv = uv
for ring, flip in ((rings[0], True), (rings[-1], False)):
    c = sum((v.co for v, _ in ring), Vector()) / SIDES
    cv = bm.verts.new(c)
    for k in range(SIDES):
        k2 = (k + 1) % SIDES
        vs = (ring[k][0], ring[k2][0], cv) if not flip else (ring[k2][0], ring[k][0], cv)
        f = bm.faces.new(vs)
        for lp in f.loops:
            lp[uvl].uv = ring[k][1]
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bmesh.ops.triangulate(bm, faces=bm.faces[:])
mb = bpy.data.materials.new('Bow'); mb.use_nodes = True
bsdf = next(nd for nd in mb.node_tree.nodes if nd.type == 'BSDF_PRINCIPLED')
tex = mb.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = img
mb.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color']); bsdf.inputs['Roughness'].default_value = 0.6
me = bpy.data.meshes.new('BowMesh'); bm.to_mesh(me); bm.free()
bow = bpy.data.objects.new('BowMesh', me); bpy.context.scene.collection.objects.link(bow); me.materials.append(mb)
for p in me.polygons:
    p.use_smooth = True
# string ends: where the string column meets the limbs (first/last rows with string pixels next to the limb)
srows = [r for r in range(top, bot) if al[r, int(STRING_X)] and al[r, int(STRING_X) + 2]]
s_top, s_bot = min(srows), max(srows)
string = {'top': list(to_bow(STRING_X, s_top + 6)), 'bottom': list(to_bow(STRING_X, s_bot - 6))}
# ---------------------------------------------------------------- arrow texture (rows: shaft wood, head steel, fletch)
tw, th_ = 64, 256
A = np.zeros((th_, tw, 4), np.float32)
A[:, :, 3] = 1
A[:, :, :3] = (0.36, 0.22, 0.12)                                # shaft wood
A[:16, :, :3] = (0.62, 0.64, 0.66)                              # steel head (top rows)
A[200:, :, :3] = (0.86, 0.86, 0.84)                             # fletching
for k in range(200, 256, 6):
    A[k, :, :3] = (0.70, 0.70, 0.70)                            # vane barbs
A[16:20, :, :3] = (0.18, 0.12, 0.08)                            # binding below the head
aimg = bpy.data.images.new('arrow', tw, th_)
aimg.pixels[:] = A[::-1].ravel(); aimg.filepath_raw = R('textures', 'props', 'arrow.png'); aimg.file_format = 'PNG'; aimg.save()
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
SH, L_SHAFT, HEAD = 6, 0.74, 0.07


def ring(y, r, sides):
    return [bm.verts.new((math.cos(2 * math.pi * k / sides) * r, y, math.sin(2 * math.pi * k / sides) * r)) for k in range(sides)]


def strip(a, b, ya, yb):
    for k in range(len(a)):
        k2 = (k + 1) % len(a)
        f = bm.faces.new((a[k], a[k2], b[k2], b[k]))
        for lp, uv in zip(f.loops, ((0.1 + 0.8 * k / len(a), ya / 0.81), (0.1 + 0.8 * (k + 1) / len(a), ya / 0.81),
                                    (0.1 + 0.8 * (k + 1) / len(a), yb / 0.81), (0.1 + 0.8 * k / len(a), yb / 0.81))):
            lp[uvl].uv = uv


r0 = ring(0.0, 0.0035, SH); r1 = ring(L_SHAFT, 0.0040, SH)
strip(r0, r1, 0.0, L_SHAFT)
hb = ring(L_SHAFT, 0.0065, 4); tip = bm.verts.new((0, L_SHAFT + HEAD, 0))
for k in range(4):
    f = bm.faces.new((hb[k], hb[(k + 1) % 4], tip))
    for lp in f.loops:
        lp[uvl].uv = (0.5, 0.98)
f = bm.faces.new(list(reversed(hb)))
for lp in f.loops:
    lp[uvl].uv = (0.5, 0.95)
cap = bm.verts.new((0, 0, 0))
for k in range(SH):
    f = bm.faces.new((r0[(k + 1) % SH], r0[k], cap))
    for lp in f.loops:
        lp[uvl].uv = (0.5, 0.3)
for k in range(3):                                              # fletching vanes, two-sided
    a = 2 * math.pi * k / 3 + math.pi / 2
    d = Vector((math.cos(a), 0, math.sin(a)))
    q = [Vector((0, 0.02, 0)) + d * 0.004, Vector((0, 0.13, 0)) + d * 0.004, Vector((0, 0.10, 0)) + d * 0.016,
         Vector((0, 0.02, 0)) + d * 0.014]
    vs = [bm.verts.new(p) for p in q]
    uvq = ((0.1, 0.02), (0.1, 0.2), (0.9, 0.2), (0.9, 0.02))
    for order in ((0, 1, 2, 3), (3, 2, 1, 0)):
        vv = [bm.verts.new(q[i]) for i in order] if order[0] == 3 else vs
        f = bm.faces.new(vv)
        for lp, i in zip(f.loops, order):
            lp[uvl].uv = uvq[i]
bmesh.ops.triangulate(bm, faces=bm.faces[:])
ma = bpy.data.materials.new('Arrow'); ma.use_nodes = True
bsdf = next(nd for nd in ma.node_tree.nodes if nd.type == 'BSDF_PRINCIPLED')
tex = ma.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = aimg
ma.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color']); bsdf.inputs['Roughness'].default_value = 0.6
me = bpy.data.meshes.new('ArrowMesh'); bm.to_mesh(me); bm.free()
arrow = bpy.data.objects.new('ArrowMesh', me); bpy.context.scene.collection.objects.link(arrow); me.materials.append(ma)
info = {'metres_per_px': M, 'grip_row': GRIP_ROW, 'grip_x': float(GRIP_X), 'string': string,
        'bow_tris': len(bow.data.polygons), 'arrow_tris': len(arrow.data.polygons), 'arrow_length': L_SHAFT + HEAD}
json.dump(info, open(R('work', 'bow.json'), 'w'), indent=1)
print('BOW', json.dumps(info))
bpy.ops.wm.save_as_mainfile(filepath=R('work', 'props.blend'))
