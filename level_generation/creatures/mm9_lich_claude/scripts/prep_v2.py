"""Rigged body -> final mesh before UVs: real skull in place of Meshy's old-man head, sleeve entries capped, tattered hems
(MM9's skins cut the sleeve hems by alpha; real geometry here, so no extra alpha material), per-part reduction.

Args: <in blend> <skull glb> <out blend> <report json> <config json>
"""
import bpy, bmesh, sys, json, heapq
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
IN, SKULL, OUT, REP, CFG = argv
cfg = json.load(open(CFG))
rep = {}
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = bpy.data.objects['MM9_Rig']
me = body.data
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
J = {b.name: np.array(rig.matrix_world @ b.head_local) for b in rig.data.bones}
rng = np.random.default_rng(cfg.get('seed', 9))

# ---- skull
bm = bmesh.new(); bm.from_mesh(me)
lay = bm.faces.layers.int['part']
gone = [f for f in bm.faces if f[lay] in cfg['drop_parts']]
bmesh.ops.delete(bm, geom=gone, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(me); bm.free(); me.update()

existing = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=SKULL)
new = [o for o in bpy.data.objects if o not in existing]
sk = next(o for o in new if o.type == 'MESH')
m = sk.matrix_world.copy()
for o in new:
    if o is not sk:
        sk.parent = None
sk.matrix_world = m
for o in new:
    if o is not sk:
        bpy.data.objects.remove(o)
for o in bpy.data.objects:
    o.select_set(o is sk)
bpy.context.view_layer.objects.active = sk
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
sk.data.materials.clear()
sm = sk.data
bm = bmesh.new(); bm.from_mesh(sm); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
# drop scraps and the strands Meshy strung across the open mouth
seen = {}; comps = []
for v in bm.verts:
    if v.index in seen:
        continue
    st = [v]; seen[v.index] = len(comps); c = [v]
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen[y.index] = len(comps); st.append(y); c.append(y)
    comps.append(c)
small = [v for c in comps if len(c) < 20 for v in c]
bmesh.ops.delete(bm, geom=small, context='VERTS')
gap = cfg['mouth_gap']   # normalised skull coordinates: x, y and z ranges of the open mouth in front of the molars
strand = []
for f in bm.faces:
    c = f.calc_center_median()
    if not (gap['y'][0] < c.y < gap['y'][1] and gap['z'][0] < c.z < gap['z'][1]):
        continue
    ls = [e.calc_length() for e in f.edges]
    if max(ls) > gap['long'] or all(gap['z'][0] < v.co.z < gap['z'][1] for v in f.verts):
        strand.append(f)
rep['mouth_strand_faces'] = len(strand)
bmesh.ops.delete(bm, geom=strand, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
# deepen the eye sockets (floor of the orbit pushed in); the master's ember sits deep in the socket
for e in cfg['sockets']:
    for v in bm.verts:
        d = np.hypot((v.co.x - e['x']) / e['rx'], (v.co.z - e['z']) / e['rz'])
        if d < 1 and v.co.y > e['y_floor'] and v.co.y < e['y_floor'] + 0.12:
            v.co.y += e['depth'] * (1 - d * d)
bm.to_mesh(sm); bm.free(); sm.update()
co = np.array([v.co for v in sm.vertices])
t = cfg['skull']
s = (t['z'][1] - t['z'][0]) / (co[:, 2].max() - co[:, 2].min())
co = co * s
co[:, 2] += t['z'][0] - co[:, 2].min()
co[:, 1] += t['y_front'] - co[:, 1].min()
co[:, 0] += t['x'] - 0.5 * (co[:, 0].min() + co[:, 0].max())
for v, c in zip(sm.vertices, co):
    v.co = Vector(c)
# reduce the skull on its own, teeth included
for o in bpy.data.objects:
    o.select_set(o is sk)
bpy.context.view_layer.objects.active = sk
md = sk.modifiers.new('d', 'DECIMATE'); md.ratio = t['tris'] / len(sm.polygons)
bpy.ops.object.modifier_apply(modifier=md.name)
sm = sk.data
rep['skull_tris'] = len(sm.polygons)
attr = sm.attributes.new('part', 'INT', 'FACE')
attr.data.foreach_set('value', [30] * len(sm.polygons))
g = sk.vertex_groups.new(name='Bip01 Head')
g.add(list(range(len(sm.vertices))), 1.0, 'REPLACE')
for o in bpy.data.objects:
    o.select_set(o in (body, sk))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
me = body.data

# ---- caps and hems
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lay = bm.faces.layers.int['part']
wl = bm.verts.layers.deform.verify()
# thumbs: Meshy's hoop is a third longer than the fingers; cut the last segment and close it on a blunt bone tip
for S in 'LR':
    gi = body.vertex_groups.get(f'Bip01 {S} Tip0').index
    tip = [v for v in bm.verts if v[wl].get(gi, 0) > 0.5]
    rim_v = {y for v in tip for e in v.link_edges for y in [e.other_vert(v)] if y not in tip}
    bmesh.ops.delete(bm, geom=tip, context='VERTS')
    es = [e for v in rim_v for e in v.link_edges if e.is_boundary]
    c = sum((v.co for v in rim_v), Vector()) / len(rim_v)
    for v in rim_v:
        v.co = c + (v.co - c) * 0.55
    fs = bmesh.ops.holes_fill(bm, edges=list(set(es)), sides=0)['faces']
    bmesh.ops.triangulate(bm, faces=fs)
    rep['thumb_cut_' + S] = len(tip)
bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()


def boundary_loops():
    seen, loops = set(), []
    for e in bm.edges:
        if e.is_boundary and e.index not in seen:
            lp, st = [], [e]
            while st:
                x = st.pop()
                if x.index in seen:
                    continue
                seen.add(x.index); lp.append(x)
                for v in x.verts:
                    st += [y for y in v.link_edges if y.is_boundary and y.index not in seen]
            loops.append(lp)
    return loops


bm.edges.index_update()
caps = 0
for lp in boundary_loops():
    p = lp[0].link_faces[0][lay]
    if p != 2:
        continue
    c = np.mean([tuple(v.co) for e in lp for v in e.verts], 0)
    if abs(c[0]) > 0.15 and c[2] < 1.35 and 20 < len(lp) < 45:
        fs = bmesh.ops.holes_fill(bm, edges=lp, sides=0)['faces']
        fs = bmesh.ops.triangulate(bm, faces=fs)['faces']
        for f in fs:
            f[lay] = 2
        caps += 1
rep['sleeve_caps'] = caps
bm.faces.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.verts.ensure_lookup_table()
bm.edges.index_update(); bm.verts.index_update()


def hem_frame(name):
    """(axis, origin, verts) of a hem: sleeves about the arm from the hem up, the robe about the vertical body axis."""
    if name == 'robe':
        vs = [v for v in bm.verts if v.link_faces and v.link_faces[0][lay] == 8]
        return np.array([0, 0, 1.0]), np.array([0.0, 0.03, 0]), vs
    S = name[-1]; sx = -1 if S == 'L' else 1
    vs = [v for v in bm.verts if v.link_faces and v.link_faces[0][lay] == 2 and v.co.x * sx > 0.12 and v.co.z < 1.32]
    low = np.array([tuple(v.co) for v in vs if v.co.z < 1.05])
    axis = J[f'Bip01 {S} Forearm'] - low.mean(0); axis /= np.linalg.norm(axis)
    return axis, low.mean(0), vs


def rim_of(name, nbins):
    axis, o, vs = hem_frame(name)
    u = np.cross(axis, [0, 1.0, 0]); u /= np.linalg.norm(u); w = np.cross(axis, u)
    P_ = np.array([tuple(v.co) for v in vs]) - o
    h = P_ @ axis; th = np.arctan2(P_ @ w, P_ @ u)
    k = ((th + np.pi) / (2 * np.pi) * nbins).astype(int) % nbins
    rim = np.full(nbins, np.nan)
    for i in range(nbins):
        if (k == i).any():
            rim[i] = h[k == i].min()
    return axis, vs, h, th, k, rim


for name in ('sleeveL', 'sleeveR', 'robe'):
    for radius, cuts in cfg['subdiv']:
        axis, vs, h, th, k, rim = rim_of(name, 64)
        r = h - np.nan_to_num(rim[k], nan=9)
        near = {v for v, x, z in zip(vs, r, [v.co.z for v in vs]) if x < radius and (name != 'robe' or z < cfg['robe_hem_z'] + radius)}
        target = [e for e in bm.edges if e.verts[0] in near and e.verts[1] in near and e.calc_length() > cfg['min_edge']]
        bmesh.ops.subdivide_edges(bm, edges=target, cuts=cuts, use_grid_fill=False)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
        bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
        bm.verts.index_update(); bm.edges.index_update(); bm.faces.index_update()
        bm.normal_update()

protect = set()
for name in ('sleeveL', 'sleeveR', 'robe'):
    h_ = cfg['hem']['robe' if name == 'robe' else 'sleeve']
    nb = 96
    axis, vs, h, th, k, rim = rim_of(name, nb)
    P_ = np.array([tuple(v.co) for v in vs])
    ring_r = h_['arc_radius']
    # teeth over the angle: valleys at random intervals, depth at each valley
    xs = [-np.pi]; ds = [0.0]
    while xs[-1] < np.pi:
        w = rng.uniform(*h_['width']) / ring_r
        xs.append(xs[-1] + w * 0.55); ds.append(rng.uniform(*h_['depth']))
        xs.append(xs[-1] + w * 0.45); ds.append(rng.uniform(0, h_['tip']))
    R = h_['radius']
    rr = np.nan_to_num(rim[k], nan=9)
    # the rim height varies inside a bin: distance above the rim, floored at zero
    r = np.maximum(h - rr, 0)
    dist = np.interp(th, xs, ds)
    if name == 'robe':
        # the bottom hem only: the factor falls off smoothly toward the side slits, by the rim height smoothed round the body
        rb = np.nan_to_num(rim, nan=2.0)
        rb = np.array([np.mean(rb[np.arange(i - 3, i + 4) % nb]) for i in range(nb)])
        z0 = cfg['robe_hem_z']
        fac = np.clip((z0 - rb) / 0.12, 0, 1)
        dist = dist * fac[k]
    a = np.clip(1 - r / R, 0, 1)
    for v, d, aa, rv in zip(vs, dist, a, r):
        if aa > 0:
            v.co += Vector(axis) * float(d * aa)
        if rv < 0.025:
            protect.add(v)
    rep[name] = {'verts': len(vs), 'moved': int((a * dist > 0.002).sum()), 'protected': int((r < 0.025).sum())}
prot_lay = bm.verts.layers.int.new('prot')
for v in bm.verts:
    v[prot_lay] = 1 if v in protect else 0
bm.to_mesh(me); bm.free(); me.update()

# ---- reduction, part by part
def parts():
    a = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', a)
    return a


rep['before'] = {int(k): int(n) for k, n in zip(*np.unique(parts(), return_counts=True))}
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
for pid, target in cfg['tris'].items():
    pid = int(pid)
    a = parts()
    prot = np.zeros(len(me.vertices), np.int32); me.attributes['prot'].data.foreach_get('value', prot)
    cur = (a == pid)
    free = cur & ~np.array([prot[list(p.vertices)].any() for p in me.polygons])
    fixed = int(cur.sum() - free.sum())
    if cur.sum() <= target or free.sum() == 0:
        continue
    for x in list(me.vertices) + list(me.edges):
        x.select = False
    me.polygons.foreach_set('select', free.tolist())
    verts = np.zeros(len(me.vertices), bool)
    verts[np.array([v for p, f in zip(me.polygons, free) if f for v in p.vertices])] = True
    me.vertices.foreach_set('select', verts.tolist())
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.decimate(ratio=max(0.05, (target - fixed) / free.sum()))
    bpy.ops.object.mode_set(mode='OBJECT')
    me = body.data
me.attributes.remove(me.attributes['prot'])
# ---- linings: inner copies (same weights, 4 mm in, flipped), on their own chart space; composed darker. Back faces are
# culled in game, so without them the hood's far side, the robe behind the legs and the boot flares show the background.
bm = bmesh.new(); bm.from_mesh(me)
lay = bm.faces.layers.int['part']
fid = bm.faces.layers.int.new('fid')
bm.faces.ensure_lookup_table()
for i, f in enumerate(bm.faces):
    f[fid] = i
bm.normal_update()
groups = {40: [f for f in bm.faces if f[lay] == 2 and min(v.co.z for v in f.verts) > cfg['hood_z']],
          41: [f for f in bm.faces if f[lay] == 8],
          42: [f for f in bm.faces if f[lay] in (4, 7) and min(v.co.z for v in f.verts) > cfg['boot_flare_z']]}
for pid, fs in groups.items():
    vn = {}
    for f in fs:
        for v in f.verts:
            vn[v] = vn.get(v, Vector()) + f.normal * f.calc_area()
    dup = bmesh.ops.duplicate(bm, geom=fs)
    new_f = [g for g in dup['geom'] if isinstance(g, bmesh.types.BMFace)]
    for old, nv in dup['vert_map'].items():
        if isinstance(old, bmesh.types.BMVert) and old in vn:
            nv.co = old.co - vn[old].normalized() * cfg['lining_offset']
    for f in new_f:
        f[lay] = pid
    bmesh.ops.reverse_faces(bm, faces=new_f)
    rep[f'lining_{pid}'] = len(new_f)
bm.to_mesh(me); bm.free(); me.update()
rep['after'] = {int(k): int(n) for k, n in zip(*np.unique(parts(), return_counts=True))}
rep['tris'] = len(me.polygons)
# zero-weight vertices (subdivision keeps weights; check)
bad = [v.index for v in me.vertices if not v.groups]
rep['unweighted'] = len(bad)
bpy.ops.object.shade_smooth()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('PREP', json.dumps(rep))
