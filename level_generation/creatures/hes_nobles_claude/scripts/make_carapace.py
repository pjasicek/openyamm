"""Noble carapace (hes_nobles_claude, copied from hes_kreegan_claude/make_armour.py via the Overseer project; the
projection ignores the body's ivory spurs/claws (attribute 'ivory', mark_ivory.py) unless a plate sets keep_ivory,
materials NB_Plate / NB_Glow, layout work/carapace_layout.json). Original notes: rigid ivory chitin-ceramic plates (concept fam_troopers.png / 07_kreegan_castes.png), one object per
plate, each 100 % on one bone, so every plate splits into its own attachment GLB on that bone's node
(actors.yml `attachments`; the engine has no skinned attachments, so nothing here deforms).

Each plate is a projected shell: a grid over its outline in a parameter domain is cast onto the rest-pose body
(outermost hit, the whole body incl. spikes, straps and the chest ornament), smoothed (Laplacian on the grid) and pushed
out to at least OFF from the skin (BVH nearest), then thickened by T outward (inner surface, outer surface, a closed
rim); the outer surface's two outermost rings are lifted by LIP (the gold-trimmed edge). Domains:
- 'plane': u = x, v = z, rays along +Y (front) or -Y (back);
- 'cyl': u = angle about the bone axis (0 = the bone frame's REF direction, toward +X of the reference), v = fraction
  along the bone (head 0, child joint 1), rays from outside toward the axis;
- 'cap': u = azimuth, v = elevation about a centre (pauldrons), rays toward the centre.
Rows: v from v0 to v1 in NV steps; each row spans u in [lo(v), hi(v)] (piecewise linear tables), NU columns.
flat_rows: each row at its highest skin height (a stiff plate that does not follow creases across it).
Glow seams: polylines in normalised plate coordinates (s across 0..1, r along 0..1), a 7 mm strip GLOW_H above the
outer surface, material HKR_Glow; studs: small octagons. UVs: the outer surface fills the plate's rect of the armour
atlas (rect size proportional to the plate's physical extent, one texel density for all plates), the inner surface
and rim take a shared dark strip. Writes work/armour.blend (objects Arm_<name>, vertex group = bone, custom props
bone/kind) and work/armour_layout.json (rects, per-plate size in metres) for armour_texture.py.
Args: -- <rig blend> [plates json] [out blend]"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = json.load(open(a[1] if len(a) > 1 else os.path.join(HERE, 'scripts', 'carapace_noble.json')))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
CO = [body.matrix_world @ v.co for v in me.vertices]
TREE_ALL = BVHTree.FromPolygons([tuple(c) for c in CO], [tuple(p.vertices) for p in me.polygons])
for o in [o for o in bpy.data.objects if o.name.startswith('Arm_')]:
    bpy.data.objects.remove(o, do_unlink=True)
ATLAS = SPEC.get('atlas', 1024); DENS = SPEC.get('texels_per_m', 1400)


def interp(tab, v):
    xs = [p[0] for p in tab]; ys = [p[1] for p in tab]
    return float(np.interp(v, xs, ys))


def bone_frame(bn, ref):
    b = rig.data.bones[bn]
    h = Vector(b.head_local)
    child = SPEC_CHILD.get(bn)
    t = Vector(rig.data.bones[child].head_local) if child else Vector(b.tail_local)
    ax = (t - h).normalized()
    r = Vector(ref); r = (r - ax * r.dot(ax)).normalized(); s = ax.cross(r)
    return h, t, ax, r, s


SPEC_CHILD = {}
for s_ in 'LR':
    SPEC_CHILD.update({f'B_{s_}_UpperArm': f'B_{s_}_Forearm', f'B_{s_}_Forearm': f'B_{s_}_Hand',
                       f'B_{s_}_Thigh': f'B_{s_}_Calf', f'B_{s_}_Calf': f'B_{s_}_Foot', f'B_{s_}_Clavicle': f'B_{s_}_UpperArm'})


def ray_for(pl, u, v):
    k = pl['kind']
    if k == 'plane':
        d = Vector((0, 1, 0)) if pl.get('side', 'front') == 'front' else Vector((0, -1, 0))
        return Vector((u, -d.y * 1.0, v)) , d, None
    if k == 'cyl':
        h, t, ax, r, s = pl['_frame']
        c = h + (t - h) * v
        dirv = r * math.cos(u) + s * math.sin(u)
        return c + dirv * 0.5, -dirv, c
    if k == 'cap':
        c = Vector(pl['centre']); ref = Vector(pl['out']).normalized(); up = Vector((0, 0, 1))
        side = up.cross(ref).normalized(); up2 = ref.cross(side)
        dirv = (ref * math.cos(u) + side * math.sin(u)) * math.cos(v) + up2 * math.sin(v)
        return c + dirv * 0.6, -dirv, c
    raise ValueError(k)


def outward(pl, p, c):
    k = pl['kind']
    if k == 'plane':
        return Vector((0, -1, 0)) if pl.get('side', 'front') == 'front' else Vector((0, 1, 0))
    return (p - c).normalized() if c is not None else Vector((0, 0, 1))


layout = {'atlas': ATLAS, 'plates': {}}
cursor = [4, 4, 0]                                   # x, y, row height (shelf packing)
mat_plate = bpy.data.materials.get('NB_Plate') or bpy.data.materials.new('NB_Plate')
mat_glow = bpy.data.materials.get('NB_Glow') or bpy.data.materials.new('NB_Glow')
report = {}
if 'piece' not in me.attributes: me.attributes.new('piece', 'INT', 'POINT')
PIECE = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', PIECE)
IVORY = np.zeros(len(me.vertices), np.int32); me.attributes['ivory'].data.foreach_get('value', IVORY)
GI = {g.index: g.name for g in body.vertex_groups}
DOM = [GI[max(v.groups, key=lambda g: g.weight).group] if v.groups else None for v in me.vertices]
COA = np.array([tuple(c) for c in CO])


def to_param(pl, X):
    """skin points -> (u, v, h) in the plate's domain; h = height above the domain's base (larger = further out)"""
    k = pl['kind']
    if k == 'plane':
        fr = pl.get('side', 'front') == 'front'
        return X[:, 0], X[:, 2], (-X[:, 1] if fr else X[:, 1])
    if k == 'cyl':
        h, t, ax, r, s_ = (np.array(x) for x in pl['_frame'])
        L = np.linalg.norm(t - h); rel = X - h; al = rel @ ax
        perp = rel - np.outer(al, ax)
        return np.arctan2(perp @ s_, perp @ r), al / L, np.linalg.norm(perp, axis=1)
    if k == 'cap':
        c, ref, side, up2 = (np.array(x) for x in cap_frame(pl))
        rel = X - c; d = np.linalg.norm(rel, axis=1); n_ = rel / d[:, None]
        el = np.arcsin(np.clip(n_ @ up2, -1, 1)); az = np.arctan2(n_ @ side, n_ @ ref)
        return az, el, d


def from_param(pl, u, v, hgt):
    k = pl['kind']
    if k == 'plane':
        fr = pl.get('side', 'front') == 'front'
        return np.array([u, -hgt if fr else hgt, v]), np.array([0, -1.0 if fr else 1.0, 0])
    if k == 'cyl':
        h, t, ax, r, s_ = (np.array(x) for x in pl['_frame'])
        c = h + (t - h) * v; d = r * math.cos(u) + s_ * math.sin(u)
        return c + d * hgt, d
    if k == 'cap':
        c, ref, side, up2 = (np.array(x) for x in cap_frame(pl))
        d = (ref * math.cos(u) + side * math.sin(u)) * math.cos(v) + up2 * math.sin(v)
        return c + d * hgt, d


def cap_frame(pl):
    c = Vector(pl['centre']); ref = Vector(pl['out']).normalized(); up = Vector((0, 0, 1))
    side = up.cross(ref).normalized(); up2 = ref.cross(side)
    return c, ref, side, up2


for pl in SPEC['plates']:
    name = pl['name']
    xb, xp = set(pl.get('exclude_bones', [])), set(pl.get('exclude_pieces', []))
    xb |= set(SPEC.get('exclude_bones_all', []))
    keepv = np.array([not (DOM[i] in xb or PIECE[i] in xp) for i in range(len(CO))])
    if not pl.get('keep_ivory'):
        keepv &= IVORY == 0
    if pl.get('include_bones'):
        ib = set(pl['include_bones']); keepv &= np.array([DOM[i] in ib for i in range(len(CO))])
    if pl['kind'] == 'cyl':
        pl['_frame'] = bone_frame(pl['frame_bone'] if 'frame_bone' in pl else pl['bone'], pl.get('ref', (1, 0, 0)))
    NU, NV = pl.get('nu', 9), pl.get('nv', 8)
    v0, v1 = pl['v']
    OFF, T, LIP = pl.get('off', 0.018), pl.get('t', 0.008), pl.get('lip', 0.004)
    WU, WV = pl.get('win', (0.035, 0.035) if pl['kind'] == 'plane' else ((math.radians(22), 0.07) if pl['kind'] == 'cyl' else (math.radians(16), math.radians(16))))
    U, V, Hh = to_param(pl, COA[keepv])
    if pl['kind'] != 'plane':
        pass
    dom = np.zeros((NV, NU, 2)); H = np.full((NV, NU), np.nan)
    for i in range(NV):
        v = v0 + (v1 - v0) * i / (NV - 1)
        lo, hi = interp(pl['lo'], v), interp(pl['hi'], v)
        for j in range(NU):
            u = lo + (hi - lo) * j / (NU - 1); dom[i, j] = (u, v)
            du_ = np.abs(np.angle(np.exp(1j * (U - u)))) if pl['kind'] != 'plane' else np.abs(U - u)
            m = (du_ < WU) & (np.abs(V - v) < WV)
            if pl['kind'] == 'plane':
                m &= Hh > -0.5
            if 'hmax' in pl:
                m &= Hh < pl['hmax']
            if m.any():
                H[i, j] = Hh[m].max() if 'hpct' not in pl else np.percentile(Hh[m], pl['hpct'])
    hitok = ~np.isnan(H)
    if not hitok.any():
        raise ValueError('plate ' + name + ' has no skin under it')
    for it in range(20):                                   # fill empty windows from neighbours
        if not np.isnan(H).any(): break
        for i, j in zip(*np.nonzero(np.isnan(H))):
            nb = [H[x, y] for x, y in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)) if 0 <= x < NV and 0 <= y < NU and not np.isnan(H[x, y])]
            if nb: H[i, j] = max(nb)
    if pl.get('flat_rows'):                                # a stiff plate across (the tasset): each row at its highest
        H = np.repeat(H.max(1, keepdims=True), NU, axis=1)
    H0 = H.copy()
    for it in range(pl.get('smooth', 8)):                  # upper smoothing: never below the envelope
        Q = H.copy()
        Q[1:-1, :] = 0.5 * H[1:-1, :] + 0.25 * (H[:-2, :] + H[2:, :])
        Q[:, 1:-1] = 0.5 * Q[:, 1:-1] + 0.25 * (Q[:, :-2] + Q[:, 2:])
        H = np.maximum(Q, H0)
    for it in range(pl.get('smooth2', 3)):                 # a final pass that may round off single bumps
        Q = H.copy(); Q[1:-1, 1:-1] = 0.6 * H[1:-1, 1:-1] + 0.1 * (H[:-2, 1:-1] + H[2:, 1:-1] + H[1:-1, :-2] + H[1:-1, 2:]); H = np.maximum(Q, H0 - 0.004)
    P = np.zeros((NV, NU, 3)); outn = np.zeros((NV, NU, 3))
    for i in range(NV):
        for j in range(NU):
            P[i, j], outn[i, j] = from_param(pl, dom[i, j, 0], dom[i, j, 1], H[i, j] + OFF + pl.get('crown', 0.0) * math.sin(math.pi * j / (NU - 1)))
    tree = BVHTree.FromPolygons([tuple(c) for c in CO], [tuple(p.vertices) for p in me.polygons if all(keepv[k_] for k_ in p.vertices)])
    # outward normal of the base surface (grid cross product), oriented like outn
    du = np.gradient(P, axis=1); dv = np.gradient(P, axis=0); N = np.cross(du, dv)
    N /= np.linalg.norm(N, axis=2, keepdims=True) + 1e-12
    flip = (N * outn).sum(2) < 0; N[flip] *= -1
    ring = np.minimum(np.minimum(np.arange(NV)[:, None], NV - 1 - np.arange(NV)[:, None]),
                      np.minimum(np.arange(NU)[None, :], NU - 1 - np.arange(NU)[None, :]))
    lift = np.where(ring == 0, LIP * 0.6, np.where(ring == 1, LIP, 0.0))
    OUT = P + N * (T + lift)[..., None]
    IN = P.copy()
    # atlas rect (physical size: mean row length x mean column length)
    wlen = float(np.mean(np.linalg.norm(np.diff(OUT, axis=1), axis=2).sum(1)))
    hlen = float(np.mean(np.linalg.norm(np.diff(OUT, axis=0), axis=2).sum(0)))
    rw, rh = max(16, int(round(wlen * DENS))), max(16, int(round(hlen * DENS)))
    if cursor[0] + rw + 4 > ATLAS:
        cursor[0] = 4; cursor[1] += cursor[2] + 8; cursor[2] = 0
    rect = (cursor[0], cursor[1], rw, rh); cursor[0] += rw + 8; cursor[2] = max(cursor[2], rh)
    layout['plates'][name] = {'rect': rect, 'size_m': [wlen, hlen], 'nu': NU, 'nv': NV, 'bone': pl['bone'],
                              'glow': pl.get('glow', []), 'studs': pl.get('studs', []), 'style': pl.get('style', 'plate'),
                              'tier': pl.get('tier'), 'paint_glow': pl.get('paint_glow', []),
                              'paint_studs': pl.get('paint_studs', [])}
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    VO = [[bm.verts.new(OUT[i, j]) for j in range(NU)] for i in range(NV)]
    VI = [[bm.verts.new(IN[i, j]) for j in range(NU)] for i in range(NV)]
    def uv_out(i, j):
        s = j / (NU - 1); r = i / (NV - 1)
        return ((rect[0] + s * rect[2]) / ATLAS, 1 - (rect[1] + (1 - r) * rect[3]) / ATLAS)
    DARK = ((ATLAS - 12) / ATLAS, 1 - (ATLAS - 12) / ATLAS)
    faces_out, faces_in, faces_rim = [], [], []
    for i in range(NV - 1):
        for j in range(NU - 1):
            q = (VO[i][j], VO[i][j + 1], VO[i + 1][j + 1], VO[i + 1][j])
            f = bm.faces.new(q); faces_out.append((f, i, j))
            for l, (ii, jj) in zip(f.loops, ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j))):
                l[uvl].uv = uv_out(ii, jj)
            f2 = bm.faces.new((VI[i][j], VI[i + 1][j], VI[i + 1][j + 1], VI[i][j + 1])); faces_in.append((f2, i, j))
            for l in f2.loops: l[uvl].uv = DARK
    border = [(0, j) for j in range(NU - 1)] + [(i, NU - 1) for i in range(NV - 1)] + \
             [(NV - 1, j) for j in range(NU - 1, 0, -1)] + [(i, 0) for i in range(NV - 1, 0, -1)]
    for k in range(len(border)):
        (i0, j0), (i1, j1) = border[k], border[(k + 1) % len(border)]
        f = bm.faces.new((VO[i0][j0], VI[i0][j0], VI[i1][j1], VO[i1][j1])); faces_rim.append(f)
        for l, (ii, jj) in zip(f.loops, ((i0, j0), (i0, j0), (i1, j1), (i1, j1))):
            l[uvl].uv = uv_out(ii, jj)                           # the rim shares the gold edge texels
    bm.normal_update()
    # orient: outer faces along N, inner against it; rim outward from the plate centre
    for f, i, j in faces_out:
        if f.normal.dot(Vector(N[i, j])) < 0: f.normal_flip()
    for f, i, j in faces_in:
        if f.normal.dot(Vector(N[i, j])) > 0: f.normal_flip()
    for f in faces_rim:
        c = f.calc_center_median()
        k_ = int(np.argmin(np.linalg.norm(IN.reshape(-1, 3) - np.array(c), axis=1)))
        mid = Vector(IN.reshape(-1, 3).mean(0))
        if f.normal.dot(c - mid) < 0: f.normal_flip()
    # glow strips and studs on the outer surface (bilinear lookup in the grid)
    def surf(s, r, extra):
        x = s * (NU - 1); y = r * (NV - 1); j0 = min(int(x), NU - 2); i0 = min(int(y), NV - 2); fx, fy = x - j0, y - i0
        p = (OUT[i0, j0] * (1 - fx) * (1 - fy) + OUT[i0, j0 + 1] * fx * (1 - fy) + OUT[i0 + 1, j0] * (1 - fx) * fy + OUT[i0 + 1, j0 + 1] * fx * fy)
        n = (N[i0, j0] * (1 - fx) * (1 - fy) + N[i0, j0 + 1] * fx * (1 - fy) + N[i0 + 1, j0] * (1 - fx) * fy + N[i0 + 1, j0 + 1] * fx * fy)
        n /= np.linalg.norm(n)
        return Vector(p + n * extra), Vector(n)
    glow_faces = []
    GW = pl.get('glow_w', 0.007) / 2; GH = pl.get('glow_h', 0.0015)
    for line in pl.get('glow', []):
        pts = [surf(s, r, GH) for s, r in np.array([np.interp(np.linspace(0, len(line) - 1, max(2, 4 * len(line))), range(len(line)), [p[k] for p in line]) for k in (0, 1)]).T]
        prev = None
        for k, (p, n) in enumerate(pts):
            a_ = pts[max(k - 1, 0)][0]; b_ = pts[min(k + 1, len(pts) - 1)][0]
            tdir = (b_ - a_).normalized(); side = n.cross(tdir).normalized()
            cur = (bm.verts.new(p - side * GW), bm.verts.new(p + side * GW))
            if prev:
                f = bm.faces.new((prev[0], prev[1], cur[1], cur[0])); glow_faces.append(f)
                if f.normal.dot(n) < 0: f.normal_flip()
            prev = cur
    for s, r in pl.get('studs', []):
        p, n = surf(s, r, GH + 0.001); side = n.orthogonal().normalized(); up = n.cross(side)
        rr = pl.get('stud_r', 0.008)
        ring = [bm.verts.new(p + (side * math.cos(2 * math.pi * k / 6) + up * math.sin(2 * math.pi * k / 6)) * rr - n * 0.002) for k in range(6)]
        top = bm.verts.new(p + n * 0.003)
        for k in range(6):
            f = bm.faces.new((ring[k], ring[(k + 1) % 6], top)); glow_faces.append(f)
            if f.normal.dot(n) < 0: f.normal_flip()
    for f in glow_faces:
        for l in f.loops: l[uvl].uv = DARK
        f.material_index = 1
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='SHORT_EDGE')
    mesh = bpy.data.meshes.new('Arm_' + name); bm.to_mesh(mesh); bm.free()
    mesh.materials.append(mat_plate); mesh.materials.append(mat_glow)
    for p in mesh.polygons:
        p.use_smooth = p.material_index == 0
    ob = bpy.data.objects.new('Arm_' + name, mesh); bpy.context.scene.collection.objects.link(ob)
    ob['bone'] = pl['bone']; ob['kind'] = 'armour'
    ob.vertex_groups.new(name=pl['bone']).add(list(range(len(mesh.vertices))), 1.0, 'REPLACE')
    ob.parent = rig; md = ob.modifiers.new('Armature', 'ARMATURE'); md.object = rig
    # clearance at rest: min signed distance of the inner surface to the skin
    mind = min((Vector(p) - tree.find_nearest(Vector(p))[0]).dot(tree.find_nearest(Vector(p))[1]) for p in IN.reshape(-1, 3))
    report[name] = {'tris': len(mesh.polygons), 'glow_tris': sum(1 for p in mesh.polygons if p.material_index == 1),
                    'misses': int((~hitok).sum()), 'rest_min_clear_mm': round(mind * 1000, 1), 'rect': rect}
    print('PLATE', name, json.dumps(report[name]))

# ---------------------------------------------------------------- props: shaped parts (crest, buckler)


def alloc(wm, hm):
    rw, rh = max(16, int(round(wm * DENS))), max(16, int(round(hm * DENS)))
    if cursor[0] + rw + 4 > ATLAS:
        cursor[0] = 4; cursor[1] += cursor[2] + 8; cursor[2] = 0
    rect = (cursor[0], cursor[1], rw, rh); cursor[0] += rw + 8; cursor[2] = max(cursor[2], rh)
    return rect


def finish(name, bm, bone, extra, glow_faces=()):
    for f in glow_faces:
        f.material_index = 1
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='SHORT_EDGE')
    mesh = bpy.data.meshes.new('Arm_' + name); bm.to_mesh(mesh); bm.free()
    mesh.materials.append(mat_plate); mesh.materials.append(mat_glow)
    for p_ in mesh.polygons:
        p_.use_smooth = p_.material_index == 0
    ob = bpy.data.objects.new('Arm_' + name, mesh); bpy.context.scene.collection.objects.link(ob)
    ob['bone'] = bone; ob['kind'] = 'armour'
    ob.vertex_groups.new(name=bone).add(list(range(len(mesh.vertices))), 1.0, 'REPLACE')
    ob.parent = rig; md = ob.modifiers.new('Armature', 'ARMATURE'); md.object = rig
    report[name] = {'tris': len(mesh.polygons), 'glow_tris': sum(1 for q in mesh.polygons if q.material_index == 1), **extra}
    print('PLATE', name, json.dumps(report[name]))


for pr in SPEC.get('props', []):
    name = pr['name']; bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); DARK = ((ATLAS - 12) / ATLAS, 1 - (ATLAS - 12) / ATLAS)
    if pr['kind'] == 'loft':                     # a horn-like spike: centreline (Bezier), elliptic section (rx, ry), taper
        C = [np.array(c) for c in pr['ctrl']]; NS, SIDES = pr.get('nseg', 8), pr.get('sides', 8)
        bez = lambda t: ((1 - t) ** 3) * C[0] + 3 * ((1 - t) ** 2) * t * C[1] + 3 * (1 - t) * t * t * C[2] + t ** 3 * C[3]
        L_ = sum(np.linalg.norm(bez((k + 1) / 20) - bez(k / 20)) for k in range(20))
        rect = alloc(2 * math.pi * max(pr['r']) * 1.2, L_)
        rings = []
        for k in range(NS + 1):
            t = k / NS; c = bez(t); d = bez(min(1, t + 0.01)) - bez(max(0, t - 0.01)); d /= np.linalg.norm(d)
            side = np.array([1.0, 0, 0]); side = side - d * (side @ d); side /= np.linalg.norm(side); fw = np.cross(d, side)
            tap = (1 - t) ** pr.get('taper', 0.9) + 0.03
            rings.append([bm.verts.new(c + (side * math.cos(2 * math.pi * j / SIDES) * pr['r'][0] + fw * math.sin(2 * math.pi * j / SIDES) * pr['r'][1]) * tap) for j in range(SIDES)])
        tip = bm.verts.new(bez(1.0) + (bez(1.0) - bez(0.97)) / np.linalg.norm(bez(1.0) - bez(0.97)) * 0.01)
        uv = lambda t, j: ((rect[0] + rect[2] * j / SIDES) / ATLAS, 1 - (rect[1] + rect[3] * (1 - t)) / ATLAS)
        faces = []
        for k in range(NS):
            for j in range(SIDES):
                j2 = (j + 1) % SIDES
                f = bm.faces.new((rings[k][j], rings[k][j2], rings[k + 1][j2], rings[k + 1][j])); faces.append(f)
                for l, (tt, jj) in zip(f.loops, ((k / NS, j), (k / NS, j + 1), ((k + 1) / NS, j + 1), ((k + 1) / NS, j))):
                    l[uvl].uv = uv(tt, jj)
        for j in range(SIDES):
            f = bm.faces.new((rings[-1][j], rings[-1][(j + 1) % SIDES], tip)); faces.append(f)
            for l in f.loops: l[uvl].uv = uv(1.0, j + 0.5)
        f = bm.faces.new(list(reversed(rings[0]))); faces.append(f)
        for l in f.loops: l[uvl].uv = uv(0.0, 0.5)           # the hidden root cap in the spike's own strip (a dark
        #                                                       cap UV was dragged onto the sides by the far LODs)
        bmesh.ops.recalc_face_normals(bm, faces=faces)
        layout['plates'][name] = {'rect': rect, 'size_m': [2 * math.pi * max(pr['r']) * 1.2, L_], 'bone': pr['bone'], 'style': pr.get('style', 'spike')}
        finish(name, bm, pr['bone'], {'rect': rect})
    elif pr['kind'] == 'disc':                   # the buckler: a domed disc on a limb, glowing core
        h, t_, ax, rr, ss = (np.array(x) for x in bone_frame(pr.get('frame_bone', pr['bone']), (0, -1, 0)))
        cen = h + (t_ - h) * pr['v']
        out = np.array(pr['normal'], float); out /= np.linalg.norm(out)
        # sit the back of the disc just outside the limb's skin along `out`
        lim = max(((COA - cen) @ out)[np.linalg.norm((COA - cen) - np.outer((COA - cen) @ out, out), axis=1) < pr['R'] * 0.6], default=0.04)
        c0 = cen + out * (lim + pr.get('gap', 0.025))
        e1 = np.cross(out, ax); e1 /= np.linalg.norm(e1); e2 = np.cross(out, e1)
        R, TH, SEG = pr['R'], pr.get('t', 0.025), pr.get('seg', 16)
        radii = pr.get('radii', [0.30, 0.42, 0.62, 0.86, 1.0])
        rect = alloc(2 * R, 2 * R)
        def P(rho, th, z):
            return c0 + (e1 * math.cos(th) + e2 * math.sin(th)) * rho * R + out * z
        def dome(rho):
            return TH * (0.55 + 0.45 * (1 - rho * rho))
        uvp = lambda rho, th: ((rect[0] + rect[2] * (0.5 + 0.5 * rho * math.cos(th))) / ATLAS, 1 - (rect[1] + rect[3] * (0.5 - 0.5 * rho * math.sin(th))) / ATLAS)
        front = [[bm.verts.new(P(rho, 2 * math.pi * j / SEG, dome(rho))) for j in range(SEG)] for rho in radii]
        back = [bm.verts.new(P(1.0, 2 * math.pi * j / SEG, 0.0)) for j in range(SEG)]
        backc = bm.verts.new(P(0, 0, 0.0))
        core = bm.verts.new(P(0, 0, dome(0) - 0.004))
        faces = []; glow = []
        for k in range(len(radii) - 1):
            for j in range(SEG):
                j2 = (j + 1) % SEG; a0, a1 = 2 * math.pi * j / SEG, 2 * math.pi * (j + 1) / SEG
                f = bm.faces.new((front[k][j], front[k][j2], front[k + 1][j2], front[k + 1][j])); faces.append(f)
                for l, (rho, th) in zip(f.loops, ((radii[k], a0), (radii[k], a1), (radii[k + 1], a1), (radii[k + 1], a0))):
                    l[uvl].uv = uvp(rho, th)
        for j in range(SEG):                    # the glowing core: a fan of the innermost ring (glow material)
            j2 = (j + 1) % SEG
            f = bm.faces.new((core, front[0][j], front[0][j2])); faces.append(f); glow.append(f)
            for l in f.loops: l[uvl].uv = DARK
            f = bm.faces.new((front[-1][j], back[j], back[j2], front[-1][j2])); faces.append(f)
            for l, (rho, th) in zip(f.loops, ((1.0, 2 * math.pi * j / SEG), (1.0, 2 * math.pi * j / SEG), (1.0, 2 * math.pi * (j + 1) / SEG), (1.0, 2 * math.pi * (j + 1) / SEG))):
                l[uvl].uv = uvp(rho * 0.999, th)
            f = bm.faces.new((backc, back[j2], back[j])); faces.append(f)
            for l in f.loops: l[uvl].uv = DARK
        bm.normal_update()
        mid = c0 + out * TH * 0.4                                  # convex solid: every face points away from its centre
        for f in faces:
            if np.array(f.normal) @ (np.array(f.calc_center_median()) - mid) < 0: f.normal_flip()
        layout['plates'][name] = {'rect': rect, 'size_m': [2 * R, 2 * R], 'bone': pr['bone'], 'style': 'buckler', 'radii': radii}
        finish(name, bm, pr['bone'], {'rect': rect, 'centre': [round(float(x), 3) for x in c0]}, glow)

json.dump(layout, open(os.path.join(HERE, 'work', 'carapace_layout.json'), 'w'), indent=1)
print('ARMOUR plates', len(report), 'tris', sum(r['tris'] for r in report.values()), 'atlas rows used', cursor[1] + cursor[2])
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a[2]) if len(a) > 2 else os.path.join(HERE, 'work', 'carapace.blend'))
