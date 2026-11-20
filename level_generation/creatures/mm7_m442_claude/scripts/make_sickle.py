"""Sickle for m442 from the HD prop reference (references_hd/sickle.png: the prop alone, flat side to the camera, handle
vertical at the bottom, the crescent blade above it), natm's prop route (make_props.py / prop_textures.py): the
silhouette gives the outline, planar projection gives the texture.
Prop space: +Y along the grip toward the blade, origin at the grip centre (the solved fist, grip_solve.py), +X = image
right of the reference, +Z the blade's flat normal. LENGTH m overall (reference bbox height).
- handle: the bottom run of narrow rows centred on the handle (width < 1.6 x the median of the bottom 15 %, centre
  within 0.35 x that width), an octagon of radius R_HANDLE
  (= grip_solve.py R_HANDLE) on the handle's centre line, flat ends;
- blade: every silhouette pixel above the handle top (plus 4 % of overlap into it), traced as one outline (Moore
  boundary of the largest component, simplified to ~5 mm), filled as an n-gon, triangulated and given THICK
  thickness (both faces planar-projected from the reference; the rim takes the nearest outline colour).
Run twice: plain python3 writes textures/props/sickle_basecolor.png (bled crop, 512 px high) and
textures/props/sickle_shape.json (outline and handle in prop metres); then Blender writes work/props.blend
('SickleMesh' with 'UVMap' and an image material) and prints the triangle count. Args: none"""
import os, json, math
import numpy as np
try:
    import bpy, bmesh
except ImportError:
    bpy = None
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(HERE, *p)
LENGTH = float(os.environ.get('SICKLE_LEN', '0.46'))
R_HANDLE = float(os.environ.get('R_HANDLE', '0.014'))
THICK = 0.004

if bpy is None:
    from PIL import Image
    from scipy import ndimage
    im = Image.open(R('references_hd', 'sickle.png')).convert('RGBA')
    a = np.asarray(im); al = a[..., 3] > 128
    lab, n = ndimage.label(al); big = 1 + int(np.argmax(ndimage.sum(al, lab, range(1, n + 1)))); al = lab == big
    holes = ndimage.binary_fill_holes(al) & ~al                      # only pin-holes: the crescent's inner gap stays open
    hl, hn = ndimage.label(holes)
    for k in range(1, hn + 1):
        if (hl == k).sum() < 400:
            al |= hl == k
    ys, xs = np.where(al); y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    px = LENGTH / (y1 - y0)
    width = np.array([al[y].sum() for y in range(y0, y1 + 1)])
    ref = np.median(width[int(len(width) * 0.85):])
    cen = np.array([xs[ys == y].mean() if (ys == y).any() else np.nan for y in range(y0, y1 + 1)])
    c_ref = np.nanmedian(cen[int(len(cen) * 0.85):])
    top = y1                                                         # up the handle while narrow and centred
    while top > y0 and width[top - 1 - y0] < 1.6 * ref and abs(cen[top - 1 - y0] - c_ref) < 0.35 * ref:
        top -= 1
    cx = np.array([xs[ys == y].mean() for y in range(top, y1 + 1)])
    hx = float(np.median(cx))
    grip_y = (top + y1) / 2
    # Moore boundary trace of the blade region (rows above the handle top + overlap)
    cut = int(top + 0.04 * (y1 - top))
    bl = al.copy(); bl[cut:] = False
    lab, n = ndimage.label(bl); bl = lab == (1 + int(np.argmax(ndimage.sum(bl, lab, range(1, n + 1)))))
    sy, sx = np.argwhere(bl)[0]
    nb = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
    pts = [(sy, sx)]; cur = (sy, sx); back = 6
    for _ in range(200000):
        for k in range(8):
            d = (back + 1 + k) % 8
            ny, nx = cur[0] + nb[d][0], cur[1] + nb[d][1]
            if 0 <= ny < bl.shape[0] and 0 <= nx < bl.shape[1] and bl[ny, nx]:
                back = (d + 4) % 8; cur = (ny, nx); break
        if cur == pts[0]:
            break
        pts.append(cur)
    step = max(1, int(round(0.005 / px)))                         # ~5 mm along the outline
    P = np.array(pts[::step], np.float64)
    out = [[(p[1] - hx) * px, (grip_y - p[0]) * px] for p in P]           # prop metres: x right, y up
    crop = (int(x0) - 8, int(y0) - 8, int(x1) + 8, int(y1) + 8)
    rgb = a[..., :3].astype(np.float32); m = al.copy()
    for _ in range(30):
        acc = np.zeros_like(rgb); cnt = np.zeros(m.shape, np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            mm = np.roll(np.roll(m, dy, 0), dx, 1); acc += np.roll(np.roll(rgb, dy, 0), dx, 1) * mm[..., None]; cnt += mm
        new = (~m) & (cnt > 0); rgb[new] = acc[new] / cnt[new][:, None]; m |= new
    tex = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).crop(crop)
    h = 512; w = int(round(tex.width * h / tex.height)); w += -w % 4
    tex.resize((w, h), Image.LANCZOS).save(R('textures', 'props', 'sickle_basecolor.png'))
    json.dump({'outline': out, 'handle': {'x': 0.0, 'y_top': (grip_y - top) * px, 'y_bot': (grip_y - y1) * px,
                                          'r': R_HANDLE},
               'crop_px': crop, 'px': px, 'grip_px': [hx, grip_y], 'tex_size': [w, h]},
              open(R('textures', 'props', 'sickle_shape.json'), 'w'))
    print('SICKLE outline pts', len(out), 'handle len cm', round((y1 - top) * px * 100, 1), 'blade top cm',
          round((grip_y - y0) * px * 100, 1), 'px m', round(px, 5))
else:
    S = json.load(open(R('textures', 'props', 'sickle_shape.json')))
    px = S['px']; cx0, cy0, cx1, cy1 = S['crop_px']; gx, gy = S['grip_px']
    def uv(x, y):                                                   # prop metres -> crop texture uv (planar)
        ix = gx + x / px; iy = gy - y / px
        return ((ix - cx0) / (cx1 - cx0), 1 - (iy - cy0) / (cy1 - cy0))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    O = S['outline']
    fr = [bm.verts.new((x, y, THICK / 2)) for x, y in O]
    bk = [bm.verts.new((x, y, -THICK / 2)) for x, y in O]
    # explicit ear clipping of the concave crescent (bmesh's n-gon fill covered 3x the outline's area)
    P2 = np.array(O); n_ = len(P2)
    if sum(P2[i, 0] * P2[(i + 1) % n_, 1] - P2[(i + 1) % n_, 0] * P2[i, 1] for i in range(n_)) < 0:
        order = list(range(n_))[::-1]
    else:
        order = list(range(n_))
    cross = lambda a, b, c: (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    def inside(p, a, b, c):
        return cross(a, b, p) >= 0 and cross(b, c, p) >= 0 and cross(c, a, p) >= 0
    tris, poly = [], order[:]
    while len(poly) > 3:
        for k in range(len(poly)):
            i0, i1, i2 = poly[k - 1], poly[k], poly[(k + 1) % len(poly)]
            a_, b_, c_ = P2[i0], P2[i1], P2[i2]
            if cross(a_, b_, c_) <= 1e-12:
                continue
            if any(inside(P2[q], a_, b_, c_) for q in poly if q not in (i0, i1, i2)):
                continue
            tris.append((i0, i1, i2)); poly.pop(k); break
        else:
            break                                                  # degenerate rest: stop
    tris.append(tuple(poly[:3]))
    for i0, i1, i2 in tris:
        bm.faces.new((fr[i0], fr[i1], fr[i2])); bm.faces.new((bk[i2], bk[i1], bk[i0]))
    for i in range(len(O)):
        j = (i + 1) % len(O)
        bm.faces.new((fr[i], bk[i], bk[j], fr[j]) if order[0] == 0 else (fr[j], bk[j], bk[i], fr[i]))
    H = S['handle']; r = H['r']; ring = []
    for y in (H['y_bot'], H['y_top']):
        ring.append([bm.verts.new((r * math.cos(t), y, r * math.sin(t))) for t in np.linspace(0, 2 * math.pi, 8, endpoint=False)])
    hf = [bm.faces.new((ring[0][k], ring[0][(k + 1) % 8], ring[1][(k + 1) % 8], ring[1][k])) for k in range(8)]
    hf.append(bm.faces.new(list(reversed(ring[0])))); hf.append(bm.faces.new(ring[1]))
    for f in bm.faces:
        for l in f.loops:
            co = l.vert.co
            if f in hf:                                              # handle: projected from the reference's handle strip
                l[uvl].uv = uv(co.x * 0.6, co.y)
            else:
                l[uvl].uv = uv(co.x, co.y)
    bm.normal_update()
    me = bpy.data.meshes.new('SickleMesh'); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new('SickleMesh', me); bpy.context.scene.collection.objects.link(ob)
    m = bpy.data.materials.new('Sickle'); m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    t = m.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(R('textures', 'props', 'sickle_basecolor.png'))
    m.node_tree.links.new(t.outputs['Color'], bsdf.inputs['Base Color']); me.materials.append(m)
    print('PROP SickleMesh tris', sum(len(p.vertices) - 2 for p in me.polygons))
    bpy.ops.wm.save_as_mainfile(filepath=R('work', 'props.blend'))
