"""Clean the Smart Topology return (work/clean_v1.blend, 2.20 m, forward -Y, character left +X) into the electrapede's
modelling mesh, work/clean_v2.blend. Pieces are classified by rule (scripts/pieces.py lists them):
- plates: the body's segment shells (one closed piece per plate). Two pieces in the middle came back as merged,
  folded plates (two and three plates in one piece, with holes): each is replaced by copies of the nearest good plate,
  one per leg pair inside it, scaled to the local width, height and pitch;
- legs: Meshy's short straight leg spikes (0.14 m) are dropped; every one becomes a procedural jointed leg (femur up
  and out to a raised knee, tibia down to a pointed foot on the floor, 6-sided tapered tubes) from the same hip, fanned
  forward at the front and back at the rear, sized by the local plate width;
- sockets: the ring bumps the legs leave from; those without a leg are dropped;
- head: every other piece in front (head shell, mouth parts, palps, antennae) scaled 1.25x about the neck so the head
  is wider than the body, as in the native frames; Meshy's four small eye bumps are replaced by two big compound-eye
  ellipsoids placed on the head's upper front by ray casts (the native's defining feature);
- tail: the small cerci at the tail tip are kept.
Small open holes are filled. Each piece is decimated by its part's ratio. Face attribute `part`: 0 plate, 1 head,
2 eye, 3 antenna, 4 leg, 5 socket, 6 cerci; face attribute `seg`: the plate/leg-pair index from the front (0 = the
neck plate), -1 for the head; face attribute `side`: +1 left, -1 right, 0 centre (legs and sockets)."""
import bpy, bmesh, os, math, json
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
ob = bpy.data.objects['Pede']
bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()

# ---- connected pieces --------------------------------------------------------------------------------------------
lab = [-1] * len(bm.verts); pieces = []
for v in bm.verts:
    if lab[v.index] >= 0:
        continue
    st = [v]; lab[v.index] = len(pieces); idx = []
    while st:
        x = st.pop(); idx.append(x.index)
        for e in x.link_edges:
            w = e.other_vert(x)
            if lab[w.index] < 0:
                lab[w.index] = lab[v.index]; st.append(w)
    pieces.append(idx)
CO = np.array([v.co[:] for v in bm.verts])
info = []
for k, idx in enumerate(pieces):
    p = CO[idx]
    info.append(dict(k=k, n=len(idx), mn=p.min(0), mx=p.max(0), c=p.mean(0)))


def kind(i):
    n, mn, mx, c = i['n'], i['mn'], i['mx'], i['c']
    ext = mx - mn
    if c[1] > 1.03 and n < 100:
        return 'cerci'
    if 60 <= n <= 130 and np.abs(np.r_[mn[0], mx[0]]).max() > 0.09 and ext[0] > 0.07 and mx[2] < 0.135 and c[1] > -0.87:
        return 'leg'
    if n < 45 and mx[2] < 0.15 and c[1] > -0.88 and abs(c[0]) > 0.015:
        return 'socket'
    if n > 140 and mn[1] > -0.98 and ext[0] > 0.06:
        return 'plate'
    if c[1] > -0.75:
        raise SystemExit(f'unclassified piece {i["k"]} at {c}')
    return 'head'


for i in info:
    i['kind'] = kind(i)
legs = sorted([i for i in info if i['kind'] == 'leg'], key=lambda i: i['c'][1])
print('KINDS', {k: sum(1 for i in info if i['kind'] == k) for k in ('plate', 'leg', 'socket', 'head', 'cerci')})

# leg pairs (front to back): hips from the leg pieces' inner ends
pairs = []
for i in legs:
    p = CO[pieces[i['k']]]
    ax = np.abs(p[:, 0]); inner = p[ax < ax.min() + 0.02].mean(0)
    i['hip'] = inner; i['side'] = 1 if i['c'][0] > 0 else -1
    if pairs and abs(pairs[-1][0]['c'][1] - i['c'][1]) < 0.05:
        pairs[-1].append(i)
    else:
        pairs.append([i])
assert all(len(p) == 2 for p in pairs), [len(p) for p in pairs]
LEG_Y = [float(np.mean([i['hip'][1] for i in p])) for p in pairs]
print('LEG_PAIRS', len(pairs), [round(y, 3) for y in LEG_Y])

# ---- plates: replace merged/folded ones -----------------------------------------------------------------------------
plates = [i for i in info if i['kind'] == 'plate']
bad = [i for i in plates if (i['mx'][1] - i['mn'][1]) > 0.22]
good = [i for i in plates if i not in bad and i['c'][1] > -0.75]
new_geom = []        # (verts list, faces list, part, seg)


def plate_dims(i):
    return (i['mx'][0] - i['mn'][0], i['mx'][2] - i['mn'][2], i['mx'][1] - i['mn'][1])


for b in bad:
    slots = [y for y in LEG_Y if b['mn'][1] < y < b['mx'][1]]
    lo = max([g for g in good if g['c'][1] < b['c'][1]], key=lambda g: g['c'][1])
    hi = min([g for g in good if g['c'][1] > b['c'][1]], key=lambda g: g['c'][1])
    print('REPLACE plate', b['k'], 'y', round(b['mn'][1], 3), round(b['mx'][1], 3), 'slots', [round(s, 3) for s in slots],
          'templates', lo['k'], hi['k'])
    for y in slots:
        j = LEG_Y.index(y)
        pitch = (LEG_Y[j + 1] - LEG_Y[j - 1]) / 2
        t = (y - lo['c'][1]) / (hi['c'][1] - lo['c'][1])
        tpl = lo if t < 0.5 else hi
        wl, hl, ll = plate_dims(lo); wh, hh, lh = plate_dims(hi); wt, ht, lt = plate_dims(tpl)
        w = wl + (wh - wl) * t; h = hl + (hh - hl) * t
        tp_y = LEG_Y[int(np.argmin([abs(tpl['c'][1] - q) for q in LEG_Y]))]
        tp_j = LEG_Y.index(tp_y)
        tp_pitch = (LEG_Y[tp_j + 1] - LEG_Y[tp_j - 1]) / 2
        sy = pitch / tp_pitch
        idx = pieces[tpl['k']]
        p = CO[idx].copy()
        zc = tpl['mn'][2]
        q = np.empty_like(p)
        q[:, 0] = p[:, 0] * (w / wt)
        q[:, 1] = (p[:, 1] - tp_y) * sy + y
        q[:, 2] = (p[:, 2] - zc) * (h / ht) + zc + ((lo['mn'][2] + (hi['mn'][2] - lo['mn'][2]) * t) - zc)
        remap = {v: n for n, v in enumerate(idx)}
        faces = [[remap[v.index] for v in f.verts] for f in bm.faces if lab[f.verts[0].index] == tpl['k']]
        new_geom.append((q, faces, 0, None, y))

# ---- remove what is replaced -----------------------------------------------------------------------------------------
eye_bumps = [i for i in info if i['kind'] == 'head' and i['n'] < 50 and i['c'][1] < -0.94
             and (i['c'][2] > 0.22 or abs(i['c'][0]) > 0.075)]
print('EYE_BUMPS', [(i['k'], [round(x, 3) for x in i['c']]) for i in eye_bumps])
sock = [i for i in info if i['kind'] == 'socket']
drop_sock = []
for s in sock:
    sd = 1 if s['c'][0] > 0 else -1
    if not any(l['side'] == sd and abs(l['hip'][1] - s['c'][1]) < 0.05 for l in legs):
        drop_sock.append(s)
print('DROP_SOCKETS', [(s['k'], round(s['c'][1], 3)) for s in drop_sock])
drop = {i['k'] for i in bad + legs + eye_bumps + drop_sock}
role = {i['k']: i['kind'] for i in info}
# per-piece seg index: nearest leg pair by y (plates, sockets); head -1; cerci last
NSEG = len(LEG_Y)


def seg_of(y):
    return int(np.argmin([abs(y - q) for q in LEG_Y]))


# face attributes on the kept original faces
for name in ('part', 'seg', 'side'):
    if name not in [a.name for a in ob.data.attributes]:
        pass
part_layer = bm.faces.layers.int.new('part'); seg_layer = bm.faces.layers.int.new('seg')
side_layer = bm.faces.layers.int.new('side')
ANT = []
for i in info:
    if i['kind'] == 'head':
        ext = i['mx'] - i['mn']
        # antennae: thin pieces reaching high above the head
        if i['mx'][2] > 0.29 and i['n'] < 140:
            ANT.append(i['k'])
print('ANTENNAE', [(k, [round(x, 3) for x in info[k]['c']]) for k in ANT])
for f in bm.faces:
    k = lab[f.verts[0].index]; r = role[k]
    c = info[k]['c']
    f[part_layer] = {'plate': 0, 'head': 1, 'socket': 5, 'cerci': 6, 'leg': 4}[r]
    if k in ANT:
        f[part_layer] = 3
    f[seg_layer] = -1 if r == 'head' else (NSEG - 1 if r == 'cerci' else seg_of(c[1]))
    f[side_layer] = (1 if c[0] > 0 else -1) if r == 'socket' else 0
bmesh.ops.delete(bm, geom=[v for v in bm.verts if lab[v.index] in drop], context='VERTS')

# ---- fill small holes on the kept pieces ------------------------------------------------------------------------------
bnd = [e for e in bm.edges if e.is_boundary]
res = bmesh.ops.holes_fill(bm, edges=bnd, sides=24)
left = sum(1 for e in bm.edges if e.is_boundary)
print('HOLES filled faces', len(res['faces']), 'boundary edges before', len(bnd), 'after', left)

# ---- head 1.25x about the neck -----------------------------------------------------------------------------------------
HEAD_PIVOT = Vector((0, -0.90, 0.16)); HS = 1.25
head_verts = {v for f in bm.faces if f[part_layer] in (1, 3) for v in f.verts}
for v in head_verts:
    v.co = HEAD_PIVOT + (v.co - HEAD_PIVOT) * HS


# ---- add new geometry ---------------------------------------------------------------------------------------------------
def add(verts, faces, part, seg, side):
    vs = [bm.verts.new(Vector(p)) for p in verts]
    out = []
    for f in faces:
        try:
            nf = bm.faces.new([vs[i] for i in f])
        except ValueError:
            continue
        nf[part_layer] = part; nf[seg_layer] = seg; nf[side_layer] = side; nf.smooth = True; out.append(nf)
    return out


for q, faces, part, _, y in new_geom:
    add(q, faces, 0, seg_of(y), 0)

# eyes: ray cast the scaled head from the front
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
head_faces = [f for f in bm.faces if f[part_layer] == 1]
hb = bmesh.new()
vm = {}
for f in head_faces:
    vv = []
    for v in f.verts:
        if v not in vm:
            vm[v] = hb.verts.new(v.co)
        vv.append(vm[v])
    try:
        hb.faces.new(vv)
    except ValueError:
        pass
tree = BVHTree.FromBMesh(hb)
hz = [v.co.z for v in vm]; hxs = [v.co.x for v in vm]
print('HEAD box x', round(min(hxs), 3), round(max(hxs), 3), 'z', round(min(hz), 3), round(max(hz), 3))
EYE_R = Vector((0.074, 0.070, 0.064))   # (across, up, along the facing axis)


def ellipsoid(center, radii, rot, nu=16, nv=10):
    verts = []; faces = []
    for j in range(1, nv):
        th = math.pi * j / nv
        for i in range(nu):
            ph = 2 * math.pi * i / nu
            p = Vector((math.sin(th) * math.cos(ph) * radii.x, math.sin(th) * math.sin(ph) * radii.y, math.cos(th) * radii.z))
            verts.append(center + rot @ p)
    top = len(verts); verts.append(center + rot @ Vector((0, 0, radii.z)))
    bot = len(verts); verts.append(center + rot @ Vector((0, 0, -radii.z)))
    for j in range(nv - 2):
        for i in range(nu):
            a = j * nu + i; b = j * nu + (i + 1) % nu; c = (j + 1) * nu + (i + 1) % nu; d = (j + 1) * nu + i
            faces.append([a, d, c, b])
    for i in range(nu):
        faces.append([top, i, (i + 1) % nu])
        last = (nv - 2) * nu
        faces.append([bot, last + (i + 1) % nu, last + i])
    return verts, faces


EX, EZ = 0.066, 0.238
hits = {sd: tree.ray_cast(Vector((sd * EX, -2.0, EZ)), Vector((0, 1, 0)))[0] for sd in (1, -1)}
ey = (hits[1].y + hits[-1].y) / 2          # Meshy's head is a little asymmetric: one depth for both eyes
for sd in (1, -1):
    surf = Vector((sd * EX, ey, EZ))
    axis = Vector((sd * 0.40, -0.88, 0.18)).normalized()      # facing forward and a little out and up
    centre = surf + Vector((sd * 0.006, 0.034, 0.0))
    rot = axis.to_track_quat('Z', 'Y').to_matrix()
    v, f = ellipsoid(centre, EYE_R, rot)
    add(v, f, 2, -1, 0)
    print('EYE', sd, 'hit', [round(x, 3) for x in hits[sd]], 'centre', [round(x, 3) for x in centre])

# procedural legs
SPLAY_F, SPLAY_B = -0.07, 0.07
plate_w = {}
for i in info:
    if i['kind'] == 'plate' and i not in bad:
        plate_w[seg_of(i['c'][1])] = i['mx'][0] - i['mn'][0]
for q, faces, part, _, y in new_geom:
    plate_w[seg_of(y)] = q[:, 0].max() - q[:, 0].min()
REF_W = 0.233
NS = 6


def tube(points, radii):
    verts = []; faces = []
    prev_n = None
    for j, (p, r) in enumerate(zip(points, radii)):
        if j == 0:
            t = (points[1] - points[0]).normalized()
        elif j == len(points) - 1:
            t = (points[-1] - points[-2]).normalized()
        else:
            t = ((points[j + 1] - points[j]).normalized() + (points[j] - points[j - 1]).normalized()).normalized()
        if prev_n is None:
            n = t.cross(Vector((0, 0, 1)))
            if n.length < 1e-4:
                n = t.cross(Vector((1, 0, 0)))
            n.normalize()
        else:
            n = (prev_n - t * prev_n.dot(t)).normalized()
        b = t.cross(n); prev_n = n
        if r <= 0:
            verts.append(p.copy()); continue
        for i in range(NS):
            a = 2 * math.pi * i / NS
            verts.append(p + (n * math.cos(a) + b * math.sin(a)) * r)
    # rings then a tip vertex
    nr = len(points) - 1
    for j in range(nr - 1):
        for i in range(NS):
            a = j * NS + i; b2 = j * NS + (i + 1) % NS
            faces.append([a, b2, b2 + NS, a + NS])
    tip = len(verts) - 1
    for i in range(NS):
        faces.append([(nr - 1) * NS + i, (nr - 1) * NS + (i + 1) % NS, tip])
    cap = list(range(NS))[::-1]
    faces.append(cap)
    return verts, faces


LEGS = []
for j, pair in enumerate(pairs):
    t = j / (len(pairs) - 1)
    splay = SPLAY_F + (SPLAY_B - SPLAY_F) * t
    k = min(1.15, plate_w.get(j, REF_W) / REF_W)
    for leg in pair:
        sd = leg['side']; H = Vector(leg['hip'])
        H = Vector((H.x - sd * 0.012, H.y, H.z))             # start inside the socket
        K = H + Vector((sd * 0.13 * k, splay * 0.45, 0.075 * k))
        F = Vector((H.x + sd * 0.27 * k, H.y + splay, 0.0))
        # tibia bows outward a little
        M1 = K.lerp(F, 0.35) + Vector((sd * 0.012 * k, 0, 0.012 * k))
        M2 = K.lerp(F, 0.70) + Vector((sd * 0.008 * k, 0, 0.004 * k))
        F1 = K.lerp(F, 0.92)
        pts = [H, H.lerp(K, 0.5), K, M1, M2, F1, F]
        rad = [0.017 * k, 0.015 * k, 0.0125 * k, 0.0105 * k, 0.008 * k, 0.005 * k, 0.0]
        v, f = tube(pts, rad)
        add(v, f, 4, j, sd)
        LEGS.append(dict(seg=j, side=sd, hip=list(H), knee=list(K), foot=list(F)))
print('LEGS', len(LEGS))

bm.normal_update()
bm.to_mesh(ob.data)
ob.data.update()
json.dump(dict(leg_y=LEG_Y, legs=LEGS, head_pivot=list(HEAD_PIVOT), head_scale=HS),
          open(os.path.join(HERE, 'work', 'clean_v2.json'), 'w'), indent=1)

# ---- decimate per part (each piece stays closed: collapse within parts) ------------------------------------------------
RATIO = {0: 0.55, 1: 0.85, 3: 1.0, 5: 0.5, 6: 0.45}
me = ob.data
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
for part, ratio in RATIO.items():
    if ratio >= 1.0:
        continue
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for p in me.polygons:
        p.select = me.attributes['part'].data[p.index].value == part
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.decimate(ratio=ratio)
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris(quad_method='SHORTEST_DIAGONAL', ngon_method='BEAUTY')
bpy.ops.object.mode_set(mode='OBJECT')
for p in me.polygons:
    p.use_smooth = True
cnt = {}
for p in me.polygons:
    k = me.attributes['part'].data[p.index].value; cnt[k] = cnt.get(k, 0) + 1
co = np.array([v.co[:] for v in me.vertices])
print('TRIS', len(me.polygons), 'by part', dict(sorted(cnt.items())), 'box', co.min(0).round(3).tolist(), co.max(0).round(3).tolist())
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v2.blend'))
