"""Billhook for 7m452 from the HD prop reference (references_hd/billhook.png: vertical, blade up, hook to image left).
Prop space (as make_club.py / mm7_m190_claude make_axe.py, read by export_runtime.py): +Y along the shaft toward the
blade, origin at the grip centre (GRIP_FRAC of the length above the butt), +X image right, +Z toward the viewer.
LENGTH overall.
- shaft and socket: a body of revolution from the silhouette's centre run per sampled row (rows SOCKET_TOP..butt),
  10-sided rings, the radius scaled so the shaft at the grip is R_HANDLE (the solved fist's handle radius);
- blade (rows above SOCKET_TOP, including the separate hook-tip runs): the silhouette rasterised into CELL-pixel
  cells, one front and one back face per cell, welded, the boundary relaxed (removes the cell staircase), edge
  walls; a wedge 6 mm thick at the spine -> 1.5 mm at the cutting edge (simple: thickness by distance to the socket
  axis);
- planar texture: the reference's front (columns X0..X1, rows Y0..Y1), bled, 256 x 1024.
Writes work/props.blend ('ClubMesh' - the name the shared club scripts load -, material 'Club', UVMap) and
work/club.json. Args: none"""
import bpy, bmesh, os, json, math
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(HERE, *p)
os.makedirs(R('textures'), exist_ok=True)
LENGTH = float(os.environ.get('LENGTH', '1.4'))
R_HANDLE = float(os.environ.get('R_HANDLE', '0.02'))
GRIP_FRAC = float(os.environ.get('GRIP_FRAC', '0.28'))   # native walk m452w*2: the fist a quarter up the shaft
SOCKET_TOP = int(os.environ.get('SOCKET_TOP', '450'))
CELL = 6
bpy.ops.wm.read_factory_settings(use_empty=True)
img = bpy.data.images.load(R('references_hd', 'billhook.png'))
W_, H_ = img.size
px = np.array(img.pixels[:]).reshape(H_, W_, 4)[::-1]
al = px[:, :, 3] > 0.5
rows_any = np.where(al.any(1))[0]
TOP, BOT = int(rows_any.min()), int(rows_any.max())
M = LENGTH / (BOT - TOP)
GRIP = int(BOT - GRIP_FRAC * (BOT - TOP))
cols_any = np.where(al.any(0))[0]
X0, X1, Y0, Y1 = int(cols_any.min()) - 8, int(cols_any.max()) + 8, TOP - 8, BOT + 8


def runs(r):
    xs = np.where(al[int(r)])[0]
    out, s, p = [], None, None
    for x in xs:
        if s is None:
            s = p = x
        elif x != p + 1:
            out.append((s, p)); s = p = x
        else:
            p = x
    if s is not None:
        out.append((s, p))
    return out


def centre_run(r):
    rs = runs(r)
    return max(rs, key=lambda q: q[1] - q[0])


ga, gb = centre_run(GRIP); CX = (ga + gb) / 2
SCALE_R = R_HANDLE / ((gb - ga + 1) / 2 * M)
y_of = lambda r: (GRIP - r) * M
x_of = lambda c: (c - CX) * M
uv = lambda c, r: ((c - X0) / (X1 - X0), 1 - (r - Y0) / (Y1 - Y0))
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')


def face(vs, uvs):
    f = bm.faces.new(vs)
    for lp, u in zip(f.loops, uvs):
        lp[uvl].uv = u
    return f


# ---- shaft + socket
N = 10
rows = [BOT - 2] + list(np.linspace(BOT - 10, SOCKET_TOP - 6, 34).astype(int))
rings = []
for r in rows:
    a_, b_ = centre_run(r); c, hw = (a_ + b_) / 2, (b_ - a_ + 1) / 2
    rad = hw * M * SCALE_R * (0.7 if r == rows[0] else 1.0)
    ring = []
    for k in range(N):
        ang = 2 * math.pi * k / N
        ring.append((bm.verts.new((x_of(c) + math.cos(ang) * rad, y_of(r), math.sin(ang) * rad)), uv(c + math.cos(ang) * hw * 0.9, r)))
    rings.append((ring, c, r))
for (a_, _, _), (b_, _, _) in zip(rings[:-1], rings[1:]):
    for k in range(N):
        k2 = (k + 1) % N
        face((a_[k][0], a_[k2][0], b_[k2][0], b_[k][0]), (a_[k][1], a_[k2][1], b_[k2][1], b_[k][1]))
for (ring, c, r), sign in ((rings[0], -1), (rings[-1], 1)):
    cap = bm.verts.new((x_of(c), y_of(r) + sign * 0.004, 0))
    for k in range(N):
        k2 = (k + 1) % N
        if sign < 0:
            face((ring[k2][0], ring[k][0], cap), (ring[k2][1], ring[k][1], uv(c, r)))
        else:
            face((ring[k][0], ring[k2][0], cap), (ring[k][1], ring[k2][1], uv(c, r)))
shaft_faces = len(bm.faces)
# ---- blade: cells
bl = al.copy(); bl[SOCKET_TOP:] = False
gy, gx = np.mgrid[TOP - CELL:SOCKET_TOP + CELL:CELL, X0:X1:CELL]
cells = {}
for y in range(TOP - CELL, SOCKET_TOP, CELL):
    for x in range(X0, X1, CELL):
        blk = bl[max(y, 0):y + CELL, x:x + CELL]
        if blk.size and blk.mean() > 0.5:
            cells[(y, x)] = True
vmap = {}


def V(y, x, side):
    k = (y, x, side)
    if k not in vmap:
        vmap[k] = bm.verts.new((x_of(x), y_of(y), 0.0))
    return vmap[k]


blade_faces = []
for (y, x) in cells:
    for side in (1, -1):
        q = [V(y, x, side), V(y, x + CELL, side), V(y + CELL, x + CELL, side), V(y + CELL, x, side)]
        if side < 0:
            q = q[::-1]
        us = [uv(v.co.x / M + CX, GRIP - v.co.y / M) for v in q]
        blade_faces.append(face(q, us))
# edge walls between the two sides
for (y, x) in cells:
    for (dy, dx, a, b) in ((-CELL, 0, (y, x), (y, x + CELL)), (CELL, 0, (y + CELL, x + CELL), (y + CELL, x)),
                           (0, -CELL, (y + CELL, x), (y, x)), (0, CELL, (y, x + CELL), (y + CELL, x + CELL))):
        if (y + dy, x + dx) in cells:
            continue
        va, vb = V(*a, 1), V(*b, 1); wa, wb = V(*a, -1), V(*b, -1)
        u_ = uv(x + CELL / 2, y + CELL / 2)
        face((vb, va, wa, wb), (u_, u_, u_, u_))
# relax the boundary (staircase) on both sides, then set the wedge thickness
bnd = {k for k in vmap if any(not cells.get((k[0] - oy, k[1] - ox)) for oy in (0, CELL) for ox in (0, CELL))}
for it in range(4):
    newpos = {}
    for k in bnd:
        y, x, s = k
        nb = [(y + dy, x + dx, s) for dy, dx in ((-CELL, 0), (CELL, 0), (0, -CELL), (0, CELL)) if (y + dy, x + dx, s) in vmap and (y + dy, x + dx, s) in bnd]
        if len(nb) >= 2:
            p = sum((vmap[n].co for n in nb), vmap[k].co * 0) / len(nb)
            newpos[k] = vmap[k].co * 0.5 + p * 0.5
    for k, p in newpos.items():
        vmap[k].co = p
for (y, x, s), v in vmap.items():
    d = abs(v.co.x - x_of(CX)) / max(M * 120, 1e-6)
    t = 0.003 - 0.00225 * min(1.0, d)
    v.co.z = s * t
bmesh.ops.remove_doubles(bm, verts=list(vmap.values()), dist=1e-6)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bmesh.ops.triangulate(bm, faces=bm.faces[:])
crop = px[Y0:Y1, X0:X1]
cov = crop[..., 3] > 0.5
rgb = crop[..., :3].copy(); filled = cov.copy()
for _ in range(80):
    if filled.all():
        break
    acc = np.zeros_like(rgb); cnt = np.zeros(filled.shape)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        sh = np.roll(filled, (dy, dx), (0, 1)); sc = np.roll(rgb, (dy, dx), (0, 1))
        acc += sc * sh[..., None]; cnt += sh
    grow = ~filled & (cnt > 0)
    rgb[grow] = acc[grow] / cnt[grow][:, None]; filled |= grow
rgb[~filled] = rgb[cov].mean(0)
timg = bpy.data.images.new('club_tex', X1 - X0, Y1 - Y0)
timg.pixels[:] = np.concatenate([rgb, np.ones(rgb.shape[:2] + (1,))], -1)[::-1].ravel()
timg.scale(256, 1024)
timg.filepath_raw = R('textures', '7m452_club_basecolor.png'); timg.file_format = 'PNG'; timg.save()
mat = bpy.data.materials.new('Club'); mat.use_nodes = True
bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
t = mat.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(R('textures', '7m452_club_basecolor.png'))
mat.node_tree.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
me = bpy.data.meshes.new('ClubMesh'); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new('ClubMesh', me); bpy.context.scene.collection.objects.link(ob); me.materials.append(mat)
# the cells are coplanar per side: dissolve them into large n-gons, then triangulate (6k -> ~1k tris)
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
m_ = ob.modifiers.new('dis', 'DECIMATE'); m_.decimate_type = 'DISSOLVE'; m_.angle_limit = math.radians(2)
bpy.ops.object.modifier_apply(modifier='dis')
m_ = ob.modifiers.new('tri', 'TRIANGULATE'); bpy.ops.object.modifier_apply(modifier='tri')
# smooth shaft, flat blade
me = ob.data
co = np.array([tuple(v.co) for v in me.vertices])
for p in me.polygons:
    p.use_smooth = abs(p.normal.z) < 0.9 and p.center.y < y_of(SOCKET_TOP) + 0.01
info = {'metres_per_px': M, 'length': LENGTH, 'grip_row': GRIP, 'top_y': y_of(TOP), 'butt_y': y_of(BOT),
        'head_radius': float(np.hypot(co[:, 0], co[:, 2]).max()), 'blade_from_y': y_of(SOCKET_TOP), 'tris': len(ob.data.polygons)}
json.dump(info, open(R('work', 'club.json'), 'w'), indent=1)
print('CLUB', json.dumps(info))
bpy.ops.wm.save_as_mainfile(filepath=R('work', 'props.blend'))
if os.environ.get('RENDER'):
    import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common
    ob.rotation_euler = (math.pi / 2, 0, 0); ob.location.z = 0.2
    common.workbench_clay(bpy.context.scene, textured=True)
    common.render_views(R('review', 'billhook'), 0.53, 1.6, views=('front', 'left', 'three_quarter'), resolution=(400, 900))
