"""Flamberge and round shield for m150 from the HD prop sheets (references_hd/sword.png left view = broad side, drawn
diagonally; references_hd/shield.png left view = exterior three-quarter, right view = inner three-quarter), natm's
prop route: silhouette rows give the outline, planar projection gives the texture.

Sword prop space (as m406's): +Y along the grip toward the tip, origin at the grip centre, +X toward the edge (image
right of the straightened sheet; double-edged), +Z the flat normal. The sheet's sword axis is found by PCA of its
alpha and the image turned so the tip points up; then per row: blade = diamond section (4 mm half thickness at the
ridge) following the wavy outline; guard = flat bar; grip = octagon of radius R_HANDLE (the solved fist); pommel round.
Overall length SWORD_LEN.
Shield prop space: origin on the forearm axis at the strap, +Y along the forearm toward the hand, +Z out of the shield
face (exterior), X completes it. A dish of radius SHIELD_R (dome depth DOME, a raised boss and a rolled rim, 7 mm
shell), its inner apex STRAP_GAP in front of the forearm; 12 rim studs. Texture: the exterior and the inner views
are unskewed from their fitted ellipses onto circles, side by side in one atlas (front u 0..0.5, back 0.5..1).
Run twice: plain python3 writes textures/props/*_basecolor.png and the outline json; Blender writes work/props.blend
('SwordMesh', 'ShieldMesh', each with 'UVMap' and its own image material). Args: none"""
import os, json, math
import numpy as np
try:
    import bpy, bmesh
except ImportError:
    bpy = None
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(HERE, *p)
E = lambda k, d: float(os.environ.get(k, d))
SWORD_LEN, R_HANDLE = E('SWORD_LEN', 1.15), E('R_HANDLE', 0.013)
SHIELD_R, DOME, STRAP_GAP = E('SHIELD_R', 0.31), E('DOME', 0.07), E('STRAP_GAP', 0.06)


def bleed(rgb, al, rounds=60):
    rgb = rgb.astype(np.float32).copy(); al = al.copy()
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
    from scipy import ndimage
    os.makedirs(R('textures', 'props'), exist_ok=True)
    # ---------------------------------------------------------------- sword: straighten the broad-side view
    im = Image.open(R('references_hd', 'sword.png')).convert('RGBA'); A = np.array(im)
    lab, n = ndimage.label(A[:, :, 3] > 128); sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    objs = ndimage.find_objects(lab); xs = [objs[i][1].start for i in range(n)]
    big = sorted(np.argsort(-sizes)[:2], key=lambda i: xs[i])[0] + 1          # the left (broad-side) view
    ys, xs_ = np.where(lab == big); P = np.column_stack([xs_, ys]).astype(float); c = P.mean(0)
    u = np.linalg.svd(P - c, full_matrices=False)[2][0]   # full U of 79k points = 50 GB
    if u[1] > 0:                                                               # point the axis up the image (tip)
        u = -u
    ang = math.degrees(math.atan2(u[0], -u[1]))                               # clockwise from up
    one = A.copy(); one[lab != big] = 0
    rot = Image.fromarray(one).rotate(ang, resample=Image.BICUBIC, expand=True)   # the diagonal sword is longer than the sheet
    ra = np.array(rot); al = ra[:, :, 3] > 128
    yy, xx = np.where(al); x0, x1, y0, y1 = xx.min() - 4, xx.max() + 5, yy.min(), yy.max() + 1
    crop = ra[y0:y1, x0:x1]
    # which end is the tip: the narrower end
    w_top = (crop[:40, :, 3] > 128).sum(1).mean(); w_bot = (crop[-40:, :, 3] > 128).sum(1).mean()
    if w_top > w_bot:
        crop = crop[::-1, ::-1].copy()
    H = crop.shape[0]
    rows = {}
    for r in range(H):
        s = np.where(crop[r, :, 3] > 128)[0]
        if len(s):
            rows[r] = [int(s.min()), int(s.max())]
    widths = np.array([rows[r][1] - rows[r][0] if r in rows else 0 for r in range(H)])
    # guard = the widest rows in the lower third; grip below it; pommel = the widening at the very end
    low = np.arange(int(H * 0.6), H)
    g = low[np.argmax(widths[low])]
    gs = [r for r in low if widths[r] > 0.6 * widths[g]]
    guard0, guard1 = min(gs), max(gs)
    grip = np.arange(guard1 + 1, H)
    gw = float(np.median(widths[guard1 + 15:guard1 + 80]))
    pom0 = next((r for r in grip if r > guard1 + 15 and widths[r] > 1.4 * gw), H - 30)
    prof = {'H': H, 'W': int(crop.shape[1]), 'guard': [int(guard0), int(guard1)], 'pommel': int(pom0), 'rows': rows,
            'angle_deg': ang}
    json.dump(prof, open(R('textures', 'props', 'sword_rows.json'), 'w'))
    Image.fromarray(bleed(crop[:, :, :3], crop[:, :, 3] > 128)).resize((256, 1024), Image.LANCZOS).save(
        R('textures', 'props', 'sword_basecolor.png'))
    print('SWORD sheet turned', round(ang, 1), 'deg; rows', H, 'guard', guard0, guard1, 'pommel', pom0)
    # ---------------------------------------------------------------- shield: unskew both views onto circles
    im = Image.open(R('references_hd', 'shield.png')).convert('RGBA'); A = np.array(im)
    lab, n = ndimage.label(A[:, :, 3] > 128); sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    two = sorted(np.argsort(-sizes)[:2] + 1, key=lambda i: np.where(lab == i)[1].mean())
    atlas = np.zeros((1024, 2048, 3), np.uint8)
    for k, comp in enumerate(two):                                            # 0 exterior (left), 1 inner (right)
        ys, xs_ = np.where(lab == comp); P = np.column_stack([xs_, ys]).astype(float); c = P.mean(0)
        C = np.cov((P - c).T); ev, V = np.linalg.eigh(C)
        # the boundary of a uniformly filled ellipse: semi-axis = 2 sqrt(eigenvalue)
        ax = 2 * np.sqrt(ev)
        S = V @ np.diag(1.0 / ax) @ V.T                                       # ellipse -> unit circle
        Si = np.linalg.inv(S)
        # the views are three-quarter: the boss is not at the ellipse centre. Resample radially: texture radius rho at
        # angle th samples the line from the boss centre (gold, inside rho_ellipse < 0.55) to the fitted rim point
        rel = (S @ (P - c).T).T; rho_e = np.linalg.norm(rel, axis=1)
        rgbP = A[ys, xs_, :3].astype(float); mx = rgbP.max(1); mn = rgbP.min(1)
        gold = (rho_e < 0.55) & (mx > 120) & ((mx - mn) / np.maximum(mx, 1) > 0.35) & (rgbP[:, 0] > rgbP[:, 2] * 1.3)
        boss = P[gold].mean(0) if gold.sum() > 50 else c
        gy, gx = np.mgrid[0:1024, 0:1024]
        qx = (gx - 511.5) / 511.5; qy = -(gy - 511.5) / 511.5
        if k == 1:
            qx = -qx                                                          # the inner face is seen from behind
        rho = np.sqrt(qx ** 2 + qy ** 2); th = np.arctan2(qy, qx)
        rim = (Si @ np.stack([np.cos(th).ravel(), -np.sin(th).ravel()])).T + c   # image y points down
        src = boss + (rim - boss) * np.minimum(rho, 1.0).ravel()[:, None]
        sx = np.clip(src[:, 0].round().astype(int), 0, A.shape[1] - 1); sy = np.clip(src[:, 1].round().astype(int), 0, A.shape[0] - 1)
        print('SHIELD view', k, 'boss px', np.round(boss, 1), 'ellipse centre', np.round(c, 1))
        rgb = A[sy, sx, :3].reshape(1024, 1024, 3); a = (A[sy, sx, 3] > 128).reshape(1024, 1024)
        atlas[:, k * 1024:(k + 1) * 1024] = bleed(rgb, a)
        print('SHIELD view', k, 'ellipse semi-axes px', np.round(ax, 1), 'centre', np.round(c, 1))
    Image.fromarray(atlas).resize((1024, 512), Image.LANCZOS).save(R('textures', 'props', 'shield_basecolor.png'))
    raise SystemExit

# ===================================================================================================== Blender part
prof = json.load(open(R('textures', 'props', 'sword_rows.json')))
rows = {int(k): v for k, v in prof['rows'].items()}; H, W = prof['H'], prof['W']
g0, g1 = prof['guard']; pom = prof['pommel']
PX = SWORD_LEN / H
grip_rows = [r for r in range(g1 + 1, pom) if r in rows]
GRIP_X = float(np.mean([np.mean(rows[r]) for r in grip_rows]))
GRIP_ROW = (g1 + pom) / 2.0
uvs = lambda x, r: (x / W, 1.0 - r / H)
Pt = lambda x, r, z: ((x - GRIP_X) * PX, (GRIP_ROW - r) * PX, z)
bpy.ops.wm.read_factory_settings(use_empty=True)


def image_material(name, f):
    m = bpy.data.materials.new(name); m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    t = m.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(R('textures', 'props', f))
    m.node_tree.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
    return m


bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
tip_r = min(rows)


def section(r):
    lo, hi = rows[r]
    if r < g0:                                                                # blade: diamond, both edges sharp
        t = 0.004 * min(1.0, (r - tip_r) / 60.0) + 0.0003
        c = (lo + hi) / 2
        return [(hi, 0.0), (c, t), (lo, 0.0), (c, -t)]
    if r <= g1:                                                               # guard: flat bar
        return [(hi, 0.0), (hi - 2, 0.007), (lo + 2, 0.007), (lo, 0.0), (lo + 2, -0.007), (hi - 2, -0.007)]
    c = (lo + hi) / 2
    rad = R_HANDLE if r < pom else min(0.022, (hi - lo) / 2 * PX)
    return [(GRIP_X + rad / PX * math.cos(a), rad * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)]


blade_rows = list(range(tip_r + 4, g0, max(4, (g0 - tip_r) // 34))) + [g0 - 1]
sel = blade_rows + [g0, (g0 + g1) // 2, g1] + list(np.linspace(g1 + 2, pom - 1, 5).astype(int)) + \
      list(np.linspace(pom, max(rows) - 2, 4).astype(int))
sel = [r for r in sel if r in rows]
prev = None
for r in sel:
    cur = [(bm.verts.new(Pt(x, r, z)), x) for x, z in section(r)]
    if prev is not None:
        pr, pv = prev
        if len(pv) == len(cur):
            n = len(cur)
            for i in range(n):
                j = (i + 1) % n
                f = bm.faces.new((pv[i][0], pv[j][0], cur[j][0], cur[i][0]))
                for loop, (x, rr) in zip(f.loops, ((pv[i][1], pr), (pv[j][1], pr), (cur[j][1], r), (cur[i][1], r))):
                    loop[uvl].uv = uvs(x, rr)
        else:
            for ring, rr, rev in ((pv, pr, False), (cur, r, True)):
                vs = [v for v, _ in ring]
                f = bm.faces.new(vs[::-1] if rev else vs)
                for loop, (_, x) in zip(f.loops, (ring[::-1] if rev else ring)):
                    loop[uvl].uv = uvs(x, rr)
    else:
        lo, hi = rows[tip_r]
        tip = bm.verts.new(Pt((lo + hi) / 2, tip_r, 0.0)); n = len(cur)
        for i in range(n):
            j = (i + 1) % n
            f = bm.faces.new((tip, cur[j][0], cur[i][0]))
            for loop, (x, rr) in zip(f.loops, (((lo + hi) / 2, tip_r), (cur[j][1], r), (cur[i][1], r))):
                loop[uvl].uv = uvs(x, rr)
    prev = (r, cur)
end = [v for v, _ in prev[1]]
f = bm.faces.new(end[::-1])
for loop in f.loops:
    loop[uvl].uv = uvs(GRIP_X, H - 1)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new('SwordMesh'); bm.to_mesh(me); bm.free()
sw = bpy.data.objects.new('SwordMesh', me); bpy.context.scene.collection.objects.link(sw)
me.materials.append(image_material('Sword', 'sword_basecolor.png'))
for p in me.polygons:
    p.use_smooth = True
co = np.array([tuple(v.co) for v in me.vertices])
print('SWORD tris', sum(len(p.vertices) - 2 for p in me.polygons), 'length m', round(float(np.ptp(co[:, 1])), 3),
      'tip y', round(float(co[:, 1].max()), 3), 'width m', round(float(np.ptp(co[:, 0])), 3))

# ---------------------------------------------------------------- shield
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
SEG = 20
RINGS = [0.035, 0.06, 0.075, 0.13, 0.19, 0.25, 0.29]                 # radii (m); the rim at SHIELD_R follows


def zf(r):
    """front surface height above the inner apex plane (dome + boss), r in m"""
    z = DOME * (1 - (r / SHIELD_R) ** 2)
    if r < 0.075:
        z += 0.028 * math.cos(math.pi / 2 * r / 0.075)
    return z


rad = [r for r in RINGS if r < SHIELD_R - 0.01] + [SHIELD_R]
TH = 0.007
centre = (0.0, 0.0, STRAP_GAP - DOME)                                   # apex plane offset so the inner apex sits at STRAP_GAP


def P3(r, a, z):
    return (r * math.cos(a), r * math.sin(a), z + centre[2])


front, back = [], []
for r in rad:
    fr, bk = [], []
    for i in range(SEG):
        a = 2 * math.pi * i / SEG
        fr.append(bm.verts.new(P3(r, a, zf(r) + TH)))
        bk.append(bm.verts.new(P3(r * 0.985, a, DOME * (1 - (r / SHIELD_R) ** 2))))
    front.append(fr); back.append(bk)
uvF = lambda v: (0.25 + v.co.x / SHIELD_R * 0.25 * 0.97, 0.5 + v.co.y / SHIELD_R * 0.5 * 0.97)
uvB = lambda v: (0.75 + v.co.x / SHIELD_R * 0.25 * 0.97, 0.5 + v.co.y / SHIELD_R * 0.5 * 0.97)


def quad(vs, fn, flip=False):
    f = bm.faces.new(vs[::-1] if flip else vs)
    for loop in f.loops:
        loop[uvl].uv = fn(loop.vert)


for k in range(len(rad) - 1):
    for i in range(SEG):
        j = (i + 1) % SEG
        a, b, c, d = front[k][i], front[k][j], front[k + 1][j], front[k + 1][i]
        quad([a, d, c, b], uvF)
        a, b, c, d = back[k][i], back[k][j], back[k + 1][j], back[k + 1][i]
        quad([a, b, c, d], uvB)
# centre caps: the boss top ring as one polygon each side (triangulated below)
quad([front[0][i] for i in range(SEG)][::-1], uvF)
quad([back[0][i] for i in range(SEG)], uvB)
# rim: front edge -> back edge
for i in range(SEG):
    j = (i + 1) % SEG
    quad([front[-1][i], front[-1][j], back[-1][j], back[-1][i]], uvF)
# studs on the rim front
for i in range(12):
    a = 2 * math.pi * (i + 0.5) / 12; r0 = SHIELD_R * 0.93
    cz = zf(r0) + TH
    ring = []
    for q in range(4):
        b = a + math.pi / 2 * q
        ring.append(bm.verts.new((r0 * math.cos(a) + 0.012 * math.cos(b), r0 * math.sin(a) + 0.012 * math.sin(b), cz + centre[2] - 0.002)))
    top = bm.verts.new((r0 * math.cos(a), r0 * math.sin(a), cz + centre[2] + 0.022))
    for q in range(4):
        quad([ring[q], ring[(q + 1) % 4], top], uvF)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bmesh.ops.triangulate(bm, faces=bm.faces)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new('ShieldMesh'); bm.to_mesh(me); bm.free()
# prop space: the dish was built about +Z; +Y along the forearm toward the hand is the dish's +Y
sh = bpy.data.objects.new('ShieldMesh', me); bpy.context.scene.collection.objects.link(sh)
me.materials.append(image_material('Shield', 'shield_basecolor.png'))
for p in me.polygons:
    p.use_smooth = True
co = np.array([tuple(v.co) for v in me.vertices])
print('SHIELD tris', sum(len(p.vertices) - 2 for p in me.polygons), 'diameter m', round(float(np.ptp(co[:, 0])), 3),
      'z range', round(float(co[:, 2].min()), 3), round(float(co[:, 2].max()), 3))
bpy.ops.wm.save_as_mainfile(filepath=R('work', 'props.blend'))
