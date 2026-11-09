"""Clip authoring on the winged Kreegan rig (imported inside Blender scripts of this project).

The winged rig's B_* bones share the local humanoid set's rest frames (hes_overseer_codex README: source-frame rest
transforms), so a library clip transfers by copying WORLD rotations (the set faces +Y, our rig -Y: TURN). A clip is
authored at 48 Hz over a native base (the Overseer clips carry the flying demon's wings, legs and pelvis): per frame
the base pose is applied, then each layer writes world rotations of its bones, blended toward the base by its weight.
Arms and clavicles are written relative to the chest (`rel`: the source pose re-expressed under the current B_Spine2),
so the flight's body sway carries them and the flying demon's raised clavicles do not throw the arms forward.

Layer: dict(bones=[...], src=<source clip>, t=<function time -> source time>, w=<function time -> 0..1>,
            rel='B_Spine2' for arm and clavicle bones).
"""
import bpy, math
from mathutils import Matrix, Quaternion, Vector

FPS = 48
TURN = Matrix.Rotation(math.pi, 4, 'Z')
TRUNK = ['B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck', 'B_Head']
CLAV = ['B_L_Clavicle', 'B_R_Clavicle']
ARM = {s: [f'B_{s}_UpperArm', f'B_{s}_Forearm', f'B_{s}_Hand'] for s in 'LR'}
LEGS = [f'B_{s}_{b}' for s in 'LR' for b in ('Thigh', 'Calf', 'Foot', 'Toe0')]
SAMPLED = TRUNK + CLAV + ARM['L'] + ARM['R'] + LEGS


def smooth(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def envelope(t0, t1, t2, t3):
    """0 before t0, eased up to 1 at t1, 1 until t2, eased down to 0 at t3"""
    return lambda t: smooth((t - t0) / max(t1 - t0, 1e-6)) * (1 - smooth((t - t2) / max(t3 - t2, 1e-6)))


def set_action(obj, act):
    obj.animation_data_create(); obj.animation_data.action = act
    if getattr(act, 'slots', None) and len(act.slots):
        obj.animation_data.action_slot = act.slots[0]


def frame_at(scene, f):
    scene.frame_set(math.floor(f), subframe=f % 1)


def load_sources(root, wanted, scene):
    """wanted: {glb file (relative to anim_library/humanoid_set): [clip names]} -> {clip: (duration, [ {bone: quat} ] at 48 Hz)}"""
    out = {}
    for fname, names in wanted.items():
        old_o, old_a = set(bpy.data.objects), set(bpy.data.actions)
        bpy.ops.import_scene.gltf(filepath=str(root / 'anim_library' / 'humanoid_set' / fname))
        new_o = set(bpy.data.objects) - old_o; new_a = set(bpy.data.actions) - old_a
        src = next(o for o in new_o if o.type == 'ARMATURE'); src.animation_data_create()
        for tr in src.animation_data.nla_tracks: tr.mute = True
        fps = scene.render.fps / scene.render.fps_base
        for name in names:
            act = next(a for a in new_a if a.name.split('@')[-1].split('|')[-1] == name)
            set_action(src, act)
            s0, s1 = act.frame_range; dur = (s1 - s0) / fps
            samples = []
            for k in range(math.ceil(dur * FPS) + 1):
                t = min(k / FPS, dur); frame_at(scene, s0 + t * fps)
                d = {n: (TURN @ src.matrix_world @ src.pose.bones[n].matrix).to_3x3().normalized().to_quaternion()
                     for n in SAMPLED if n in src.pose.bones}
                d['_pelvis'] = (TURN @ src.matrix_world @ src.pose.bones['B_Pelvis'].head).copy()
                samples.append(d)
            rest = (TURN @ src.matrix_world @ src.data.bones['B_Pelvis'].head_local.to_4d()).to_3d()
            out[name] = (dur, samples)
            out['_rest_pelvis'] = rest
        for o in new_o: bpy.data.objects.remove(o, do_unlink=True)
        for a in new_a: bpy.data.actions.remove(a)
    return out


def sample(src, name, t, bone):
    dur, vals = src[name]; u = max(0.0, min(t, dur)) * FPS
    i = min(int(u), len(vals) - 1); j = min(i + 1, len(vals) - 1)
    if bone == '_pelvis':
        return vals[i][bone].lerp(vals[j][bone], u - int(u))
    return vals[i][bone].slerp(vals[j][bone], u - int(u))


def set_world_rot(rig, n, q):
    pb = rig.pose.bones[n]; M = q.to_matrix().to_4x4(); M.translation = pb.matrix.translation.copy()
    pb.matrix = M; bpy.context.view_layer.update()


LIMIT = ['B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck', 'B_Head', 'B_L_Clavicle', 'B_R_Clavicle'] + \
        [f'B_{s}_{b}' for s in 'LR' for b in ('UpperArm', 'Forearm', 'Hand')]
MAX_STEP = math.radians(24)
TWIST_SHARE = 0.6             # playbook: forearm twist bone 0.6 of the hand roll


def author(rig, scene, src, name, base, seconds, layers, base_time=None, post=None, limit=True):
    """Write action `name` (seconds long, keys at 48 Hz). base: a native action; base_time(t) -> base seconds
    (default: t looped over the base's length). post(t): optional callback after the layers (finger poses, fixes)."""
    seconds = round(seconds * FPS) / FPS                           # whole 48 Hz frames (exact clip lengths)
    order = [b.name for b in rig.data.bones]
    bfps = 24.0                                                    # the imported Overseer clips' frame rate
    blen = (base.frame_range[1] - base.frame_range[0]) / bfps
    bt = base_time or (lambda t: t % blen)
    times = [k / FPS for k in range(int(round(seconds * FPS)) + 1)]
    poses = []
    for t in times:                                                # sample the base first (one action active at a time)
        set_action(rig, base); frame_at(scene, base.frame_range[0] + bt(t) * bfps)
        poses.append({n: rig.pose.bones[n].matrix_basis.copy() for n in order})
    act = bpy.data.actions.new(name); act.use_fake_user = True
    set_action(rig, act); prev = {}; prev_w = {}; prev_roll = {}
    for t, pose in zip(times, poses):
        for n, M in pose.items(): rig.pose.bones[n].matrix_basis = M
        bpy.context.view_layer.update()
        for L in layers:
            w = L['w'](t)
            if w <= 0: continue
            st = L['t'](t)
            if L.get('pelvis_loc'):                            # grounded sets: the source pelvis path, scaled
                pb = rig.pose.bones['B_Pelvis']; rest = rig.data.bones['B_Pelvis'].head_local
                off = (sample(src, L['src'], st, '_pelvis') - src['_rest_pelvis']) * L['pelvis_loc']
                M = pb.matrix.copy(); M.translation = M.translation.lerp(rest + off, w); pb.matrix = M
                bpy.context.view_layer.update()
            for n in L['bones']:
                if L.get('rel'):                                    # the source pose relative to this bone
                    ref = L['rel']
                    q_src = sample(src, L['src'], st, n); c_src = sample(src, L['src'], st, ref)
                    q = rig.pose.bones[ref].matrix.to_quaternion() @ c_src.inverted() @ q_src
                else:
                    q = sample(src, L['src'], st, n)
                cur = rig.pose.bones[n].matrix.to_quaternion()
                if cur.dot(q) < 0: q.negate()
                set_world_rot(rig, n, cur.slerp(q, w))
        if limit:                                                  # angular rate limit (world, parents first), before
            #                                                        the post hook so the support IK follows the limited arm
            for n in LIMIT:
                pb = rig.pose.bones[n]; cur = pb.matrix.to_quaternion()
                if n in prev_w:
                    if cur.dot(prev_w[n]) < 0: cur.negate()
                    ang = prev_w[n].rotation_difference(cur).angle
                    if ang > MAX_STEP:
                        set_world_rot(rig, n, prev_w[n].slerp(cur, MAX_STEP / ang)); cur = pb.matrix.to_quaternion()
                prev_w[n] = cur.copy()
        if post: post(t)                                           # fists, floor, clearance, support IK
        for side in 'LR':                                          # forearm twist helper takes 60 % of the hand's roll
            tw = rig.pose.bones[f'B_{side}_ForearmTwist']; tw.rotation_mode = 'QUATERNION'
            _, roll = wrist_cost(rig, side, rig.pose.bones[f'B_{side}_Hand'].matrix.to_3x3().normalized())
            if side in prev_roll:                                  # unwrapped across frames (no 360 deg flip)
                roll = prev_roll[side] + ((roll - prev_roll[side] + 180) % 360 - 180)
            prev_roll[side] = roll
            share = max(-85.0, min(85.0, TWIST_SHARE * roll))      # under the gate's 90 deg forearm roll
            tw.rotation_quaternion = Quaternion((0, 1, 0), math.radians(share))
        bpy.context.view_layer.update()
        for n in order:
            pb = rig.pose.bones[n]; loc, q, sc = pb.matrix_basis.decompose()
            if n in prev and q.dot(prev[n]) < 0: q.negate()
            prev[n] = q.copy(); pb.rotation_mode = 'QUATERNION'
            pb.location = loc; pb.rotation_quaternion = q; pb.scale = sc
            for path in ('location', 'rotation_quaternion', 'scale'):
                pb.keyframe_insert(path, frame=t * FPS)
    act.use_frame_range = True; act.frame_start = 0; act.frame_end = seconds * FPS
    return act


def two_bone_ik(rig, side, wrist, hand_rot, phi=0.0):
    """Put B_<side>_Hand's head at `wrist` (armature space) with world rotation `hand_rot` (Quaternion), the elbow kept a
    hinge (mm6_natm_claude/scripts/armik.py `solve`, copied): the upper arm swings onto the new shoulder -> elbow line and
    rolls by the change of the elbow-plane normal, the forearm swings onto elbow -> wrist. The elbow plane is the current
    one turned by `phi` degrees about the shoulder -> wrist line. Returns the miss (m) when out of reach."""
    ua, fa, hd = (rig.pose.bones[f'B_{side}_{b}'] for b in ('UpperArm', 'Forearm', 'Hand'))
    S = ua.head.copy(); E0 = fa.head.copy(); W0 = hd.head.copy()
    L1, L2 = (E0 - S).length, (W0 - E0).length
    T = Vector(wrist); d = T - S; miss = max(0.0, d.length - (L1 + L2) * 0.999)
    if miss > 0: T = S + d.normalized() * (L1 + L2) * 0.999; d = T - S
    dist = d.length; u = d.normalized()
    r = (W0 - S).normalized(); p = (E0 - S) - r * (E0 - S).dot(r)
    p = p if p.length > 1e-6 else Vector((0, 0, -1))
    p = Quaternion(u, math.radians(phi)) @ ((W0 - S).normalized().rotation_difference(u) @ p)
    v = p - u * p.dot(u); v = v.normalized() if v.length > 1e-6 else u.orthogonal().normalized()
    ca = max(-1.0, min(1.0, (L1 * L1 + dist * dist - L2 * L2) / (2 * L1 * dist)))
    E = S + L1 * (u * ca + v * math.sqrt(max(0.0, 1 - ca * ca)))
    a0, a1 = (E0 - S).normalized(), (E - S).normalized()
    q = a0.rotation_difference(a1)
    n0 = (E0 - S).cross(W0 - E0); n1 = (E - S).cross(T - E)
    if n0.length > 1e-6 and n1.length > 1e-6:
        n0 = q @ n0; n0 = (n0 - a1 * n0.dot(a1)).normalized(); n1 = (n1 - a1 * n1.dot(a1)).normalized()
        q = Quaternion(a1, math.atan2(a1.dot(n0.cross(n1)), n0.dot(n1))) @ q
    M = ua.matrix.copy(); R = (q.to_matrix() @ M.to_3x3().normalized()).to_4x4(); R.translation = M.translation; ua.matrix = R
    bpy.context.view_layer.update()
    Mf = fa.matrix.copy(); f0 = (hd.head - Mf.translation).normalized()
    qf = f0.rotation_difference((T - Mf.translation).normalized())
    R = (qf.to_matrix() @ Mf.to_3x3().normalized()).to_4x4(); R.translation = Mf.translation; fa.matrix = R
    bpy.context.view_layer.update()
    set_world_rot(rig, hd.name, hand_rot)
    return miss


def wrist_cost(rig, side, hand_rot):
    """(swing deg, twist deg) of a hand world rotation against its forearm, relative to the rest relation
    (mm6_natm_claude/scripts/armik.py)."""
    fa, hd = f'B_{side}_Forearm', f'B_{side}_Hand'
    Mf = rig.pose.bones[fa].matrix.to_3x3().normalized()
    rest_rel = rig.data.bones[fa].matrix_local.to_3x3().inverted() @ rig.data.bones[hd].matrix_local.to_3x3()
    q = (rest_rel.inverted() @ (Mf.inverted() @ hand_rot)).to_quaternion()
    axis = Vector((0, 1, 0))
    t = 2 * math.atan2(Vector((q.x, q.y, q.z)).dot(axis), q.w); t = (t + math.pi) % (2 * math.pi) - math.pi
    sw = q @ Quaternion(axis, t).inverted()
    return math.degrees(min(sw.angle, 2 * math.pi - sw.angle)), math.degrees(t)


PHIS = (-60, -30, 0, 30, 60)


def grip_candidates(rel0, axis_w):
    """120 rigid support grips: rel0 turned about the handle (weapon-frame axis) every 30 deg, on both sides, each with
    the elbow plane turned by one of PHIS (deg)"""
    perp = axis_w.orthogonal().normalized()
    out = []
    for flip in (False, True):
        base = (Matrix.Rotation(math.pi, 3, perp) @ rel0) if flip else rel0
        out += [(Matrix.Rotation(math.radians(a), 3, axis_w) @ base, phi) for a in range(0, 360, 30) for phi in PHIS]
    return out


def support_grip(rig, mount_R, grip_pt, grip_axis, source_hand_q, release=(0.15, 0.35), state=None, pts=None):
    """The left fist on a weapon held by the right: the weapon's frame is Grip_R's pose @ mount_R (4x4, weapon ->
    socket); the support handle passes through grip_pt along grip_axis (weapon coords). The grip (Grip_L's rotation in
    the weapon's frame, `state['rel']`) is held rigidly for the whole clip, so it never flips. On the clip's first frame
    it starts from the clip's own left hand turned the least onto the handle; with state['trial'] (a dry pass), every
    candidate grip is solved and scored per frame (wrist bend + 0.35 x twist + reach miss + the weapon's `pts` inside the
    support forearm) into state['costs'], so the clip can be authored again with the best (the playbook's least wrist
    bend chosen over the whole clip, armik.py). Where the clip's own left grip is `release` (m) away from the handle,
    the grip blends back to the clip's hand. Returns the reach miss (m) while fully gripping."""
    W = rig.pose.bones['Grip_R'].matrix @ mount_R
    Wr = W.to_3x3().normalized()
    P = W @ Vector(grip_pt); A = (W.to_3x3() @ Vector(grip_axis)).normalized()
    gl = rig.data.bones['Grip_L']; hl = rig.data.bones['B_L_Hand']
    G_in_H = hl.matrix_local.inverted() @ gl.matrix_local                 # the grip socket in the hand's frame
    if state is None or 'rel' not in state:
        cur = source_hand_q.to_matrix() @ G_in_H.to_3x3()                 # Grip_L's rotation with the clip's hand
        z = cur.col[2]; best = None
        for sgn in (1, -1):
            q = z.rotation_difference(A * -sgn)
            if best is None or q.angle < best[0]: best = (q.angle, q)
        rel = Wr.inverted() @ (best[1].to_matrix() @ cur)
        if state is not None:
            state['rel'] = (rel, 0)
            if 'trial' in state and state['trial'] is None:
                state['trial'] = grip_candidates(rel, Vector(grip_axis).normalized()); state['costs'] = [0.0] * len(state['trial'])
                state['rel'] = (rel, 0)
    src_grip = rig.pose.bones['Grip_L'].matrix.translation.copy(); src_wrist = rig.pose.bones['B_L_Hand'].head.copy()
    w = 1.0 - smooth(((src_grip - P).length - release[0]) / (release[1] - release[0]))
    if state is not None:                                        # let go and take hold over >= 8 frames, not in one
        wp = state.get('w_prev', w); w = max(wp - 0.12, min(wp + 0.12, w)); state['w_prev'] = w
    if w <= 0:
        return 0.0
    q = source_hand_q.copy()

    def place(cand):
        rel, phi = cand
        grip_rot = Wr @ rel
        hand_rot = (grip_rot @ G_in_H.to_3x3().inverted()).to_quaternion()
        G = grip_rot.to_4x4(); G.translation = P
        wrist = (G @ G_in_H.inverted()).translation
        qq = q.copy()
        if qq.dot(hand_rot) < 0: qq.negate()
        return two_bone_ik(rig, 'L', src_wrist.lerp(wrist, w), qq.slerp(hand_rot, w), phi * w), hand_rot
    if state is not None and state.get('trial'):
        arm = [f'B_L_{b}' for b in ('UpperArm', 'Forearm', 'Hand')]
        snap = {n: rig.pose.bones[n].matrix_basis.copy() for n in arm}
        for k, cand in enumerate(state['trial']):
            miss, hand_rot = place(cand)
            sw, tw = wrist_cost(rig, 'L', hand_rot.to_matrix())
            c = sw + 0.35 * abs(tw) + 300 * miss
            if pts:                                                   # the weapon inside the support forearm
                E = rig.pose.bones['B_L_Forearm'].head; H = rig.pose.bones['B_L_Hand'].head; d = H - E
                for p in pts:
                    x = W @ Vector(p); u = max(0.0, min(1.0, (x - E).dot(d) / d.length_squared))
                    c += 200 * max(0.0, 0.055 - (x - (E + d * u)).length)
            state['costs'][k] += c
            for n in arm: rig.pose.bones[n].matrix_basis = snap[n]
            bpy.context.view_layer.update()
    miss, _ = place(state['rel'] if state is not None else (rel, 0))
    return miss if w > 0.99 else 0.0


def swing_clear(rig, mount_R, points, tree, margin=0.03, iterations=4):
    """Long props out of the body (playbook: turn the least where the shaft enters): `points` (weapon coords) are tested
    against the posed body (`tree`, a BVH in armature space, normals outward); the right upper arm swings about the
    shoulder by the least rotation that puts the deepest offending point `margin` outside. Returns the worst depth (m)."""
    worst0 = None
    for _ in range(iterations):
        W = rig.pose.bones['Grip_R'].matrix @ mount_R
        worst = None
        for p in points:
            q = W @ Vector(p); loc, n, i, d = tree.find_nearest(q)
            if loc is None or d > 0.08: continue                  # only near the skin (a far 'inside' is a sign error)
            depth = margin - (q - loc).dot(n)
            if depth > 0 and (worst is None or depth > worst[0]): worst = (depth, q, n)
        if worst0 is None: worst0 = worst[0] - margin if worst else -1.0
        if worst is None: break
        ua = rig.pose.bones['B_R_UpperArm']; S = ua.head
        v = worst[1] - S; v2 = v + worst[2] * worst[0]
        rq = v.rotation_difference(v2.normalized() * v.length)
        M = Matrix.Translation(S) @ rq.to_matrix().to_4x4() @ Matrix.Translation(-S)
        ua.matrix = M @ ua.matrix; bpy.context.view_layer.update()
    return max(worst0 or 0.0, 0.0)


def mount_matrix(m):
    adj = (Matrix.Rotation(math.radians(m.get('adjust', (0, 0))[0]), 4, 'Z')
           @ Matrix.Rotation(math.radians(m.get('adjust', (0, 0))[1]), 4, 'X'))   # mount_search.py: out of the body
    if 'orbit' in m:                                       # a worn piece turned about the limb's axis (the socket's Z
        deg, ax, ay = m['orbit']                           # through (ax, ay) in socket coords), emitter_search.py
        adj = (Matrix.Translation((ax, ay, 0)) @ Matrix.Rotation(math.radians(deg), 4, 'Z')
               @ Matrix.Translation((-ax, -ay, 0))) @ adj
    return adj @ Matrix.Scale(m.get('scale', 1.0), 4) @ _mount_matrix(m)


def _mount_matrix(m):
    """weapons.json mount -> the 4x4 weapon -> socket transform. Either `axes` (the socket-frame directions of the
    weapon's x, y, z; optional `mirror`: the left-hand copy, z negated) and `roll` (degrees about the socket's Z), or
    `grip_axis` (a pistol grip: the socket's +Z along the grip toward the barrel, the socket's -Y along the barrel `barrel`,
    default weapon +z), or `line` (two-handed: the socket-frame direction from the right grip to the left one in the
    source's carry, grip_lines.json; the weapon's centre -> support point vector is turned onto it, then rolled about it:
    by `roll`, or with a `grip_axis` so that the pistol grip stays nearest the fist's axis), all about `centre` (the grip
    centre, weapon coords)."""
    if 'line' in m:                                        # two-handed: the grip-to-support vector on the source line
        v = (Vector(m['support']['point']) - Vector(m['centre'])).normalized(); line = Vector(m['line']).normalized()
        R0 = v.rotation_difference(line).to_matrix()
        def rolled(a):
            return Matrix.Rotation(math.radians(a), 3, line) @ R0
        if 'grip_axis' in m:                               # keep the pistol grip in the fist (its axis near socket +Z)
            g = Vector(m['grip_axis']).normalized()
            a = min(range(0, 360, 2), key=lambda a: (rolled(a) @ g).angle(Vector((0, 0, 1))))
        else:
            a = m.get('roll', 0)
        return rolled(a).to_4x4() @ Matrix.Translation(-Vector(m['centre']))
    if 'grip_axis' in m:
        g = Vector(m['grip_axis']).normalized(); b = Vector(m.get('barrel', (0, 0, 1)))
        y = -(b - g * b.dot(g)).normalized(); x = y.cross(g)
        R = Matrix((x, y, g)).to_4x4()                     # rows: the socket axes in weapon coords
    else:
        ax = Matrix([m['axes'][0], m['axes'][1], m['axes'][2]]).transposed()
        R = (Matrix.Rotation(math.radians(m.get('roll', 0)), 3, 'Z') @ ax).to_4x4()
    if m.get('mirror'):
        R = Matrix.Diagonal((1, 1, -1, 1)) @ R
    return R @ Matrix.Translation(-Vector(m['centre']))
