"""Double-bitted axe for m190 from the HD prop reference (references_hd/axe.png: vertical, head up, the two blades left
and right of the haft, rows 43..1459). Prop space (as mm7_m222_claude/scripts/make_scimitar.py, read by export_runtime.py):
+Y along the haft toward the head, origin at the grip centre (image row 1230, the leather grip), +X toward the right
blade's edge (image right), +Z the blade's flat normal. 0.70 m overall.
- haft: 8-sided rings, radius 1.6 cm (the solved fist, grip_solve.py R_HANDLE) widened where the reference is wider
  (gold bands, collar), up to 2.6 cm; a gold pommel ball at the butt;
- head: the collar rings continue to row 250, then the top spike (4-sided cone) to the tip;
- blades: per side the reference outline (outer edge and the crescent's inner edge, rows 70..615) as a filled plate,
  a wedge 1.2 cm thick at the haft tapering to 0.2 cm at the edge.
Planar texture: columns 140..880 x rows 30..1478 of the reference, bled, 512 x 1024 (textures/m190_axe_basecolor.png).
Writes work/props.blend ('AxeMesh', material 'Axe', UVMap) and work/axe.json. Args: none"""
import bpy, bmesh, os, json, math
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(HERE, *p)
os.makedirs(R('textures'), exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
img = bpy.data.images.load(R('references_hd', 'axe.png'))
W_, H_ = img.size
px = np.array(img.pixels[:]).reshape(H_, W_, 4)[::-1]
al = px[:, :, 3] > 0.5
TOP, BOT, GRIP = 43, 1459, 1230
M = 0.70 / (BOT - TOP)
CX = 511.5                                                   # haft centre column (471..552)
HAFT_HW = 40.5                                               # haft half-width in px
X0, X1, Y0, Y1 = 140, 880, 30, 1478
y_of = lambda r: (GRIP - r) * M
x_of = lambda c: (c - CX) * M
uv = lambda c, r: ((c - X0) / (X1 - X0), 1 - (r - Y0) / (Y1 - Y0))


def runs(r):
    row = al[int(r)]; out, s = [], None
    for x in range(W_):
        if row[x] and s is None:
            s = x
        if not row[x] and s is not None:
            out.append((s, x - 1)); s = None
    return out


def centre_run(r):
    return next(((a, b) for a, b in runs(r) if a <= CX <= b), None)


bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')


def face(vs, uvs):
    f = bm.faces.new(vs)
    for lp, u in zip(f.loops, uvs):
        lp[uvl].uv = u
    return f


# ---- haft and collar: rings bottom -> row 250
rows = [BOT - 4, BOT - 20, 1420, 1400, 1380] + list(range(1350, 990, -40)) + [990, 975] + list(range(940, 640, -60)) + \
       [640, 615, 600, 560, 500, 440, 400, 380, 330, 290, 260, 250]
rings = []
for r in rows:
    cr = centre_run(r)
    hw = (cr[1] - cr[0] + 1) / 2 if cr and r > 620 else (HAFT_HW if r > 620 else min((cr[1] - cr[0] + 1) / 2 if cr else HAFT_HW, 70))
    if r <= 620 and cr and cr[1] - cr[0] > 300:              # merged with the blades: the collar width
        hw = 70
    rad = float(np.clip(0.016 * hw / HAFT_HW, 0.016, 0.026)) if r > 620 else float(np.clip(0.016 * hw / HAFT_HW, 0.016, 0.03))
    ring = []
    for k in range(8):
        a = 2 * math.pi * k / 8
        ring.append((bm.verts.new((math.cos(a) * rad, y_of(r), math.sin(a) * rad)), uv(CX + math.cos(a) * hw * 0.9, r)))
    rings.append(ring)
for a_, b_ in zip(rings[:-1], rings[1:]):
    for k in range(8):
        k2 = (k + 1) % 8
        face((a_[k][0], a_[k2][0], b_[k2][0], b_[k][0]), (a_[k][1], a_[k2][1], b_[k2][1], b_[k][1]))
# pommel ball under the lowest ring
pc = bm.verts.new((0, y_of(BOT), 0))
for k in range(8):
    face((rings[0][(k + 1) % 8][0], rings[0][k][0], pc), (rings[0][(k + 1) % 8][1], rings[0][k][1], uv(CX, BOT)))
# spike: 4-sided cone from the top ring
tip = bm.verts.new((0, y_of(TOP), 0))
top = rings[-1]
for k in range(8):
    face((top[k][0], top[(k + 1) % 8][0], tip), (top[k][1], top[(k + 1) % 8][1], uv(CX, TOP)))
# ---- blades
blade_rows = list(range(72, 620, 18))


def blade_outline(side):
    outer, inner = [], []
    for r in blade_rows:
        rs = [(a, b) for a, b in runs(r)]
        if side < 0:
            rs = [(a, min(b, CX - HAFT_HW)) for a, b in rs if a < CX - HAFT_HW - 4]
            if not rs:
                continue
            a, b = rs[0]; outer.append((a, r)); inner.append((b, r))
        else:
            rs = [(max(a, CX + HAFT_HW), b) for a, b in rs if b > CX + HAFT_HW + 4]
            if not rs:
                continue
            a, b = rs[-1]; outer.append((b, r)); inner.append((a, r))
    return outer, inner


blade_tris = 0
for side in (-1, 1):
    outer, inner = blade_outline(side)
    loop = outer + inner[::-1]                               # outer edge top -> bottom, inner edge bottom -> top
    pts = []
    for c, r in loop:
        d = abs(c - CX) - HAFT_HW
        span = max(abs(loop[0][0] - CX) - HAFT_HW, 1)
        t = 0.006 - 0.005 * float(np.clip(d / 360.0, 0, 1))  # half-thickness: 6 mm at the haft -> 1 mm at the edge
        pts.append((x_of(c), y_of(r), t, uv(c, r)))
    fv = [bm.verts.new((x, y, t)) for x, y, t, _ in pts]
    bv = [bm.verts.new((x, y, -t)) for x, y, t, _ in pts]
    n = len(pts)
    for vs, flip in ((fv, False), (bv, True)):
        edges = [bm.edges.new((vs[i], vs[(i + 1) % n])) for i in range(n)]
        res = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges)
        for f in [g for g in res['geom'] if isinstance(g, bmesh.types.BMFace)]:
            for lp in f.loops:
                i = vs.index(lp.vert); lp[uvl].uv = pts[i][3]
            blade_tris += 1
    for i in range(n):
        j = (i + 1) % n
        face((fv[i], fv[j], bv[j], bv[i]), (pts[i][3], pts[j][3], pts[j][3], pts[i][3]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bmesh.ops.triangulate(bm, faces=bm.faces[:])
crop = px[Y0:Y1, X0:X1]
cov = crop[..., 3] > 0.5
rgb = crop[..., :3].copy()
filled = cov.copy()
for _ in range(60):                                           # bleed: grow the covered colour outward (no scipy in Blender)
    if filled.all():
        break
    acc = np.zeros_like(rgb); cnt = np.zeros(filled.shape)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        sh = np.roll(filled, (dy, dx), (0, 1)); sc = np.roll(rgb, (dy, dx), (0, 1))
        acc += sc * sh[..., None]; cnt += sh
    grow = ~filled & (cnt > 0)
    rgb[grow] = acc[grow] / cnt[grow][:, None]; filled |= grow
rgb[~filled] = rgb[cov].mean(0)
timg = bpy.data.images.new('axe_tex', X1 - X0, Y1 - Y0)
timg.pixels[:] = np.concatenate([rgb, np.ones(rgb.shape[:2] + (1,))], -1)[::-1].ravel()
timg.scale(512, 1024)
timg.filepath_raw = R('textures', 'm190_axe_basecolor.png'); timg.file_format = 'PNG'; timg.save()
mat = bpy.data.materials.new('Axe'); mat.use_nodes = True
bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
t = mat.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(R('textures', 'm190_axe_basecolor.png'))
mat.node_tree.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
me = bpy.data.meshes.new('AxeMesh'); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new('AxeMesh', me); bpy.context.scene.collection.objects.link(ob); me.materials.append(mat)
for p in me.polygons:
    p.use_smooth = False
co = np.array([tuple(v.co) for v in me.vertices])
info = {'metres_per_px': M, 'length': 0.70, 'grip_row': GRIP, 'top_y': y_of(TOP), 'butt_y': y_of(BOT),
        'head_half_width': float(np.abs(co[:, 0]).max()), 'tris': len(me.polygons)}
json.dump(info, open(R('work', 'axe.json'), 'w'), indent=1)
print('AXE', json.dumps(info))
bpy.ops.wm.save_as_mainfile(filepath=R('work', 'props.blend'))
