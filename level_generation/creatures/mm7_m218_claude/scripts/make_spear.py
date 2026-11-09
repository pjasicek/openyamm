"""Spear mesh for m218 in prop space, modelled from the HD spear reference (references_hd/spear.png, vertical, tip up) and
textured by planar projection of that image (cropped to columns X0..X0+CW, 64 x 1024: textures/m218_spear_basecolor.png).
Prop space: +Y toward the tip, origin at the carry grip 0.85 m above the butt, 2.0 m long (image rows 35..1499).
Shaft: 8-sided, r 1.4 cm (the solved fists close on 1.4 cm), bindings r 1.6 cm where the reference is wider; blade:
4-sided diamond section, width from the reference alpha, 0.8 cm thick; butt closed with a cap ring.
Writes work/props.blend (object SpearMesh, material Spear, UVMap) and work/spear.json. Args: none"""
import bpy, bmesh, os, json, math
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(HERE, *p)
os.makedirs(R('textures'), exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
img = bpy.data.images.load(R('references_hd', 'spear.png'))
W_, H_ = img.size
px = np.array(img.pixels[:]).reshape(H_, W_, 4)[::-1]
al = px[:, :, 3] > 0.5
ys, xs = np.where(al)
TOP, BOT = ys.min(), ys.max()
M = 2.0 / (BOT - TOP)
X0, CW = 470, 82
GRIP_FROM_BUTT = 0.85
y_of = lambda r: (BOT - r) * M - GRIP_FROM_BUTT
row_of = lambda y: BOT - (y + GRIP_FROM_BUTT) / M


def half_width(r):
    c = np.where(al[int(r)])[0]
    return ((c.max() - c.min() + 1) / 2 * M, (c.max() + c.min()) / 2) if len(c) else (0.0, (X0 + CW / 2))


uvx = lambda x: (x - X0) / CW
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
BLADE_BASE = 170                                                  # image row where the blade meets the socket
rings = []
shaft_rows = [BOT, BOT - 8] + list(np.arange(BOT - 30, BLADE_BASE + 40, -60)) + [BLADE_BASE + 20, BLADE_BASE]
for r in shaft_rows:
    hw, cx = half_width(r)
    rad = 0.016 if hw > 0.0235 else 0.014
    ring = []
    for k in range(8):
        a = 2 * math.pi * k / 8
        v = bm.verts.new((math.cos(a) * rad, y_of(r), math.sin(a) * rad))
        ring.append((v, (uvx(cx + math.cos(a) * hw / M * 0.9), 1 - r / H_)))
    rings.append(ring)
for a_, b_ in zip(rings[:-1], rings[1:]):
    for k in range(8):
        k2 = (k + 1) % 8
        f = bm.faces.new((a_[k][0], a_[k2][0], b_[k2][0], b_[k][0]))
        for lp, (v, uv) in zip(f.loops, (a_[k], a_[k2], b_[k2], b_[k])):
            lp[uvl].uv = uv
cap = bm.verts.new((0, y_of(BOT), 0))
for k in range(8):
    f = bm.faces.new((rings[0][(k + 1) % 8][0], rings[0][k][0], cap))
    for lp in f.loops:
        lp[uvl].uv = (0.5, 1 - BOT / H_)
# blade: diamond rings from BLADE_BASE up to the tip
brows = list(np.arange(BLADE_BASE, TOP + 4, -14)) + [TOP]
prev = rings[-1]
blade = []
for r in brows:
    hw, cx = half_width(r)
    hw = max(hw, 0.002)
    th = 0.004 * max(hw / 0.04, 0.25)
    pts = [(hw, 0), (0, th), (-hw, 0), (0, -th)]
    ring = []
    for (dx, dz), uu in zip(pts, (1, 0.5, 0, 0.5)):
        v = bm.verts.new((dx, y_of(r), dz))
        ring.append((v, (uvx(cx + (uu - 0.5) * 2 * hw / M), 1 - r / H_)))
    blade.append(ring)
for a_, b_ in zip(blade[:-1], blade[1:]):
    for k in range(4):
        k2 = (k + 1) % 4
        f = bm.faces.new((a_[k][0], a_[k2][0], b_[k2][0], b_[k][0]))
        for lp, (v, uv) in zip(f.loops, (a_[k], a_[k2], b_[k2], b_[k])):
            lp[uvl].uv = uv
tip = bm.verts.new((0, y_of(TOP) + 0.004, 0))
for k in range(4):
    f = bm.faces.new((blade[-1][k][0], blade[-1][(k + 1) % 4][0], tip))
    for lp in f.loops:
        lp[uvl].uv = (0.5, 1 - TOP / H_)
cap2 = bm.verts.new((0, y_of(BLADE_BASE), 0))                   # close the socket top under the blade
for k in range(8):
    f = bm.faces.new((rings[-1][k][0], rings[-1][(k + 1) % 8][0], cap2))
    for lp in f.loops:
        lp[uvl].uv = (0.5, 1 - BLADE_BASE / H_)
f = bm.faces.new([v for v, _ in reversed(blade[0])])
for lp in f.loops:
    lp[uvl].uv = (0.5, 1 - BLADE_BASE / H_)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bmesh.ops.triangulate(bm, faces=bm.faces[:])
crop = np.asarray(img.pixels[:]).reshape(H_, W_, 4)[::-1][:, X0:X0 + CW]
cov = crop[..., 3] > 0.5
rgb = crop[..., :3].copy()
glob = rgb[cov].mean(0)
for r in range(rgb.shape[0]):                                     # bleed each row's colour into its transparent texels
    c = np.where(cov[r])[0]
    if len(c):
        idx = np.clip(np.searchsorted(c, np.arange(rgb.shape[1])), 0, len(c) - 1)
        rgb[r] = rgb[r][c[idx]]
    else:
        rgb[r] = glob
timg = bpy.data.images.new('spear_tex', CW, H_)
timg.pixels[:] = np.concatenate([rgb, np.ones(rgb.shape[:2] + (1,))], -1)[::-1].ravel()
timg.scale(64, 1024)
timg.filepath_raw = R('textures', 'm218_spear_basecolor.png'); timg.file_format = 'PNG'; timg.save()
mat = bpy.data.materials.new('Spear'); mat.use_nodes = True
bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
t = mat.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(R('textures', 'm218_spear_basecolor.png'))
mat.node_tree.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
me = bpy.data.meshes.new('SpearMesh'); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new('SpearMesh', me); bpy.context.scene.collection.objects.link(ob); me.materials.append(mat)
for p in me.polygons:
    p.use_smooth = True
info = {'metres_per_px': M, 'length': 2.0, 'grip_from_butt': GRIP_FROM_BUTT, 'tip_y': y_of(TOP), 'butt_y': y_of(BOT),
        'tris': len(me.polygons), 'crop': [X0, CW]}
json.dump(info, open(R('work', 'spear.json'), 'w'), indent=1)
print('SPEAR', json.dumps(info))
bpy.ops.wm.save_as_mainfile(filepath=R('work', 'props.blend'))
