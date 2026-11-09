"""All-metal robot v2 rig, built directly from the Smart Topology return (249 pieces). Forward -Y, up +Z, character
left +X. Rigid hard-surface route (one bone per rigid part), with three model edits before UVs:
- each leg piece is the sleeve, its arm plate and the spike rod in one connected surface: the rod faces are split off
  (edges cut at the rod/sleeve seam) and the rod's open top is extruded 10 cm up its axis inside the sleeve, so the
  spike can slide out of the sleeve (native walk) without stretching or showing its end;
- weights: spikes, caps (rod tops above the rings) -> Spike_XX; sleeve, rings and arm plate -> Leg_XX, blending to
  Body 8-13 cm from the sleeve centre; cables near a sleeve blend Body -> Leg over 5-10 cm; the tail (one piece) and
  the neck by arc position along their centerlines (linear blends between neighbouring bones); fins copy the nearest
  tail vertex; head pieces -> Head, lower jaw and its teeth -> Jaw; the gun (ball, barrel, rear housing) -> Gun,
  hinged at its rear bracket; everything else -> Body.
Writes work/rig_v1.blend, work/raw_rig.npz (grounded rest co, tri, piece per vertex after the edits) and
work/rig_plan.json."""
import bpy, bmesh, os, json
import numpy as np
from mathutils import Vector
from collections import deque
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(P, 'meshy/smart_topology_v1/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh: bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
mesh.name = mesh.data.name = 'Robot'; mesh.data.materials.clear()
me = mesh.data


def pieces(bm):
    bm.verts.ensure_lookup_table()
    part = -np.ones(len(bm.verts), int); sizes = []
    for v in bm.verts:
        if part[v.index] >= 0: continue
        k = len(sizes); part[v.index] = k; st = [v]; n = 0
        while st:
            a = st.pop(); n += 1
            for e in a.link_edges:
                b = e.other_vert(a)
                if part[b.index] < 0: part[b.index] = k; st.append(b)
        sizes.append(n)
    order = np.argsort(sizes, kind='stable')[::-1]; remap = np.empty(len(sizes), int); remap[order] = np.arange(len(sizes))
    return remap[part]


bm = bmesh.new(); bm.from_mesh(me)
raw = np.load(os.path.join(P, 'work/raw_st1.npz'))
co = np.array([tuple(v.co) for v in bm.verts]); assert np.abs(co - raw['co']).max() < 1e-5
part = raw['part']
LEGS = {'FR': (1, 62, 16), 'FL': (3, 61, 17), 'RR': (7, 58, 14), 'RL': (5, 60, 12)}   # leg piece, cap, ring
legs = {}
rod_verts = {}
for nm, (lp, cap, ring) in LEGS.items():
    p = np.nonzero(part == lp)[0]; tip = co[p[np.argmin(co[p, 2])]]
    top = co[part == cap].mean(0); ax = (top - tip) / np.linalg.norm(top - tip)
    t = (co[p] - tip) @ ax; r = np.linalg.norm((co[p] - tip) - np.outer(t, ax), axis=1)
    rod = p[(t < 0.273) & (r < 0.031)]
    hip = tip + ax * 0.31                        # sleeve centre on the spike axis
    legs[nm] = dict(tip=tip, top=top, ax=ax, hip=hip, piece=lp, cap=cap, ring=ring)
    rod_verts[nm] = set(int(i) for i in rod)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
for nm, rv in rod_verts.items():
    rod_faces = [f for f in bm.faces if all(v.index in rv for v in f.verts)]
    rf = set(rod_faces)
    seam = [e for e in bm.edges if len(e.link_faces) == 2 and (e.link_faces[0] in rf) != (e.link_faces[1] in rf)]
    bmesh.ops.split_edges(bm, edges=seam)
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    rod_vs = {v for f in rod_faces for v in f.verts}
    bound = [e for e in bm.edges if e.is_boundary and all(v in rod_vs for v in e.verts)]
    ax = Vector(legs[nm]['ax'].tolist())
    ret = bmesh.ops.extrude_edge_only(bm, edges=bound)
    new_v = [g for g in ret['geom'] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=ax * 0.10, verts=new_v)
    legs[nm]['seam_edges'] = len(seam); legs[nm]['rod_boundary'] = len(bound); legs[nm]['rod_faces'] = len(rod_faces)
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    rod_verts[nm] = {v.index for v in rod_vs} | {v.index for v in new_v}
bm.to_mesh(me); bm.free()
me.update()
co = np.array([tuple(v.co) for v in me.vertices]); n0 = len(raw['co'])
# piece id per vertex: original vertices keep their raw piece, split copies / extrusions take their source piece
bm = bmesh.new(); bm.from_mesh(me); newpart = pieces(bm); bm.free()
part_v = np.empty(len(co), int); part_v[:n0] = part
for i in range(n0, len(co)):
    same = np.nonzero(newpart[:n0] == newpart[i])[0]
    part_v[i] = part[same[0]] if len(same) else -1
# ---- skeleton (raw frame; grounded at the end) ----
Z0 = co[:, 2].min()
NECK = [(0.0, -0.125, 0.022), (0.0, -0.205, 0.052), (0.0, -0.288, 0.085)]
HEAD_END = (0.0, -0.47, 0.065)
JAW = ((0.0, -0.312, 0.078), (0.0, -0.43, 0.03))
GUN = ((0.0, 0.02, -0.145), (0.0, -0.258, -0.148))


def tail_centerline():
    """Surface shortest path over the tail piece from its chassis end to its tip, refined to slab centroids."""
    idx = np.nonzero(part_v == 0)[0]; S = set(idx.tolist())
    adj = {i: [] for i in idx}
    for e in me.edges:
        a, b = e.vertices
        if a in S and b in S:
            w = float(np.linalg.norm(co[a] - co[b])); adj[a].append((b, w)); adj[b].append((a, w))
    import heapq
    def dijk(s):
        dist = {s: 0.0}; prev = {}; h = [(0.0, s)]
        while h:
            dd, u = heapq.heappop(h)
            if dd > dist[u]: continue
            for v, w in adj[u]:
                if dd + w < dist.get(v, 1e9): dist[v] = dd + w; prev[v] = u; heapq.heappush(h, (dd + w, v))
        return dist, prev
    base = idx[np.argmin(co[idx, 1])]
    dist, prev = dijk(base); tipv = max(dist, key=dist.get)
    path = [tipv]
    while path[-1] != base: path.append(prev[path[-1]])
    path = co[path[::-1]]
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1); s = np.r_[0, np.cumsum(seg)]
    J = []
    for k in range(9):
        q = path[np.searchsorted(s, s[-1] * k / 8, side='left').clip(0, len(path) - 1)]
        if k in (0, 8): J.append(q); continue
        near = co[idx][np.linalg.norm(co[idx] - q, axis=1) < 0.04]
        J.append(near.mean(0) if len(near) else q)
    J = np.array(J)
    J[1:-1] = (J[:-2] + 2 * J[1:-1] + J[2:]) / 4
    J[0] = co[idx][np.linalg.norm(co[idx] - J[0], axis=1) < 0.04].mean(0)
    return J


TAIL = tail_centerline()
bones = [('Body', None, (0.0, 0.02, -0.02), (0.0, -0.10, -0.02)), ('Gun', 'Body', GUN[0], GUN[1]),
         ('Neck1', 'Body', NECK[0], NECK[1]), ('Neck2', 'Neck1', NECK[1], NECK[2]), ('Head', 'Neck2', NECK[2], HEAD_END),
         ('Jaw', 'Head', JAW[0], JAW[1])]
for k in range(len(TAIL) - 1):
    bones.append((f'Tail{k + 1}', 'Body' if k == 0 else f'Tail{k}', tuple(TAIL[k]), tuple(TAIL[k + 1])))
for nm, L in legs.items():
    bones.append((f'Leg_{nm}', 'Body', tuple(L['hip']), tuple(L['tip'])))
    bones.append((f'Spike_{nm}', f'Leg_{nm}', tuple(L['top']), tuple(L['tip'])))
names = [b[0] for b in bones]; ix = {n: i for i, n in enumerate(names)}
W = np.zeros((len(co), len(names)), np.float32)


def chain_weights(vs, joints, bnames, before='Body'):
    """Linear blends by arc position along the joint polyline: full weight in each bone's middle, crossfade over
    +-30 % of the shorter neighbour around each joint; vertices before the first joint blend from `before`."""
    J = np.asarray(joints, float); L = np.linalg.norm(np.diff(J, axis=0), axis=1); S = np.r_[0, np.cumsum(L)]
    p = co[vs]; best = np.full(len(p), 1e9); sv = np.zeros(len(p))
    for i in range(len(L)):
        a = J[i]; d = J[i + 1] - a; t = np.clip(((p - a) @ d) / (d @ d), 0, 1)
        dist = np.linalg.norm(p - (a + np.outer(t, d)), axis=1)
        if i == 0:
            t0 = ((p - a) @ d) / (d @ d); t = np.where(t0 < 0, t0, t)
        m = dist < best; best[m] = dist[m]; sv[m] = S[i] + t[m] * L[i]
    for j, v in enumerate(vs):
        s = sv[j]; w = {}
        i = int(np.clip(np.searchsorted(S, s, side='right') - 1, 0, len(L) - 1))
        w[bnames[i]] = 1.0
        if s < 0.0:                             # behind the chain start
            f = float(np.clip(1 + s / 0.02, 0, 1)); w = {bnames[0]: f, before: 1 - f}
        else:
            for jj in (i, i + 1):               # crossfade around joints jj (between bone jj-1 and jj)
                if 1 <= jj < len(L):
                    h = 0.3 * min(L[jj - 1], L[jj]); u = (s - S[jj]) / h
                    if -1 < u < 1:
                        f = (u + 1) / 2; w = {bnames[jj - 1]: 1 - f, bnames[jj]: f}
        for b, x in w.items(): W[v, ix[b]] += x


C = {k: co[part_v == k].mean(0) for k in np.unique(part_v) if k >= 0}
role = {}
leg_pieces = {L['piece']: nm for nm, L in legs.items()}
caps = {L['cap']: nm for nm, L in legs.items()}; rings = {L['ring']: nm for nm, L in legs.items()}
headset = set(); jawset = {11}
jaw_co = co[part_v == 11]; head_co = co[part_v == 2]
for k, c in C.items():
    if k in leg_pieces or k in caps or k in rings or k == 0: continue
    if c[1] < -0.283 and c[2] > -0.01 and abs(c[0]) < 0.07:
        if k == 11: continue
        dj = np.linalg.norm(jaw_co - c, axis=1).min(); dh = np.linalg.norm(head_co - c, axis=1).min()
        (jawset if (dj < dh and k != 2) else headset).add(k)
gunset = set()
for k, c in C.items():
    p = co[part_v == k]
    if k in leg_pieces or k == 65: continue
    if p[:, 2].max() < -0.115 and abs(c[0]) < 0.06 and -0.27 < c[1] < 0.012:
        gunset.add(k)
neckset = set()
for k, c in C.items():
    if k in leg_pieces or k in headset or k in jawset or k in gunset or k in caps or k in rings: continue
    if -0.30 < c[1] < -0.12 and c[2] > -0.03 and abs(c[0]) < 0.07:
        neckset.add(k)
fins = set()
tail_co = co[part_v == 0]
for k, c in C.items():
    if k == 0 or k in leg_pieces or k in caps or k in rings or k in neckset or k in headset or k in gunset: continue
    p = co[part_v == k]
    if c[1] > 0.10 and np.linalg.norm(tail_co[:, None] - p[None], axis=2).min() < 0.03:
        fins.add(k)
# rigid parts
for v in range(len(co)):
    k = part_v[v]
    if k in headset: W[v, ix['Head']] = 1
    elif k in jawset: W[v, ix['Jaw']] = 1
    elif k in gunset: W[v, ix['Gun']] = 1
    elif k in caps: W[v, ix['Spike_' + caps[k]]] = 1
    elif k in rings: W[v, ix['Leg_' + rings[k]]] = 1
for nm, rv in rod_verts.items():
    for v in rv: W[v, ix['Spike_' + nm]] = 1
chain_weights(np.nonzero(part_v == 0)[0], TAIL, [f'Tail{k + 1}' for k in range(len(TAIL) - 1)])
neck_v = np.nonzero(np.isin(part_v, list(neckset)))[0]
chain_weights(neck_v, NECK + [HEAD_END], ['Neck1', 'Neck2', 'Head'])
hips = {nm: L['hip'] for nm, L in legs.items()}
for v in range(len(co)):
    if W[v].sum() > 0: continue
    k = part_v[v]
    if k in leg_pieces:
        nm = leg_pieces[k]; d = np.linalg.norm(co[v] - hips[nm]); f = float(np.clip((0.13 - d) / 0.05, 0, 1))
    else:
        dd = {nm: np.linalg.norm(co[v] - h) for nm, h in hips.items()}; nm = min(dd, key=dd.get)
        f = float(np.clip((0.10 - dd[nm]) / 0.05, 0, 1))
    W[v, ix['Leg_' + nm]] += f; W[v, ix['Body']] += 1 - f
# fins copy the nearest tail vertex
tv = np.nonzero(part_v == 0)[0]
for v in np.nonzero(np.isin(part_v, list(fins)))[0]:
    j = tv[np.argmin(np.linalg.norm(co[tv] - co[v], axis=1))]; W[v] = W[j]
W /= W.sum(1, keepdims=True)
# ---- ground, build rig ----
me.transform(__import__('mathutils').Matrix.Translation((0, 0, -Z0))); me.update()
shift = Vector((0, 0, -Z0))
for p in me.polygons: p.use_smooth = True
arm = bpy.data.armatures.new('Robot_Rig'); rig = bpy.data.objects.new('Robot_Rig', arm)
bpy.context.scene.collection.objects.link(rig); bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
for name, parent, h, t in bones:
    b = arm.edit_bones.new(name); b.head = Vector(h) + shift; b.tail = Vector(t) + shift
    b.align_roll(Vector((0, 0, 1)) if abs((b.tail - b.head).normalized().z) < 0.9 else Vector((0, -1, 0)))
    if parent:
        b.parent = arm.edit_bones[parent]
        b.use_connect = (Vector(arm.edit_bones[parent].tail) - b.head).length < 1e-6
eye = co[part_v == 55].mean(0); bar = co[np.isin(part_v, list(gunset))]
muzzle = bar[bar[:, 1] < bar[:, 1].min() + 0.01].mean(0)
SOCKETS = {'Socket_Eye': ('Head', eye), 'Socket_Muzzle': ('Gun', muzzle + np.array((0, -0.01, 0)))}
for sname, (parent, pos) in SOCKETS.items():
    s = arm.edit_bones.new(sname); s.head = Vector(pos.tolist()) + shift; s.tail = s.head + Vector((0, -0.02, 0))
    s.parent = arm.edit_bones[parent]; s.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
for j, n in enumerate(names):
    g = mesh.vertex_groups.new(name=n)
    for v in np.nonzero(W[:, j] > 1e-5)[0]:
        g.add([int(v)], float(W[v, j]), 'REPLACE')
mod = mesh.modifiers.new('Armature', 'ARMATURE'); mod.object = rig; mesh.parent = rig
me.calc_loop_triangles()
tri = np.array([tuple(t.vertices) for t in me.loop_triangles])
np.savez(os.path.join(P, 'work/raw_rig.npz'), co=co + np.array((0, 0, -Z0)), tri=tri, part=part_v)
from collections import Counter
dom = Counter(names[i] for i in W.argmax(1))
json.dump({'Z0': float(Z0), 'bones': [(nm, p_, list(map(float, h)), list(map(float, t))) for nm, p_, h, t in bones],
           'legs': {nm: {k: (v.tolist() if hasattr(v, 'tolist') else v) for k, v in L.items()} for nm, L in legs.items()},
           'sets': {'head': sorted(map(int, headset)), 'jaw': sorted(map(int, jawset)), 'gun': sorted(map(int, gunset)),
                    'neck': sorted(map(int, neckset)), 'fins': sorted(map(int, fins))},
           'sockets': {k: (v[1] + np.array((0, 0, -Z0))).tolist() for k, v in SOCKETS.items()},
           'dominant': dict(dom)}, open(os.path.join(P, 'work/rig_plan.json'), 'w'), indent=1)
print('LEGS', {nm: (L['rod_faces'], L['seam_edges'], L['rod_boundary']) for nm, L in legs.items()})
print('SETS', len(headset), len(jawset), len(gunset), len(neckset), len(fins), 'verts', len(co), 'tris', len(tri))
print('RIGGED', len(arm.bones), 'Z0', round(Z0, 4), dict(dom))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(P, 'work/rig_v1.blend'))
