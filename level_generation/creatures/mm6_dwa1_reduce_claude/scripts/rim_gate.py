"""Elbow-skin rim gate: the separate elbow skin piece of each arm (z 0.67-0.90 m) must stay tucked under the pieces
that cover its rims at rest (top rim: the shirt sleeve and its studs; bottom rim: the forearm/bracer piece).
Every 2nd frame of every clip, each rim vertex covered at rest (inside its cover, within 20 mm) is tested against the
evaluated cover surface; exposed = more than 1 mm outside it. Usage: blender -b -P rim_gate.py -- <file.blend|.glb> <label>
(.glb: LOD0 body node 'Dwarf'). Prints GATE lines and writes work/rim_gate_<label>.json."""
import bpy, bmesh, sys, os, json, numpy as np
from mathutils.bvhtree import BVHTree
path, label = sys.argv[sys.argv.index('--') + 1:][:2]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(path)); body = bpy.data.objects['Body']
else:
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.abspath(path))
    body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Dwarf') and 'LOD' not in o.name and 'Shadow' not in o.name)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); sc = bpy.context.scene
me = body.data
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)  # glTF splits seams
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
# map welded verts back to mesh vertex indices by position
co0 = np.array([v.co[:] for v in me.vertices]); wco = np.array([v.co[:] for v in bm.verts])
from mathutils import kdtree
kt = kdtree.KDTree(len(co0))
for i, c in enumerate(co0): kt.insert(c, i)
kt.balance()
rep = np.array([kt.find(c)[1] for c in wco])          # one mesh vertex per welded vertex
p = list(range(len(bm.verts)))
def f(i):
    while p[i] != i: p[i] = p[p[i]]; i = p[i]
    return i
for e in bm.edges:
    a, b = f(e.verts[0].index), f(e.verts[1].index)
    if a != b: p[a] = b
pc = np.array([f(i) for i in range(len(bm.verts))]); size = np.bincount(pc, minlength=len(pc))
fpc = np.array([pc[fc.verts[0].index] for fc in bm.faces]); ftri = [[v.index for v in fc.verts] for fc in bm.faces]
cent = np.array([np.mean([wco[i] for i in t], 0) for t in ftri])
def piece_near(x, z, lo, hi):
    ks = [k for k in np.unique(pc) if lo < size[k] < hi and abs(wco[pc == k].mean(0)[0] - x) < .04 and abs(wco[pc == k].mean(0)[2] - z) < .04]
    assert len(ks) == 1, ks
    return ks[0]
setups = []
for side, sx in (('R', -1), ('L', 1)):
    elbow = piece_near(.285 * sx, .796, 60, 200)
    ids = np.flatnonzero(pc == elbow); rim = [i for i in ids if bm.verts[i].is_boundary]
    top = [i for i in rim if wco[i, 2] > .77]; bot = [i for i in rim if wco[i, 2] <= .77]
    # covers: faces of other pieces within 4 cm of the rim (sleeve shell + studs above, forearm piece below)
    def cover(rv):
        c = np.mean(wco[rv], 0); r = np.max(np.linalg.norm(wco[rv] - c, axis=1)) + .04
        return [k for k in range(len(ftri)) if fpc[k] != elbow and np.linalg.norm(cent[k] - c) < r and size[fpc[k]] > 1]
    for zone, rv in (('top', top), ('bottom', bot)):
        setups.append((side, zone, rv, cover(rv)))
def evaluated():
    dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); m = ev.to_mesh()
    P = np.array([v.co[:] for v in m.vertices]); ev.to_mesh_clear(); return P[rep]
def frame(P, k):
    a, b, c = (P[ftri[k][j]] for j in range(3)); n = np.cross(b - a, c - a); n /= np.linalg.norm(n) + 1e-12
    t = (b - a) / (np.linalg.norm(b - a) + 1e-12); return a, b, c, np.array([t, np.cross(n, t), n])
def bary(p, a, b, c):
    v0, v1, v2 = b - a, c - a, p - a; d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
    den = d00 * d11 - d01 * d01; v = (d11 * d20 - d01 * d21) / den; w = (d00 * d21 - d01 * d20) / den
    return np.array([1 - v - w, v, w])
rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update(); P0 = evaluated()
active = []
for side, zone, rv, cv in setups:
    t = BVHTree.FromPolygons([tuple(x) for x in P0], [ftri[k] for k in cv]); pins = []
    for i in rv:
        loc, nrm, idx, d = t.find_nearest(P0[i])
        if d > .015: continue   # not covered: only pin rim vertices that lie under a cover within 15 mm
        k = cv[idx]
        a, b, c, R = frame(P0, k); bc = bary(np.array(loc), a, b, c)
        pins.append((i, k, bc, R @ (P0[i] - np.array(loc))))
    active.append((side, zone, pins)); print('SETUP', side, zone, 'rim', len(rv), 'pinned', len(pins), 'cover faces', len(cv))
if os.environ.get('RIM_DEBUG'):
    act = bpy.data.actions['Attack']; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    sc.frame_set(14); P = evaluated()
    for side, zone, pins in active[:1]:
        for i, k, bc, off in pins:
            a, b, c, R = frame(P, k); e = bc[0] * a + bc[1] * b + bc[2] * c + R.T @ off
            print('DBG', i, 'piece', fpc[k], 'size', size[fpc[k]], 'bc', np.round(bc, 2), 'off mm', np.round(off * 1000, 1), 'drift mm', round(float(np.linalg.norm(P[i] - e) * 1000), 1), 'vert moved', round(float(np.linalg.norm(P[i] - P0[i]) * 1000), 1))
    sys.exit(0)
res = {}
for act in bpy.data.actions:
    rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    for fr in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 2):
        sc.frame_set(fr); P = evaluated()
        for side, zone, pins in active:
            d = []
            for i, k, bc, off in pins:
                a, b, c, R = frame(P, k); d.append(np.linalg.norm(P[i] - (bc[0] * a + bc[1] * b + bc[2] * c + R.T @ off)) * 1000)
            d = np.array(d); r = res.setdefault(f'{side}_{zone}', {'drift_gt5mm_vertex_frames': 0, 'max_mm': 0.0, 'at': '', 'all': []})
            r['drift_gt5mm_vertex_frames'] += int((d > 5).sum()); r['all'] += d.tolist()
            if d.max() > r['max_mm']: r['max_mm'] = round(float(d.max()), 1); r['at'] = f'{act.name}:{fr}'
for k, r in res.items():
    a = r.pop('all'); r['p95_mm'] = round(float(np.percentile(a, 95)), 1); print('GATE', label, k, r)
json.dump(res, open(os.path.join(HERE, f'work/rim_gate_{label}.json'), 'w'), indent=1)
