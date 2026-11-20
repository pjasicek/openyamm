"""Broadsword for m246 from the HD prop reference (references_hd/broadsword.png, left = broad side, tip up), natm's prop
route (make_props.py / prop_textures.py): silhouette rows give the outline, planar projection gives the texture.
Prop space: +Y along the grip toward the tip, origin at the grip centre, +X toward the cutting edge, +Z the flat normal.
The blade is single-edged (seax-like): the straight IMAGE-LEFT side is the edge (the point lies on it), the image-right
side is the spine with the angled clip near the tip, so image x is mirrored into +X. 1.10 m overall (rows 33..1520).
- blade (rows 33..1180, the middle run of each row): wedge section, edge sharp, spine 6 mm thick, centre 7 mm;
- crescent quillons (rows 1090..1180, the left/right runs): flat horns 1.4 cm thick, closed tubes;
- crossbar (1180..1226): flat bar 2.2 cm thick over the full outline;
- grip (1226..1430): octagon, radius 1.3 cm (the solved fist, grip_solve.py R_HANDLE; the reference grip is wider);
- pommel (1430..1520): round, radius from the outline (<= 3 cm).
Run twice: plain python3 writes textures/props/sword_basecolor.png (256 x 1024 crop of the broad side, bled)
and textures/props/sword_rows.json (runs per row); then Blender writes work/props.blend ('SwordMesh' with 'UVMap' and an
image material) and prints the triangle count. Args: none"""
import os, json, math
import numpy as np
try:
    import bpy, bmesh
except ImportError:
    bpy = None
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(HERE, *p)
X0, X1, Y0, Y1 = 150, 480, 25, 1530                       # crop of the broad-side view
TOP, BOT = 35, 1514
PX = 1.10 / (BOT - TOP)
GRIP_ROW = 1328


def bleed(img, rounds=40):
    a = np.array(img).astype(np.float32); rgb, al = a[:, :, :3], a[:, :, 3] > 128
    for _ in range(rounds):
        if al.all():
            break
        acc = np.zeros_like(rgb); cnt = np.zeros(al.shape, np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            m = np.roll(np.roll(al, dy, 0), dx, 1); c = np.roll(np.roll(rgb, dy, 0), dx, 1)
            acc += c * m[:, :, None]; cnt += m
        new = (~al) & (cnt > 0); rgb[new] = acc[new] / cnt[new][:, None]; al = al | new
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))


if bpy is None:
    from PIL import Image
    im = Image.open(R('references_hd', 'broadsword.png')).convert('RGBA')
    A = np.array(im)[:, :512, 3] > 128
    os.makedirs(R('textures', 'props'), exist_ok=True)
    bleed(im.crop((X0, Y0, X1, Y1))).resize((256, 1024), Image.LANCZOS).save(R('textures', 'props', 'sword_basecolor.png'))
    rows = {}
    for r in range(TOP, BOT + 1):
        x = A[r].astype(int); d = np.diff(np.r_[0, x, 0])
        s, e = np.where(d == 1)[0], np.where(d == -1)[0] - 1
        runs = [[int(a), int(b)] for a, b in zip(s, e) if b - a >= 2]
        if runs:
            rows[r] = runs
    json.dump(rows, open(R('textures', 'props', 'sword_rows.json'), 'w'))
    print('SWORD texture and', len(rows), 'outline rows written')
    raise SystemExit
RUNS = {int(k): v for k, v in json.load(open(R('textures', 'props', 'sword_rows.json'))).items()}
GRIP_X = float(np.mean([np.mean(RUNS[r][0]) for r in range(1240, 1420, 10) if r in RUNS and len(RUNS[r]) == 1]))
uv = lambda x, r: ((x - X0) / (X1 - X0), 1.0 - (r - Y0) / (Y1 - Y0))
P = lambda x, r, z: (-(x - GRIP_X) * PX, (GRIP_ROW - r) * PX, z)     # image left (the edge) -> +X


def run(r, which):
    rs = RUNS[r]
    if which == 'mid':
        return min(rs, key=lambda s: abs((s[0] + s[1]) / 2 - GRIP_X))
    if which == 'left':
        return rs[0]
    if which == 'right':
        return rs[-1]
    return [rs[0][0], rs[-1][1]]


def blade(r):
    lo, hi = run(r, 'mid')
    k = min(1.0, (r - TOP) / 60.0)
    e, s = 0.0003, 0.003 * k + 0.0003
    c = lo + (hi - lo) * 0.45
    return [(lo, 0.0), (c, 0.0035 * k + 0.0003), (hi, s), (hi, -s), (c, -0.0035 * k - 0.0003)]


def horn(which):
    def sec(r):
        lo, hi = run(r, which)
        return [(lo, 0.007), (hi, 0.007), (hi, -0.007), (lo, -0.007)]
    return sec


def bar(r):
    lo, hi = run(r, 'all')
    return [(lo, 0.011), (hi, 0.011), (hi, -0.011), (lo, -0.011)]


def round_(rad_max):
    def sec(r):
        lo, hi = run(r, 'all'); c = (lo + hi) / 2
        rad = min(rad_max, (hi - lo) / 2 * PX)
        return [(c + rad / PX * math.cos(a), rad * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)]
    return sec


bpy.ops.wm.read_factory_settings(use_empty=True)
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')


def face(vs, uvs):
    f = bm.faces.new(vs)
    for loop, u in zip(f.loops, uvs):
        loop[uvl].uv = u
    return f


def loft(rows, sec, cap_start=True, point=False):
    prev = None
    for r in rows:
        cur = [(bm.verts.new(P(x, r, z)), x) for x, z in sec(r)]
        n = len(cur)
        if prev is None:
            if point:
                cx = sum(x for _, x in cur) / n; tip = bm.verts.new(P(cx, r - 3, 0.0))
                for i in range(n):
                    j = (i + 1) % n
                    face((tip, cur[j][0], cur[i][0]), (uv(cx, r - 3), uv(cur[j][1], r), uv(cur[i][1], r)))
            elif cap_start:
                face([v for v, _ in cur], [uv(x, r) for _, x in cur])
        else:
            pr, pv = prev
            for i in range(n):
                j = (i + 1) % n
                face((pv[i][0], pv[j][0], cur[j][0], cur[i][0]), (uv(pv[i][1], pr), uv(pv[j][1], pr), uv(cur[j][1], r), uv(cur[i][1], r)))
        prev = (r, cur)
    r, cur = prev
    face([v for v, _ in cur][::-1], [uv(x, r) for _, x in cur][::-1])


loft(list(range(TOP + 15, 1130, 45)) + [1150, 1178], blade, point=True)
loft([1090, 1102, 1114, 1126, 1140, 1154, 1166, 1178], horn('left'))
loft([1090, 1102, 1114, 1126, 1140, 1154, 1166, 1178], horn('right'))
loft([1180, 1192, 1204, 1214, 1226], bar)
loft(list(range(1226, 1430, 34)) + [1430], round_(0.013))
loft([1432, 1445, 1460, 1475, 1490, 1502, BOT - 2], round_(0.030))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new('SwordMesh'); bm.to_mesh(me); bm.free()
o = bpy.data.objects.new('SwordMesh', me); bpy.context.scene.collection.objects.link(o)
m = bpy.data.materials.new('Sword'); m.use_nodes = True
bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
t = m.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(R('textures', 'props', 'sword_basecolor.png'))
m.node_tree.links.new(t.outputs['Color'], bsdf.inputs['Base Color']); me.materials.append(m)
for p in me.polygons:
    p.use_smooth = True
co = np.array([tuple(v.co) for v in me.vertices])
print('SWORD tris', sum(len(p.vertices) - 2 for p in me.polygons), 'length m', round(float(co[:, 1].max() - co[:, 1].min()), 3),
      'tip y', round(float(co[:, 1].max()), 3), 'x range', round(float(co[:, 0].min()), 3), round(float(co[:, 0].max()), 3),
      'min face area mm2', round(min(p.area for p in me.polygons) * 1e6, 3))
json.dump({'grip_x_px': GRIP_X, 'grip_row': GRIP_ROW, 'px_m': PX, 'edge': '+X (image left)'},
          open(R('textures', 'props', 'sword_profile.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=R('work', 'props.blend'))
