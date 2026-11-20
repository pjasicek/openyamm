"""Bow, bowstring and arrow for m154 from the HD prop sheet (references_hd/bow.png: the bow vertical with its string on
image LEFT at x 336..342, rows 28..1491 = 1.30 m; one arrow on the right, point up), natm's prop route.
Prop spaces:
- Bow: +Y up the bow (the source grip axis in the fist), origin at the grip centre (reference row 778, limb centre
  x 531), +X toward the STRING (image left, so x is mirrored), +Z the limb's side. Limbs: an octagon per row, its X
  extent the reference outline (the limb's depth), Z half-width 1.6 cm at the grip tapering to 0.6 cm at the tips.
- String (separate object 'StringMesh', stays in the body mesh): two thin strips top tip -> nock -> bottom tip at
  X = the string line; the nock vertices carry the group 'StringNock', the tips 'Bow' (export_runtime.py).
- Arrow: origin at the nock (tail), +Y toward the point, 0.77 m: round shaft r 4 mm, a flat diamond head and three
  flat fletching vanes cut from the reference silhouette.
Run twice: python3 (textures, outline rows), then Blender (work/props.blend: BowMesh, StringMesh, ArrowMesh). Args: none"""
import os, json, math
import numpy as np
try:
    import bpy, bmesh
except ImportError:
    bpy = None
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(HERE, *p)
TOP, BOT, GRIP_ROW, LIMB_XC, STRING_X = 28, 1491, 778, 531.0, 339.0
PX = 1.30 / (BOT - TOP)
BX0, BX1 = 330, 600                                         # bow crop (string + limb)
AX0, AX1, AY0, AY1 = 730, 820, 360, 1260                     # arrow crop


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


if bpy is None:
    from PIL import Image
    im = Image.open(R('references_hd', 'bow.png')).convert('RGBA'); A = np.array(im)[:, :, 3]
    os.makedirs(R('textures', 'props'), exist_ok=True)
    Image.fromarray(bleed(im.crop((BX0, 0, BX1, 1536)))).resize((128, 1024), Image.LANCZOS).save(R('textures', 'props', 'bow_basecolor.png'))
    Image.fromarray(bleed(im.crop((AX0, AY0, AX1, AY1)))).resize((64, 512), Image.LANCZOS).save(R('textures', 'props', 'arrow_basecolor.png'))
    limb, arrow = {}, {}
    for r in range(TOP, BOT + 1):
        xs = np.where(A[r, 346:BX1] > 128)[0] + 346              # the limb (right of the string line)
        if len(xs):
            limb[r] = [int(xs.min()), int(xs.max())]
        xa = np.where(A[r, AX0:AX1] > 128)[0] + AX0
        if len(xa):
            arrow[r] = [int(xa.min()), int(xa.max())]
    json.dump({'limb': limb, 'arrow': arrow}, open(R('textures', 'props', 'bow_rows.json'), 'w'))
    print('BOW texture and outline rows written: limb', len(limb), 'arrow', len(arrow))
    raise SystemExit
D = json.load(open(R('textures', 'props', 'bow_rows.json')))
LIMB = {int(k): v for k, v in D['limb'].items()}; ARR = {int(k): v for k, v in D['arrow'].items()}
bpy.ops.wm.read_factory_settings(use_empty=True)


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


# ------------------------------------------------------------------ bow limbs
bx = lambda x: -(x - LIMB_XC) * PX                          # +X toward the string
by = lambda r: (GRIP_ROW - r) * PX
buv = lambda x, r: ((x - BX0) / (BX1 - BX0), 1.0 - r / 1536.0)
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
rows = [r for r in list(range(TOP + 4, BOT - 3, 24)) + [BOT - 4] if r in LIMB]
prev = None
for r in rows:
    lo, hi = LIMB[r]; c = (lo + hi) / 2; a = max((hi - lo) / 2, 2.0)
    t = abs(GRIP_ROW - r) / (GRIP_ROW - TOP); zw = 0.016 * (1 - t) + 0.006 * t
    ring = []
    for k in range(8):
        th = 2 * math.pi * k / 8
        x = c + a * math.cos(th); z = zw * math.sin(th)
        ring.append((bm.verts.new((bx(x), by(r), z)), x))
    if prev is not None:
        pr, pv = prev
        for k in range(8):
            j = (k + 1) % 8
            f = bm.faces.new((pv[k][0], pv[j][0], ring[j][0], ring[k][0]))
            for loop, (x, rr) in zip(f.loops, ((pv[k][1], pr), (pv[j][1], pr), (ring[j][1], r), (ring[k][1], r))):
                loop[uvl].uv = buv(x, rr)
    else:
        f = bm.faces.new([v for v, _ in ring][::-1])
        for loop, (_, x) in zip(f.loops, ring[::-1]):
            loop[uvl].uv = buv(x, r)
    prev = (r, ring)
f = bm.faces.new([v for v, _ in prev[1]])
for loop, (_, x) in zip(f.loops, prev[1]):
    loop[uvl].uv = buv(x, prev[0])
bow = finish(bm, 'BowMesh', material('Bow', 'bow_basecolor.png'))
top_tip = (bx(STRING_X), by(TOP + 30), 0.0); bot_tip = (bx(STRING_X), by(BOT - 30), 0.0); nock = (bx(STRING_X), 0.0, 0.0)
# ------------------------------------------------------------------ string (two strips, nock vertices grouped)
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); W = 0.0015
groups = []
for a_, b_ in ((top_tip, nock), (nock, bot_tip)):
    quad = []
    for p in (a_, b_):
        for dz in (-W, W):
            quad.append(bm.verts.new((p[0], p[1], p[2] + dz)))
    for v, p in zip(quad, (a_, a_, b_, b_)):
        groups.append('StringNock' if p is nock else 'Bow')
    f = bm.faces.new((quad[0], quad[1], quad[3], quad[2]))
    for loop in f.loops:
        loop[uvl].uv = buv(STRING_X, GRIP_ROW)
me = bpy.data.meshes.new('StringMesh'); bm.to_mesh(me); bm.free()
st = bpy.data.objects.new('StringMesh', me); bpy.context.scene.collection.objects.link(st); me.materials.append(bpy.data.materials['Bow'])
gB, gN = st.vertex_groups.new(name='Bow'), st.vertex_groups.new(name='StringNock')
for i, g in enumerate(groups):
    (gN if g == 'StringNock' else gB).add([i], 1.0, 'REPLACE')
# ------------------------------------------------------------------ arrow (origin at the nock = the tail, +Y to the point)
rs = sorted(ARR); a_top, a_bot = rs[0], rs[-1]
APX = PX
ax_c = np.mean([np.mean(ARR[r]) for r in rs if ARR[r][1] - ARR[r][0] < 25])
ay = lambda r: (a_bot - r) * APX
auv = lambda x, r: ((x - AX0) / (AX1 - AX0), 1.0 - (r - AY0) / (AY1 - AY0))
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
prev = None
for r in list(range(a_bot, a_top, -40)) + [a_top + 2]:   # shaft octagon r 4 mm
    ring = [(bm.verts.new((0.004 * math.cos(2 * math.pi * k / 6), ay(r), 0.004 * math.sin(2 * math.pi * k / 6))), k) for k in range(6)]
    if prev is not None:
        pr, pv = prev
        for k in range(6):
            j = (k + 1) % 6
            f = bm.faces.new((pv[k][0], pv[j][0], ring[j][0], ring[k][0]))
            for loop, rr in zip(f.loops, (pr, pr, r, r)):
                loop[uvl].uv = auv(ax_c, rr)
    prev = (r, ring)
for kind, (r0, r1) in (('head', (a_top, a_top + 90)), ('vane', (a_bot - 140, a_bot - 5))):
    for ang in ((0,) if kind == 'head' else (0, 2 * math.pi / 3, 4 * math.pi / 3)):
        ca, sa = math.cos(ang), math.sin(ang); strip = []
        for r in range(r0, r1 + 1, 15):
            lo, hi = ARR.get(r, (ax_c - 3, ax_c + 3)); hw = max((hi - lo) / 2, 3) * APX
            strip.append((r, hw))
        for (ra, ha), (rb, hb) in zip(strip[:-1], strip[1:]):
            if kind == 'head':
                vs = [bm.verts.new((-ha, ay(ra), 0)), bm.verts.new((ha, ay(ra), 0)), bm.verts.new((hb, ay(rb), 0)), bm.verts.new((-hb, ay(rb), 0))]
                xs_ = (ax_c - ha / APX, ax_c + ha / APX, ax_c + hb / APX, ax_c - hb / APX)
            else:
                vs = [bm.verts.new((0.004 * ca, ay(ra), 0.004 * sa)), bm.verts.new((ha * ca, ay(ra), ha * sa)),
                      bm.verts.new((hb * ca, ay(rb), hb * sa)), bm.verts.new((0.004 * ca, ay(rb), 0.004 * sa))]
                xs_ = (ax_c, ax_c + ha / APX, ax_c + hb / APX, ax_c)
            f = bm.faces.new(vs)
            for loop, x, rr in zip(f.loops, xs_, (ra, ra, rb, rb)):
                loop[uvl].uv = auv(x, rr)
arrow = finish(bm, 'ArrowMesh', material('Arrow', 'arrow_basecolor.png'))
for o in (bow, arrow):
    o.data.update()
co = np.array([tuple(v.co) for v in bow.data.vertices]); ca_ = np.array([tuple(v.co) for v in arrow.data.vertices])
print('BOW tris', sum(len(p.vertices) - 2 for p in bow.data.polygons), 'length', round(float(co[:, 1].max() - co[:, 1].min()), 3),
      'string X', round(nock[0], 3), '| ARROW tris', sum(len(p.vertices) - 2 for p in arrow.data.polygons), 'length', round(float(ca_[:, 1].max()), 3))
json.dump({'string_x': nock[0], 'top_tip': top_tip, 'bot_tip': bot_tip, 'arrow_len': float(ca_[:, 1].max())},
          open(R('textures', 'props', 'bow_geometry.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=R('work', 'props.blend'))
