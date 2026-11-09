"""Bow, bowstring and arrow for the Medusa from the Codex prop reference references_hd/05_bow.png (the bow vertical with
its string on image RIGHT at x 902..906, rows 20..857 = BOW_LEN m; snake-head tips hooking toward the string; the arrow
below it, point on image LEFT). Route of mm7_m154_claude/scripts/make_bow.py, adapted.
Prop spaces:
- Bow: +Y up the bow, origin at the grip centre (row GRIP_ROW, limb centre), +X toward the STRING (image right),
  +Z the limb's side. Limbs: an octagon per sampled row, its X extent the reference outline (the limb's depth in the
  bow plane), Z half-width 0.8 x the X half-width (round, snake-like limbs), 0.5..2 cm.
- String (object 'StringMesh', joined into the body later): a 6-sided tube r 2 mm, top tip -> nock -> bottom tip at
  X = the string line; the nock ring carries the group 'StringNock', the tip rings 'Bow'.
- Arrow: origin at the nock (tail), +Y toward the point, ARROW_LEN m: hexagonal shaft r 4 mm, a flat diamond head
  and three fletching vanes cut from the reference silhouette.
Run twice: python3 (textures, outline rows), then Blender (work/props.blend: BowMesh, StringMesh, ArrowMesh). Args: none"""
import os, json, math
import numpy as np
try:
    import bpy, bmesh
except ImportError:
    bpy = None
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(HERE, *p)
TOP, BOT, GRIP_ROW, STRING_X = 20, 857, 430, 904.0
BOW_LEN, ARROW_LEN = 1.05, 0.82
PX = BOW_LEN / (BOT - TOP)
BX0, BX1 = 760, 936                                        # bow crop (limb + string)
AX0, AX1, AY0, AY1 = 400, 1136, 895, 968                   # arrow crop (horizontal, point left)


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
    return np.clip(rgb, 0, 255).astype(np.uint8)


def runs(row):
    x = np.nonzero(row)[0]
    if not len(x):
        return []
    return [(int(s[0]), int(s[-1])) for s in np.split(x, np.where(np.diff(x) > 1)[0] + 1)]


if bpy is None:
    from PIL import Image
    im = Image.open(R('references_hd', '05_bow.png')).convert('RGBA'); A = np.array(im)[:, :, 3] > 128
    os.makedirs(R('textures', 'props'), exist_ok=True)
    Image.fromarray(bleed(im.crop((BX0, 0, BX1, 1024)))).resize((128, 1024), Image.LANCZOS).save(R('textures', 'props', 'bow_basecolor.png'))
    Image.fromarray(bleed(im.crop((AX0, AY0, AX1, AY1)))).resize((1024, 128), Image.LANCZOS).save(R('textures', 'props', 'arrow_basecolor.png'))
    limb, arrow = {}, {}
    for r in range(TOP, BOT + 1):
        rr = [(a + BX0, b + BX0) for a, b in runs(A[r, BX0:BX1])]
        rr = [(a, b) for a, b in rr if not (b - a <= 8 and abs((a + b) / 2 - STRING_X) < 6)]   # drop the bare string
        if rr:
            limb[r] = [min(a for a, _ in rr), max(b for _, b in rr)]
    for x in range(AX0, AX1):
        ys = np.nonzero(A[AY0:AY1, x])[0]
        if len(ys):
            arrow[x] = [int(ys.min() + AY0), int(ys.max() + AY0)]
    json.dump({'limb': limb, 'arrow': arrow}, open(R('textures', 'props', 'bow_rows.json'), 'w'))
    print('BOW texture and outline rows written: limb', len(limb), 'arrow', len(arrow))
    raise SystemExit
D = json.load(open(R('textures', 'props', 'bow_rows.json')))
LIMB = {int(k): v for k, v in D['limb'].items()}; ARR = {int(k): v for k, v in D['arrow'].items()}
bpy.ops.wm.read_factory_settings(use_empty=True)
LIMB_XC = (LIMB[GRIP_ROW][0] + LIMB[GRIP_ROW][1]) / 2


def material(name, img):
    m = bpy.data.materials.new(name); m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    t = m.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(R('textures', 'props', img))
    m.node_tree.links.new(t.outputs['Color'], bsdf.inputs['Base Color']); return m


def finish(bm, name, mat):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    return o


def tube(bm, uvl, rings, closed_ends=True):
    """rings: list of (list of (vert position), list of uv)); quads between consecutive rings, caps at both ends"""
    prev = None
    for pts, uvs in rings:
        ring = [bm.verts.new(p) for p in pts]
        if prev is not None:
            (pr, puv) = prev; n = len(ring)
            for k in range(n):
                j = (k + 1) % n
                f = bm.faces.new((pr[k], pr[j], ring[j], ring[k]))
                for loop, uv in zip(f.loops, (puv[k], puv[j], uvs[j], uvs[k])):
                    loop[uvl].uv = uv
        elif closed_ends:
            f = bm.faces.new(ring[::-1])
            for loop, uv in zip(f.loops, uvs[::-1]):
                loop[uvl].uv = uv
        prev = (ring, uvs)
    if closed_ends:
        f = bm.faces.new(prev[0])
        for loop, uv in zip(f.loops, prev[1]):
            loop[uvl].uv = uv


# ------------------------------------------------------------------ bow limbs
bx = lambda x: (x - LIMB_XC) * PX                          # +X toward the string (image right)
by = lambda r: (GRIP_ROW - r) * PX
buv = lambda x, r: ((x - BX0) / (BX1 - BX0), 1.0 - r / 1024.0)
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
rows = [r for r in list(range(TOP + 3, BOT - 2, 18)) + [BOT - 3] if r in LIMB]
rings = []
for r in rows:
    lo, hi = LIMB[r]; c = (lo + hi) / 2; a = max((hi - lo) / 2, 3.0)
    zw = float(np.clip(0.8 * a * PX, 0.005, 0.02))
    pts, uvs = [], []
    for k in range(8):
        th = 2 * math.pi * k / 8
        x = c + a * math.cos(th)
        pts.append((bx(x), by(r), zw * math.sin(th))); uvs.append(buv(x, r))
    rings.append((pts, uvs))
tube(bm, uvl, rings)
bow = finish(bm, 'BowMesh', material('Bow', 'bow_basecolor.png'))
tip_t, tip_b = min(r for r in LIMB if LIMB[r][1] >= STRING_X - 2), max(r for r in LIMB if LIMB[r][1] >= STRING_X - 2)
top_tip = (bx(STRING_X), by(tip_t + 12), 0.0); bot_tip = (bx(STRING_X), by(tip_b - 12), 0.0); nock = (bx(STRING_X), 0.0, 0.0)
# ------------------------------------------------------------------ string (6-sided tube; nock ring grouped)
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); RS = 0.002
suv = buv(STRING_X, GRIP_ROW)
rings, groups = [], []
for p, g in ((top_tip, 'Bow'), (nock, 'StringNock'), (bot_tip, 'Bow')):
    rings.append(([(p[0] + RS * math.cos(2 * math.pi * k / 6), p[1], p[2] + RS * math.sin(2 * math.pi * k / 6)) for k in range(6)],
                  [suv] * 6)); groups += [g] * 6
tube(bm, uvl, rings, closed_ends=False)
me = bpy.data.meshes.new('StringMesh'); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
st = bpy.data.objects.new('StringMesh', me); bpy.context.scene.collection.objects.link(st); me.materials.append(bpy.data.materials['Bow'])
gB, gN = st.vertex_groups.new(name='Bow'), st.vertex_groups.new(name='StringNock')
for i, g in enumerate(groups):
    (gN if g == 'StringNock' else gB).add([i], 1.0, 'REPLACE')
# ------------------------------------------------------------------ arrow (origin at the nock = image right end, +Y to the point)
xs = sorted(ARR); x_point, x_nock = xs[0], xs[-1]
APX = ARROW_LEN / (x_nock - x_point)
ay_c = float(np.median([np.mean(ARR[x]) for x in xs if ARR[x][1] - ARR[x][0] < 12]))
ay = lambda x: (x_nock - x) * APX
auv = lambda x, y: ((x - AX0) / (AX1 - AX0), 1.0 - (y - AY0) / (AY1 - AY0))
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
rings = []
for x in list(range(x_nock, x_point + 60, -40)) + [x_point + 60]:
    rings.append(([(0.004 * math.cos(2 * math.pi * k / 6), ay(x), 0.004 * math.sin(2 * math.pi * k / 6)) for k in range(6)],
                  [auv(x, ay_c)] * 6))
tube(bm, uvl, rings)
for kind, (x0, x1) in (('head', (x_point, x_point + 75)), ('vane', (x_nock - 150, x_nock - 4))):
    for ang in ((0,) if kind == 'head' else (0, 2 * math.pi / 3, 4 * math.pi / 3)):
        ca, sa = math.cos(ang), math.sin(ang); strip = []
        for x in range(x0, x1 + 1, 12):
            lo, hi = ARR.get(x, (ay_c - 3, ay_c + 3)); hw = max((hi - lo) / 2, 3) * APX
            strip.append((x, hw))
        for (xa, ha), (xb, hb) in zip(strip[:-1], strip[1:]):
            if kind == 'head':
                vs = [bm.verts.new((-ha, ay(xa), 0)), bm.verts.new((ha, ay(xa), 0)), bm.verts.new((hb, ay(xb), 0)), bm.verts.new((-hb, ay(xb), 0))]
                ys_ = (ay_c + ha / APX, ay_c - ha / APX, ay_c - hb / APX, ay_c + hb / APX)
            else:
                vs = [bm.verts.new((0.004 * ca, ay(xa), 0.004 * sa)), bm.verts.new((ha * ca, ay(xa), ha * sa)),
                      bm.verts.new((hb * ca, ay(xb), hb * sa)), bm.verts.new((0.004 * ca, ay(xb), 0.004 * sa))]
                ys_ = (ay_c, ay_c - ha / APX, ay_c - hb / APX, ay_c)
            f = bm.faces.new(vs)
            for loop, xx, yy in zip(f.loops, (xa, xa, xb, xb), ys_):
                loop[uvl].uv = auv(xx, yy)
arrow = finish(bm, 'ArrowMesh', material('Arrow', 'arrow_basecolor.png'))
cb = np.array([tuple(v.co) for v in bow.data.vertices]); ca_ = np.array([tuple(v.co) for v in arrow.data.vertices])
print('BOW tris', sum(len(p.vertices) - 2 for p in bow.data.polygons), 'length', round(float(np.ptp(cb[:, 1])), 3),
      'string X', round(nock[0], 3), 'brace (string to grip front) cm', round(100 * (nock[0] - bx(LIMB[GRIP_ROW][1])), 1),
      '| ARROW tris', sum(len(p.vertices) - 2 for p in arrow.data.polygons), 'length', round(float(ca_[:, 1].max()), 3))
json.dump({'string_x': nock[0], 'top_tip': top_tip, 'bot_tip': bot_tip, 'arrow_len': float(ca_[:, 1].max()),
           'grip_half_depth': float((LIMB[GRIP_ROW][1] - LIMB[GRIP_ROW][0]) / 2 * PX)},
          open(R('textures', 'props', 'bow_geometry.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=R('work', 'props.blend'))
