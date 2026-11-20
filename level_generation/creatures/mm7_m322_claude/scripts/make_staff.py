"""Crooked wooden walking staff for m322 (after mm7_m302_claude/scripts/make_club.py) from the HD prop reference
(references_hd/staff.png: vertical, thicker end up). The native front frame (m322sa0) puts the staff at 0.85 of her
height (1.49 m for the 1.75 m model) with the fist at 0.78 of it; GRIP_FRAC 0.70 up from the butt puts the butt on the floor with the carry wrist at 1.05 m.
Prop space (as make_axe.py in mm7_m190_claude, read by export_runtime.py): +Y along the staff toward the top, origin at
the grip centre (image row GRIP, just above the butt knob), +X image right, +Z toward the viewer. LENGTH overall.
- body of revolution: per sampled row the silhouette's run gives the ring centre (the branch bends a little) and its
  radius; RING_SIDES-sided rings, the radius clamped to at least the solved fist's handle radius (grip_solve.py
  R_HANDLE) along the grip; a closing fan at both ends.
- planar texture: the reference's front, columns X0..X1 x rows Y0..Y1, bled, 256 x 1024 (textures/m322_staff_basecolor.png);
  each ring vertex samples the column at its angle (front and back mirror, as the axe haft).
Writes work/props.blend ('StaffMesh', material 'Staff', UVMap) and work/staff.json. Args: none"""
import bpy, bmesh, os, json, math
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(HERE, *p)
os.makedirs(R('textures'), exist_ok=True)
LENGTH = float(os.environ.get('LENGTH', '1.49'))
GRIP_FRAC = float(os.environ.get('GRIP_FRAC', '0.70'))
R_HANDLE = float(os.environ.get('R_HANDLE', '0.016'))
RING_SIDES = 10
bpy.ops.wm.read_factory_settings(use_empty=True)
img = bpy.data.images.load(R('references_hd', 'staff.png'))
W_, H_ = img.size
px = np.array(img.pixels[:]).reshape(H_, W_, 4)[::-1]
al = px[:, :, 3] > 0.5
rows_any = np.where(al.any(1))[0]
TOP, BOT = int(rows_any.min()), int(rows_any.max())
GRIP = int(BOT - GRIP_FRAC * (BOT - TOP))
M = LENGTH / (BOT - TOP)
cols_any = np.where(al.any(0))[0]
X0, X1, Y0, Y1 = int(cols_any.min()) - 8, int(cols_any.max()) + 8, TOP - 8, BOT + 8


def run(r):
    xs = np.where(al[int(r)])[0]
    return (xs.min(), xs.max()) if len(xs) else None


CX = float(np.mean(run(GRIP)))
y_of = lambda r: (GRIP - r) * M
uv = lambda c, r: ((c - X0) / (X1 - X0), 1 - (r - Y0) / (Y1 - Y0))
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')


def face(vs, uvs):
    f = bm.faces.new(vs)
    for lp, u in zip(f.loops, uvs):
        lp[uvl].uv = u
    return f


rows = [BOT - 2] + list(np.linspace(BOT - 12, TOP + 10, 56).astype(int)) + [TOP + 2]
rings = []
for r in rows:
    a_, b_ = run(r)
    c, hw = (a_ + b_) / 2, (b_ - a_ + 1) / 2
    rad = hw * M
    if abs(r - GRIP) < 0.1 * (BOT - TOP):
        rad = max(rad, R_HANDLE)
    if r in (rows[0], rows[-1]):
        rad *= 0.6                                            # rounded ends
    ring = []
    for k in range(RING_SIDES):
        ang = 2 * math.pi * k / RING_SIDES
        ring.append((bm.verts.new(((c - CX) * M + math.cos(ang) * rad, y_of(r), math.sin(ang) * rad)),
                     uv(c + math.cos(ang) * hw * 0.92, r)))
    rings.append((ring, c, r))
for (a_, _, _), (b_, _, _) in zip(rings[:-1], rings[1:]):
    for k in range(RING_SIDES):
        k2 = (k + 1) % RING_SIDES
        face((a_[k][0], a_[k2][0], b_[k2][0], b_[k][0]), (a_[k][1], a_[k2][1], b_[k2][1], b_[k][1]))
for (ring, c, r), sign in ((rings[0], -1), (rings[-1], 1)):
    cap = bm.verts.new(((c - CX) * M, y_of(r) + sign * 0.006, 0))
    for k in range(RING_SIDES):
        k2 = (k + 1) % RING_SIDES
        vs = (ring[k2][0], ring[k][0], cap) if sign < 0 else (ring[k][0], ring[k2][0], cap)
        us = (ring[k2][1], ring[k][1], uv(c, r)) if sign < 0 else (ring[k][1], ring[k2][1], uv(c, r))
        face(vs, us)
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
timg = bpy.data.images.new('staff_tex', X1 - X0, Y1 - Y0)
timg.pixels[:] = np.concatenate([rgb, np.ones(rgb.shape[:2] + (1,))], -1)[::-1].ravel()
timg.scale(128, 1024)
timg.filepath_raw = R('textures', 'm322_staff_basecolor.png'); timg.file_format = 'PNG'; timg.save()
mat = bpy.data.materials.new('Staff'); mat.use_nodes = True
bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
t = mat.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(R('textures', 'm322_staff_basecolor.png'))
mat.node_tree.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
me = bpy.data.meshes.new('StaffMesh'); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new('StaffMesh', me); bpy.context.scene.collection.objects.link(ob); me.materials.append(mat)
for p in me.polygons:
    p.use_smooth = True
co = np.array([tuple(v.co) for v in me.vertices])
info = {'metres_per_px': M, 'length': LENGTH, 'grip_row': GRIP, 'top_y': y_of(TOP), 'butt_y': y_of(BOT),
        'head_radius': float(np.hypot(co[:, 0], co[:, 2]).max()), 'tris': len(me.polygons)}
json.dump(info, open(R('work', 'staff.json'), 'w'), indent=1)
print('STAFF', json.dumps(info))
bpy.ops.wm.save_as_mainfile(filepath=R('work', 'props.blend'))
