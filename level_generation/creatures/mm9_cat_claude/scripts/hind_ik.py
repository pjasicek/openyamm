"""Hind-leg retarget on the delivered clips (Blender module used by build_export.py).

MM9's hind chain is a long femur, a tiny shin and tarsus; the cat's mesh has real proportions and our rest joints sit in
it. For every clip frame MM9's own pose is rebuilt on a copy of the MM9 rig (same bone rotations, MM9's rest), and our leg
is solved to it: ankle and foot take MM9's position and orientation, the tarsus turns with the paw (TARSUS_FOLLOW), and hip,
stifle and hock are a two-bone IK with the stifle forward in the pelvis frame. The result is a pure function of the
resampled curves, so it stays as smooth as they are; loop ends stay equal. Keys of the six hind bones are overwritten."""
import bpy, math, os
from mathutils import Matrix, Quaternion, Vector

LEGS = (('Xblegpiv', 'Xbleg', 'Xblegmid', 'Xbankle', 'Xbfoot'), ('Xblegpiv01', 'Xbleg01', 'Xblegmid01', 'Xbankle01', 'Xbfoot01'))
TARSUS_FOLLOW = 0.6
# MM9's paw targets put our hock close to the hip when the cat sits: the knee would close to 19 degrees and the skin folds.
# Where the knee would close past KNEE_MIN the tarsus turns back about the ankle (paw and ankle stay), down to lying flat, as a
# sitting cat's does. The turn is found per frame, low-passed over the clip (SMOOTH frames, wrapped on loops), then applied.
KNEE_MIN = math.radians(float(os.environ.get("KNEE_MIN", "45")))
TURN_MAX = 80
SMOOTH = 2.0
HOCK_ABOVE_ANKLE = -0.004
LOOPS = {'Standing', 'Walking', 'Running'}


KNEE_TURN = 20.0
KNEE_SPLAY = 0.35


def smooth01(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def low_pass(values, sigma, wrap):
    n = len(values)
    r = int(3 * sigma) + 1
    w = [math.exp(-0.5 * (k / sigma) ** 2) for k in range(-r, r + 1)]
    out = []
    for i in range(n):
        tot = 0.0
        for k, wk in zip(range(-r, r + 1), w):
            j = (i + k) % (n - 1) if wrap else min(max(i + k, 0), n - 1)
            tot += wk * values[j]
        out.append(tot / sum(w))
    return out


def tarsus_turn(H, A, hock, axis, d_min):
    """Smallest turn of the tarsus about the ankle that keeps the hock d_min from the hip, within the floor limit."""
    v = hock - A
    best = 0.0
    for deg in range(0, TURN_MAX + 1):
        w = Quaternion(axis, -math.radians(deg)) @ v
        if deg and w.z < HOCK_ABOVE_ANKLE:
            break
        best = float(deg)
        if ((A + w) - H).length >= d_min:
            break
    return best


def fcurves_of(action):
    return [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]


def load_src(path):
    with bpy.data.libraries.load(path) as (src, dst):
        dst.objects = [n for n in src.objects if n == 'MM9_Rig']
    arm = dst.objects[0]
    arm.name = 'MM9_Src'
    bpy.context.scene.collection.objects.link(arm)
    arm.animation_data_clear()
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
    return arm


def aim(pb, target):
    """Turn pb about its head so its first child segment points at target (armature space)."""
    return


def solve(rig, src, offsets, actions, fps):
    vl = bpy.context.view_layer
    sc = bpy.context.scene
    names = [p.name for p in rig.pose.bones]
    ident = Matrix.Identity(4)
    rest = {b.name: b.matrix_local.copy() for b in rig.data.bones}
    src_rest = {b.name: b.matrix_local.copy() for b in src.data.bones}
    report = {}
    for act in actions:
        rig.animation_data.action = act
        f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        short = 0.0
        pending = []
        turns = {leg[0]: [] for leg in LEGS}
        for f in range(f0, f1 + 1):              # first pass: the tarsus turn each frame would need
            sc.frame_set(f)
            vl.update()
            for n in names:
                src.pose.bones[n].matrix_basis = offsets.get(n, ident) @ rig.pose.bones[n].matrix_basis
            vl.update()
            for hip, shin, tars, ank, foot in LEGS:
                A = src.pose.bones[ank].matrix.copy()
                turn = A.to_quaternion() @ src_rest[ank].to_quaternion().inverted()
                part = Quaternion().slerp(turn, TARSUS_FOLLOW)
                hock = A.translation - (part @ (rest[ank].translation - rest[tars].translation))
                par = rig.data.bones[hip].parent.name
                pel = rig.pose.bones[par].matrix.to_quaternion() @ rest[par].to_quaternion().inverted()
                L1 = (rest[shin].translation - rest[hip].translation).length
                L2 = (rest[tars].translation - rest[shin].translation).length
                d_min = math.sqrt(L1 * L1 + L2 * L2 - 2 * L1 * L2 * math.cos(KNEE_MIN))
                turns[hip].append(tarsus_turn(rig.pose.bones[hip].head.copy(), A.translation, hock, pel @ Vector((1, 0, 0)), d_min))
        wrap = act.name in LOOPS
        turns = {k: low_pass(v, SMOOTH, wrap) for k, v in turns.items()}
        for f in range(f0, f1 + 1):
            sc.frame_set(f)
            vl.update()
            for n in names:
                pb = rig.pose.bones[n]
                src.pose.bones[n].matrix_basis = offsets.get(n, ident) @ pb.matrix_basis
            vl.update()
            keys = {}
            for leg in LEGS:
                hip, shin, tars, ank, foot = leg
                A = src.pose.bones[ank].matrix.copy()
                F = src.pose.bones[foot].matrix.copy()
                # the tarsus turns with the paw: the rest tarsus vector rotated by part of the paw's world turn
                turn = A.to_quaternion() @ src_rest[ank].to_quaternion().inverted()
                part = Quaternion().slerp(turn, TARSUS_FOLLOW)
                t_rest = rest[ank].translation - rest[tars].translation
                hock = A.translation - (part @ t_rest)
                pel = rig.pose.bones[hip].parent.matrix.to_quaternion() @ rest[rig.data.bones[hip].parent.name].to_quaternion().inverted()
                hock = A.translation + Quaternion(pel @ Vector((1, 0, 0)), -math.radians(turns[hip][f - f0])) @ (hock - A.translation)
                fw = (pel @ Vector((0, -1, 0)))
                # a sitting pelvis is pitched past vertical: where the tarsus turns the knee aims forward in the sagittal
                # plane instead, splayed out a little so the thigh lies beside the belly
                k = smooth01(turns[hip][f - f0] / KNEE_TURN)
                if k > 0.0:
                    lat = pel @ Vector((1, 0, 0))
                    side = 1.0 if rest[hip].translation.x > 0 else -1.0
                    ground = Vector((0, -1, 0)) - lat * Vector((0, -1, 0)).dot(lat)
                    fw = (fw * (1 - k) + (ground.normalized() + lat * side * KNEE_SPLAY) * k).normalized()
                H = rig.pose.bones[hip].head.copy()
                L1 = (rest[shin].translation - rest[hip].translation).length
                L2 = (rest[tars].translation - rest[shin].translation).length
                D = hock - H
                d = D.length
                if d > 0.995 * (L1 + L2):
                    short = max(short, d - 0.995 * (L1 + L2))
                    D = D * (0.995 * (L1 + L2) / d)
                    d = D.length
                    hock = H + D
                u = D.normalized()
                p = (fw - u * fw.dot(u)).normalized()
                c = (L1 * L1 + d * d - L2 * L2) / (2 * d)
                h = math.sqrt(max(L1 * L1 - c * c, 0.0))
                K = H + u * c + p * h
                # femur, shin, tarsus: rest pose orientation of the pelvis frame, turned onto the solved segments
                for b, nxt_rest, a0, a1 in ((hip, shin, H, K), (shin, tars, K, hock), (tars, ank, hock, A.translation)):
                    pb = rig.pose.bones[b]
                    vl.update()
                    cur = pb.tail.copy() if False else None
                    seg = (rest[nxt_rest].translation - rest[b].translation).normalized()
                    base = (pel @ seg)
                    q = base.rotation_difference((a1 - a0).normalized()) @ pel
                    pb.matrix = Matrix.Translation(a0) @ (q @ rest[b].to_quaternion()).to_matrix().to_4x4()
                vl.update()
                for b, M in ((ank, A), (foot, F)):
                    pb = rig.pose.bones[b]
                    vl.update()
                    pb.matrix = Matrix.Translation(pb.head.copy()) @ (M.to_quaternion().to_matrix().to_4x4())
                vl.update()
                for b in leg:
                    pb = rig.pose.bones[b]
                    keys[b] = (pb.rotation_quaternion.copy(), pb.location.copy())
            pending.append((f, keys))
        for f, keys in pending:
            for b, (q, l) in keys.items():
                pb = rig.pose.bones[b]
                pb.rotation_quaternion, pb.location = q, l
                pb.keyframe_insert('rotation_quaternion', frame=f)
                pb.keyframe_insert('location', frame=f)
        report[act.name] = round(short, 4)
    return report
