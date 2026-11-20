"""Longsword for m154 from the HD prop reference (references_hd/longsword.png, left = broad side, tip up), natm's prop
route (make_props.py / prop_textures.py): silhouette rows give the outline, planar projection gives the texture.
Prop space: +Y along the grip toward the tip, origin at the grip centre, +X toward the cutting edge (the blade's
image right; the blade is double-edged), +Z the flat normal. 1.05 m overall (reference rows 15..1483). Sections per row:
- blade (rows 15..1080): diamond section 8 mm thick at the centre ridge, both edges sharp, straight outline from
  the reference;
- guard (1080..1125): flat bar, 1.6 cm thick;
- grip (1125..1400): octagon, radius 1.3 cm (the solved fist, grip_solve.py R_HANDLE), on the reference centre line;
- pommel (1400..1483): round, radius from the outline (<= 2 cm).
Run twice: plain python3 writes textures/props/sword_basecolor.png (256 x 1024 crop of the broad side, bled)
and textures/props/sword_rows.json (outline per row); then Blender writes work/props.blend ('SwordMesh' with
'UVMap' and an image material) and prints the triangle count. Args: none"""
import os, json, math
import numpy as np
try:
    import bpy, bmesh
except ImportError:
    bpy = None
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(HERE, *p)
X0, X1, Y0, Y1 = 118, 505, 6, 1493                       # crop of the broad-side view
TOP, BOT = 15, 1483
PX = 1.05 / (BOT - TOP)
GRIP_ROW, GRIP_X = 1262, None


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
    im = Image.open(R('references_hd', 'longsword.png')).convert('RGBA')
    A = np.array(im)[:, :, 3]
    os.makedirs(R('textures', 'props'), exist_ok=True)
    bleed(im.crop((X0, Y0, X1, Y1))).resize((256, 1024), Image.LANCZOS).save(R('textures', 'props', 'sword_basecolor.png'))
    rows = {}
    for r in range(TOP, BOT + 1):
        xs = np.where(A[r, X0:X1] > 128)[0] + X0
        if len(xs):
            rows[r] = [int(xs.min()), int(xs.max())]
    json.dump(rows, open(R('textures', 'props', 'sword_rows.json'), 'w'))
    print('SWORD texture and', len(rows), 'outline rows written')
    raise SystemExit
SPANS = {int(k): tuple(v) for k, v in json.load(open(R('textures', 'props', 'sword_rows.json'))).items()}
span = lambda r: SPANS.get(r)
GRIP_X = float(np.mean([np.mean(span(r)) for r in range(1140, 1390, 10) if span(r)]))
uv = lambda x, r: ((x - X0) / (X1 - X0), 1.0 - (r - Y0) / (Y1 - Y0))
P = lambda x, r, z: ((x - GRIP_X) * PX, (GRIP_ROW - r) * PX, z)

bpy.ops.wm.read_factory_settings(use_empty=True)
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
rings = []                                                 # (row, [(vert, x_img)])


def section(r):
    s = span(r); lo, hi = s; w = hi - lo
    if r <= 1080:                                          # blade: diamond, both edges sharp
        t = 0.004 * min(1.0, (r - TOP) / 80.0) + 0.0003
        c = (lo + hi) / 2
        return [(hi, 0.0), (c, t), (lo, 0.0), (c, -t)]
    if r <= 1125:                                          # guard: flat bar
        return [(hi, 0.0), (hi - 2, 0.008), (lo + 2, 0.008), (lo, 0.0), (lo + 2, -0.008), (hi - 2, -0.008)]
    c = (lo + hi) / 2
    rad = min(0.013, w / 2 * PX) if r <= 1400 else min(0.024, w / 2 * PX)   # grip = R_HANDLE 1.3 cm
    return [(c + rad / PX * math.cos(a), rad * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)]


rows = list(range(TOP + 6, 1080, 40)) + [1080, 1088, 1100, 1112, 1122, 1128] + list(range(1155, 1401, 41)) + [1405, 1425, 1445, 1465, BOT - 3]
prev = None
for r in rows:
    sec = section(r)
    cur = [(bm.verts.new(P(x, r, z)), x) for x, z in sec]
    if prev is not None:
        pr, pv = prev
        if len(pv) == len(cur):
            n = len(cur)
            for i in range(n):
                j = (i + 1) % n
                f = bm.faces.new((pv[i][0], pv[j][0], cur[j][0], cur[i][0]))
                for loop, (x, rr) in zip(f.loops, ((pv[i][1], pr), (pv[j][1], pr), (cur[j][1], r), (cur[i][1], r))):
                    loop[uvl].uv = uv(x, rr)
        else:                                              # change of section: caps on both sides
            for ring, rr, rev in ((pv, pr, False), (cur, r, True)):
                vs = [v for v, _ in ring]
                f = bm.faces.new(vs[::-1] if rev else vs)
                for loop, (_, x) in zip(f.loops, (ring[::-1] if rev else ring)):
                    loop[uvl].uv = uv(x, rr)
    else:                                                  # tip point
        tip = bm.verts.new(P(sum(x for _, x in cur) / len(cur), TOP, 0.0))
        n = len(cur)
        for i in range(n):
            j = (i + 1) % n
            f = bm.faces.new((tip, cur[j][0], cur[i][0]))
            for loop, (x, rr) in zip(f.loops, ((sum(x for _, x in cur) / n, TOP), (cur[j][1], r), (cur[i][1], r))):
                loop[uvl].uv = uv(x, rr)
    prev = (r, cur)
end = [v for v, _ in prev[1]]
f = bm.faces.new(end[::-1])
for loop in f.loops:
    loop[uvl].uv = uv(GRIP_X, BOT)
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
      'tip y', round(float(co[:, 1].max()), 3), 'blade x range', round(float(co[:, 0].min()), 3), round(float(co[:, 0].max()), 3),
      'min face area mm2', round(min(p.area for p in me.polygons) * 1e6, 3))
json.dump({'grip_x_px': GRIP_X, 'grip_row': GRIP_ROW, 'px_m': PX}, open(R('textures', 'props', 'sword_profile.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=R('work', 'props.blend'))
