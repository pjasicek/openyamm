"""m504 crumbling death (native m198da..dd, corpse m198xa: the body breaks into its limbs, torso and head, which fall
apart and lie scattered). Works on the textured master: -- <in blend (rig_v6)> <out blend (rig_v7)>.

- Rubble mesh: a copy of 'Body' cut into 14 rigid pieces by each vertex's dominant bone (head+neck, chest, belly,
  pelvis, per side upper arm, forearm, fist, thigh, shin+foot); each cut opening is closed by a cap (stone texture: a
  planar projection into a square of the body atlas well inside one island). Each piece is 100 % on its own root-level
  bone 'Rubble_<piece>' (rest at the piece centroid); the face attribute 'head' and both UV layers carry over, so the
  export assigns the same two materials.
- Sockets: 'Socket_FistL' / 'Socket_FistR' (non-deforming, at the fist centres on the hand bones) for the casts.
- Clips: every clip keys the rubble bones at scale 1e-4 (collapsed: tools/model_hide_collapsed_meshes.py then hides
  the Rubble mesh node there). Death = the gated stagger (the retargeted backward react) until BREAK_S, then the body
  collapses (B_Pelvis scale 1e-4) and the pieces take over at the body's pose: each starts from its bone's motion
  plus an outward/backward burst and a spin, falls under gravity, bounces once softly on the floor with friction and
  turns onto its long side; 1.2 s after the break all pieces rest. Dead = the last frame (export_runtime.py).
Prints the piece list and the rest/floor report per piece."""
import bpy, bmesh, sys, os, math, json
import numpy as np
from mathutils import Matrix, Vector, Quaternion
src, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
BREAK_S = float(os.environ.get('BREAK_S', '0.4'))
SETTLE_S = 1.2
COLLAPSE = 1e-4
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
sc = bpy.context.scene; sc.render.fps = FPS; sc.render.fps_base = 1
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()

# ---------------------------------------------------------------- pieces by dominant bone
def seg_of(bone):
    if bone in ('B_Head', 'B_Neck'): return 'Head'
    if bone in ('B_Spine2',) or 'Clavicle' in bone: return 'Chest'
    if bone in ('B_Spine', 'B_Spine1'): return 'Belly'
    if bone == 'B_Pelvis': return 'Pelvis'
    for s in 'LR':
        if bone.startswith(f'B_{s}_'):
            if 'UpperArm' in bone: return f'UpperArm{s}'
            if 'Forearm' in bone: return f'Forearm{s}'
            if 'Hand' in bone or 'Finger' in bone: return f'Fist{s}'
            if 'Thigh' in bone: return f'Thigh{s}'
            if any(k in bone for k in ('Calf', 'Foot', 'Toe')): return f'Shin{s}'
    return 'Belly'
REP = {'Head': 'B_Head', 'Chest': 'B_Spine2', 'Belly': 'B_Spine1', 'Pelvis': 'B_Pelvis'}
for s in 'LR':
    REP.update({f'UpperArm{s}': f'B_{s}_UpperArm', f'Forearm{s}': f'B_{s}_Forearm', f'Fist{s}': f'B_{s}_Hand',
                f'Thigh{s}': f'B_{s}_Thigh', f'Shin{s}': f'B_{s}_Calf'})
SEGS = list(REP)
vg = [g.name for g in body.vertex_groups]
vseg = np.array([SEGS.index(seg_of(vg[max(v.groups, key=lambda e: e.weight).group])) for v in body.data.vertices])

rub = body.copy(); rub.data = body.data.copy(); rub.name = rub.data.name = 'Rubble'
sc.collection.objects.link(rub)
for m in list(rub.modifiers):
    rub.modifiers.remove(m)
rub.vertex_groups.clear()
bm = bmesh.new(); bm.from_mesh(rub.data); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
fseg = bm.faces.layers.int.new('seg')
for f in bm.faces:
    s = np.bincount([vseg[v.index] for v in f.verts], minlength=len(SEGS))
    f[fseg] = int(np.argmax(s))
cut = [e for e in bm.edges if len({f[fseg] for f in e.link_faces}) > 1]
bmesh.ops.split_edges(bm, edges=cut)
# cap square: the deepest texel of the body atlas coverage (UVMap), half-size 70 % of its distance to the island edge
CS = json.load(open(os.path.join(HERE, 'work', 'cap_square.json')))       # compose_m504.py (Blender has no scipy)
cu, cv, half = CS['u'], CS['v'], CS['half']
print('RUBBLE cap square uv centre', round(cu, 3), round(cv, 3), 'half', round(half, 4))
uvl = bm.loops.layers.uv['UVMap']; huvl = bm.loops.layers.uv.get('HeadUV')
headl = bm.faces.layers.int.get('head')
caps = 0


def loops_of(edges):
    """Boundary edges -> closed vertex loops (walk; at a junction take any unused edge)."""
    left = set(edges); out = []
    adj = {}
    for e in edges:
        for v in e.verts:
            adj.setdefault(v, []).append(e)
    while left:
        e0 = left.pop(); a, b = e0.verts; loop = [a, b]; cur = b
        while True:
            nxt = next((e for e in adj[cur] if e in left), None)
            if nxt is None:
                break
            left.discard(nxt); cur = nxt.other_vert(cur)
            if cur == loop[0]:
                break
            loop.append(cur)
        if len(loop) >= 3:
            out.append(loop)
    return out


for si in range(len(SEGS)):
    bnd = [e for e in bm.edges if e.is_boundary and e.link_faces[0][fseg] == si]
    for loop in loops_of(bnd):
        # orientation: the cap must face away from the piece; the boundary loop runs opposite to the adjacent face's
        e = bm.edges.get((loop[0], loop[1])); f_adj = e.link_faces[0]
        lv = [l.vert for l in f_adj.loops]; i = lv.index(loop[0])
        if lv[(i + 1) % len(lv)] == loop[1]:
            loop = loop[::-1]
        c = sum((v.co for v in loop), Vector()) / len(loop)
        cv_ = bm.verts.new(c)
        tri = []
        for k in range(len(loop)):
            try:
                f = bm.faces.new((loop[k], loop[(k + 1) % len(loop)], cv_))
            except ValueError:
                continue
            f[fseg] = si
            if headl is not None:
                f[headl] = 0
            f.material_index = 0
            tri.append(f)
        if not tri:
            continue
        P = np.array([tuple(v.co) for v in loop]); cc = P.mean(0)
        n = Vector((0, 0, 0))
        for k in range(len(loop)):
            p0, p1 = loop[k].co - c, loop[(k + 1) % len(loop)].co - c; n += p0.cross(p1)
        n = n.normalized() if n.length > 1e-9 else Vector((0, 0, 1))
        ax = n.orthogonal().normalized(); bx = n.cross(ax)
        ext = max(1e-4, float(np.abs(np.c_[(P - cc) @ np.array(ax), (P - cc) @ np.array(bx)]).max()))
        for f in tri:
            for l in f.loops:
                d = l.vert.co - c
                l[uvl].uv = (cu + half * d.dot(ax) / ext, cv + half * d.dot(bx) / ext)
                if huvl is not None:
                    l[huvl].uv = (0.0, 0.0)
        caps += 1
bm.normal_update()
bm.to_mesh(rub.data); fs = np.zeros(len(rub.data.polygons), np.int32)
rub.data.attributes['seg'].data.foreach_get('value', fs)
bm.free()
print('RUBBLE pieces', len(SEGS), 'caps', caps, 'faces', len(rub.data.polygons), 'tris', sum(len(p.vertices) - 2 for p in rub.data.polygons))
# vertex piece = its faces' piece (split edges: no vertex is shared by two pieces)
vs = np.zeros(len(rub.data.vertices), np.int32)
for p in rub.data.polygons:
    for v in p.vertices:
        vs[v] = fs[p.index]
co = np.array([tuple(v.co) for v in rub.data.vertices])
cent = {s: co[vs == i].mean(0) for i, s in enumerate(SEGS)}

# ---------------------------------------------------------------- bones: rubble pieces and fist sockets
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
for s in SEGS:
    b = eb.new('Rubble_' + s); b.head = Vector(cent[s]); b.tail = b.head + Vector((0, 0, 0.1)); b.use_deform = True
bco = np.array([tuple(v.co) for v in body.data.vertices])
for s in 'LR':
    c = bco[vseg == SEGS.index(f'Fist{s}')].mean(0)
    b = eb.new(f'Socket_Fist{s}'); b.head = Vector(c); b.tail = b.head + Vector((0, 0, 0.06)); b.use_deform = False
    b.parent = eb[f'B_{s}_Hand']
bpy.ops.object.mode_set(mode='OBJECT')
for i, s in enumerate(SEGS):
    g = rub.vertex_groups.new(name='Rubble_' + s); g.add(np.where(vs == i)[0].tolist(), 1.0, 'REPLACE')
rub.parent = rig; rub.matrix_parent_inverse.identity()
m = rub.modifiers.new('Armature', 'ARMATURE'); m.object = rig
RB = ['Rubble_' + s for s in SEGS]
SOCK = ['Socket_FistL', 'Socket_FistR']


def set_act(a):
    rig.animation_data.action = a
    if a is not None and getattr(a, 'slots', None) is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def key_collapsed(act, frames):
    set_act(act)
    for f in frames:
        for n in RB:
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
            pb.location = (0, 0, 0); pb.rotation_quaternion = Quaternion(); pb.scale = (COLLAPSE,) * 3
            for p in ('location', 'rotation_quaternion', 'scale'):
                pb.keyframe_insert(p, frame=f)
        for n in SOCK:
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.matrix_basis.identity()
            pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)


acts = [a for a in bpy.data.actions if a.use_fake_user or a.users]
for a in list(bpy.data.actions):
    if a.name == 'Death':
        continue
    f0, f1 = (int(x) for x in a.frame_range)
    key_collapsed(a, (f0, f1))

# ---------------------------------------------------------------- Death: stagger, break, fall
death = bpy.data.actions['Death']
kb = int(round(BREAK_S * FPS)); n_settle = int(round(SETTLE_S * FPS))
set_act(death)
REST = {s: rig.data.bones[REP[s]].matrix_local.copy() for s in SEGS}


def piece_T(s):
    """Armature-space transform carrying the piece's rest vertices with its representative bone."""
    return rig.pose.bones[REP[s]].matrix @ REST[s].inverted()


sc.frame_set(kb - 1); T_prev = {s: piece_T(s).copy() for s in SEGS}
sc.frame_set(kb); T_brk = {s: piece_T(s).copy() for s in SEGS}
body_pose = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in rig.pose.bones if pb.name.startswith('B_')}
pel = np.array(rig.pose.bones['B_Pelvis'].head)
# trim the source death to the break and rebuild it
src_frames = []
for f in range(kb + 1):
    sc.frame_set(f)
    src_frames.append({pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in rig.pose.bones if pb.name.startswith('B_')})
new = bpy.data.actions.new('DeathNew'); new.use_fake_user = True
set_act(new)
for f, pose in enumerate(src_frames):
    for n, (q, l) in pose.items():
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.location = l; pb.scale = (1, 1, 1)
        pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f); pb.keyframe_insert('scale', frame=f)
key_collapsed(new, range(0, kb))
# simulation
rng = np.random.default_rng(504)
state = {}
vloc = {s: co[vs == i] - cent[s] for i, s in enumerate(SEGS)}
for s in SEGS:
    T0, T1 = T_prev[s], T_brk[s]
    p = np.array(T1 @ Vector(cent[s])); p_prev = np.array(T0 @ Vector(cent[s]))
    R = np.array(T1.to_3x3())
    out_dir = p[:2] - pel[:2]; out_dir = out_dir / max(np.linalg.norm(out_dir), 1e-3)
    h = max(p[2], 0.0)
    v = (p - p_prev) * FPS * 0.6
    v[:2] += out_dir * (0.5 + 0.4 * rng.random()) + np.array([0.0, 0.35 * h])          # outward and backward (+Y)
    v[2] += 0.6 + 0.4 * rng.random() if h > 0.9 else 0.2
    w = rng.normal(size=3); w = w / np.linalg.norm(w) * (1.5 + 2.0 * rng.random())
    w[0] += 1.2 * h                                                                     # topple backward
    L = vloc[s] @ R.T; ax = np.linalg.svd(L - L.mean(0))[2][0]
    state[s] = {'p': p, 'v': v, 'R': R, 'w': w, 'axis_local': ax @ R, 'ground': False}
dt = 1 / (FPS * 4)
frames = {s: [] for s in SEGS}
for k in range(1, n_settle + 1):
    for _ in range(4):
        for s, st in state.items():
            st['v'][2] -= 9.81 * dt
            st['p'] = st['p'] + st['v'] * dt
            ang = np.linalg.norm(st['w']) * dt
            if ang > 1e-9:
                st['R'] = np.array(Matrix.Rotation(ang, 3, Vector(st['w'] / np.linalg.norm(st['w'])))) @ st['R']
            if st['ground']:
                # turn onto the long side: the piece's long axis toward horizontal (minimal rotation), pivoting low
                a = st['R'] @ st['axis_local']; tgt = np.array([a[0], a[1], 0.0])
                if np.linalg.norm(tgt) > 1e-3 and abs(a[2]) > 0.02:
                    q = Vector(a).rotation_difference(Vector(tgt / np.linalg.norm(tgt)))
                    st['R'] = np.array(Quaternion(q.axis, q.angle * min(1.0, 6 * dt)).to_matrix()) @ st['R']
            low = (vloc[s] @ st['R'].T)[:, 2].min() + st['p'][2]
            if low < 0:
                st['p'][2] -= low
                if st['v'][2] < 0:
                    st['v'][2] *= -0.18
                st['v'][:2] *= 0.55; st['w'] *= 0.5; st['ground'] = True
            if st['ground']:
                st['v'][:2] *= (1 - 3 * dt); st['w'] *= (1 - 6 * dt)
    for s, st in state.items():
        frames[s].append((st['p'].copy(), st['R'].copy()))
# keys: body collapsed after the break, rubble pieces from the simulation
for k in range(n_settle + 1):
    f = kb + k
    for n, (q, l) in body_pose.items():
        pb = rig.pose.bones[n]; pb.rotation_quaternion = q; pb.location = l
        pb.scale = (1, 1, 1) if (k == 0 or n != 'B_Pelvis') else (COLLAPSE,) * 3
        pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f); pb.keyframe_insert('scale', frame=f)
    for s in SEGS:
        if k == 0:
            T = T_brk[s]
        else:
            p, R = frames[s][k - 1]
            T = Matrix.Translation(Vector(p)) @ Matrix(R.tolist()).to_4x4() @ Matrix.Translation(-Vector(cent[s]))
        pb = rig.pose.bones['Rubble_' + s]; pb.rotation_mode = 'QUATERNION'
        pb.matrix = T @ rig.data.bones['Rubble_' + s].matrix_local
        pb.scale = (1, 1, 1)
        for p_ in ('location', 'rotation_quaternion', 'scale'):
            pb.keyframe_insert(p_, frame=f)
    for n in SOCK:
        pb = rig.pose.bones[n]; pb.matrix_basis.identity()
        pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)
new.use_frame_range = True; new.frame_start, new.frame_end = 0, kb + n_settle
bpy.data.actions.remove(death); new.name = 'Death'
set_act(None)
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
rep = {s: {'rest_low_cm': round(100 * float((vloc[s] @ frames[s][-1][1].T)[:, 2].min() + frames[s][-1][0][2]), 2),
           'from_origin_m': round(float(np.linalg.norm(frames[s][-1][0][:2])), 2)} for s in SEGS}
print('RUBBLE death', round((kb + n_settle) / FPS, 3), 's, break at', BREAK_S, 's; pieces at rest', json.dumps(rep))
json.dump({'break_s': BREAK_S, 'death_s': (kb + n_settle) / FPS, 'pieces': rep}, open(os.path.join(HERE, 'work', 'rubble.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
