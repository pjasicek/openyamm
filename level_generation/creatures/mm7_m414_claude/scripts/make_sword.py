"""Sword for m414 from the HD prop reference (references_hd/sword.png: vertical, point up, rows 21..1520), after
mm7_m410_claude/scripts/make_dagger.py. Prop space (axe_frame.py / the export rule): +Y along the grip toward the point,
origin at the grip centre (image row 1290), +X toward an edge (image right), +Z the blade's flat normal. 0.90 m overall.
- blade (rows 21..1110): 4-sided diamond section (central ridge), width from the reference, 0.9 cm thick at the base
  tapering to the point;
- crossguard (rows 1115..1165): a flat bar, 2 cm deep;
- grip (rows 1170..1410): 8-sided, radius 1.6 cm (the solved fist, grip_solve.py R_HANDLE);
- pommel (rows 1415..1520): 8-sided ball from the outline.
Planar texture: columns 340..690 x rows 10..1530 of the reference, bled, 256 x 1024 (textures/m414_sword_basecolor.png).
Writes work/props.blend ('SwordMesh', material 'Sword', UVMap) and work/sword.json. Args: none"""
import bpy, bmesh, os, json, math
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(HERE, *p)
os.makedirs(R('textures'), exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
img = bpy.data.images.load(R('references_hd', 'sword.png'))
W_, H_ = img.size
px = np.array(img.pixels[:]).reshape(H_, W_, 4)[::-1]
al = px[:, :, 3] > 0.5
TOP, BOT, GRIP = 21, 1520, 1290
M = 0.90 / (BOT - TOP)
CX = 511.5
X0, X1, Y0, Y1 = 340, 690, 10, 1530
y_of = lambda r: (GRIP - r) * M
uv = lambda c, r: ((c - X0) / (X1 - X0), 1 - (r - Y0) / (Y1 - Y0))


def half(r):
    c = np.where(al[int(r)])[0]
    return (c.max() - c.min() + 1) / 2 if len(c) else 1.0


bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')


def face(vs, uvs):
    f = bm.faces.new(vs)
    for lp, u in zip(f.loops, uvs):
        lp[uvl].uv = u
    return f


def bridge(a_, b_):
    n = len(a_)
    for k in range(n):
        k2 = (k + 1) % n
        face((a_[k][0], a_[k2][0], b_[k2][0], b_[k][0]), (a_[k][1], a_[k2][1], b_[k2][1], b_[k][1]))


def ring8(r, rad, hw_px):
    out = []
    for k in range(8):
        a = 2 * math.pi * k / 8
        out.append((bm.verts.new((math.cos(a) * rad, y_of(r), math.sin(a) * rad)), uv(CX + math.cos(a) * hw_px * 0.9, r)))
    return out


def cap(ring, r, up):
    c = bm.verts.new((0, y_of(r), 0))
    for k in range(len(ring)):
        a_, b_ = ring[k], ring[(k + 1) % len(ring)]
        vs = (a_[0], b_[0], c) if up else (b_[0], a_[0], c)
        face(vs, (a_[1], b_[1], uv(CX, r)) if up else (b_[1], a_[1], uv(CX, r)))


# grip + pommel (8-sided), bottom -> top
rows = [1518, 1505, 1480, 1450, 1425, 1415, 1405, 1330, 1250, 1172]
rings = []
for r in rows:
    hw = half(r)
    rad = 0.016 if 1170 <= r <= 1410 else min(max(hw * M, 0.012), 0.035)
    rings.append(ring8(r, rad, hw))
for a_, b_ in zip(rings[:-1], rings[1:]):
    bridge(a_, b_)
cap(rings[0], BOT, False)
# crossguard: a box
g0, g1, gw, gd = 1165, 1115, half(1141) * M, 0.010
gv = [bm.verts.new((sx * gw, y_of(r), sz * gd)) for r in (g0, g1) for sx in (-1, 1) for sz in (-1, 1)]
gu = [uv(CX + sx * half(1141), r) for r in (g0, g1) for sx in (-1, 1) for sz in (-1, 1)]
for q in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
    face([gv[i] for i in q], [gu[i] for i in q])
cap(rings[-1], 1170, True)
# blade: diamond rings from the guard to the point
brows = [1110] + list(range(1040, TOP + 30, -80)) + [TOP + 30]
bl = []
for r in brows:
    hw = half(r) * M; th = 0.0045 * max(hw / 0.058, 0.2)
    pts = [(hw, 0), (0, th), (-hw, 0), (0, -th)]
    bl.append([(bm.verts.new((dx, y_of(r), dz)), uv(CX + (dx / M if dz == 0 else 0), r)) for dx, dz in pts])
for a_, b_ in zip(bl[:-1], bl[1:]):
    bridge(a_, b_)
tip = bm.verts.new((0, y_of(TOP), 0))
for k in range(4):
    face((bl[-1][k][0], bl[-1][(k + 1) % 4][0], tip), (bl[-1][k][1], bl[-1][(k + 1) % 4][1], uv(CX, TOP)))
f = face([v for v, _ in reversed(bl[0])], [u for _, u in reversed(bl[0])])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bmesh.ops.triangulate(bm, faces=bm.faces[:])
crop = px[Y0:Y1, X0:X1]
cov = crop[..., 3] > 0.5
rgb = crop[..., :3].copy()
filled = cov.copy()
for _ in range(80):                                           # bleed (no scipy in Blender)
    if filled.all():
        break
    acc = np.zeros_like(rgb); cnt = np.zeros(filled.shape)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        sh = np.roll(filled, (dy, dx), (0, 1)); sc = np.roll(rgb, (dy, dx), (0, 1))
        acc += sc * sh[..., None]; cnt += sh
    grow = ~filled & (cnt > 0)
    rgb[grow] = acc[grow] / cnt[grow][:, None]; filled |= grow
rgb[~filled] = rgb[cov].mean(0)
timg = bpy.data.images.new('sword_tex', X1 - X0, Y1 - Y0)
timg.pixels[:] = np.concatenate([rgb, np.ones(rgb.shape[:2] + (1,))], -1)[::-1].ravel()
timg.scale(256, 1024)
timg.filepath_raw = R('textures', 'm414_sword_basecolor.png'); timg.file_format = 'PNG'; timg.save()
mat = bpy.data.materials.new('Sword'); mat.use_nodes = True
bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
t = mat.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(R('textures', 'm414_sword_basecolor.png'))
mat.node_tree.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
me = bpy.data.meshes.new('SwordMesh'); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new('SwordMesh', me); bpy.context.scene.collection.objects.link(ob); me.materials.append(mat)
info = {'metres_per_px': M, 'length': 0.90, 'grip_row': GRIP, 'tip_y': y_of(TOP), 'butt_y': y_of(BOT),
        'guard_y': y_of(1141), 'guard_top_y': y_of(1115), 'tris': len(me.polygons)}
json.dump(info, open(R('work', 'sword.json'), 'w'), indent=1)
print('SWORD', json.dumps(info))
bpy.ops.wm.save_as_mainfile(filepath=R('work', 'props.blend'))
