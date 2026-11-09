"""Club clearance (m302: the modelled club, club_frame.py; after m190's axe clearance, natm spear_clear.py via mm7_m222_claude's scimitar version) for clips that keep their source arms: per frame, if the blade
(grip axis from work/grip_pose.json: the haft from the butt, -0.11 m, to the spike, +0.59 m, the fist +-6 cm skipped) passes inside the skin (garment 0, the right arm
excluded; inside = behind the nearest face within a 45 deg cone, 8 cm search), the hand is turned about the wrist by
the smallest rotation (directions every 30 deg around the shaft, 3..36 deg) that clears it with a 1.5 cm margin.
The per-frame angles are dilated by 2 frames and smoothed (Gaussian, sigma 1.5 frames) so the hand eases in and out.
Runs before twist_bones.py (the forearm twist is baked from the final hand). Args: -- <in blend> <out blend> <Action> ..."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Quaternion, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik, common
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
G = json.load(open(os.path.join(common.WORK, 'grip_pose.json')))
AX = Vector(G['handle_axis_hand_local']).normalized(); GC = Vector(G['handle_centre_hand_local'])
gv = np.zeros(len(me.vertices), np.int32)
if 'garment' in me.attributes:
    me.attributes['garment'].data.foreach_get('value', gv)
else:                                                         # before weights_fix.py: its piece -> label map
    pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
    GL = json.load(open(os.path.join(common.WORK, 'garments.json'))); gv = np.array([GL.get(str(p), 4) for p in pv], np.int32)
names = [g.name for g in body.vertex_groups]
armw = np.zeros(len(me.vertices))
for v in me.vertices:
    armw[v.index] = sum(e.weight for e in v.groups if names[e.group].startswith('B_R_') and any(k in names[e.group] for k in ('UpperArm', 'Forearm', 'Hand', 'Finger')))
KEEP_G = [int(x) for x in os.environ.get('KEEP_GARMENTS', '0,1').split(',')]   # 7m452 Death: + 6, the tunic skirt over the thighs
keep = np.isin(gv, KEEP_G) & (armw < 0.2)
faces = [tuple(p.vertices) for p in me.polygons if all(keep[i] for i in p.vertices)]



def set_act(x):
    rig.animation_data_create(); rig.animation_data.action = x
    if x is not None and len(x.slots): rig.animation_data.action_slot = x.slots[0]


# m302: the club's surface (prop space -> hand local) beyond the fist is sampled as well as its axis; with FLOOR=1 the
# floor (z = 0) counts as a surface (the death lies the club down)
import club_frame
CLUB = json.load(open(os.path.join(common.WORK, 'club.json')))
T = np.concatenate([np.linspace(CLUB['butt_y'], -0.06, 10), np.linspace(0.06, CLUB['top_y'], 24)])   # 10 on the 39 cm butt end (3 missed the thigh)
MARGIN = float(os.environ.get('MARGIN', '0.02'))
if os.environ.get('GRIP', '0') == '1':      # 7m452 Death: the fist itself pressed the shaft into the left thigh; sample the grip too
    T = np.concatenate([T, np.linspace(-0.05, 0.05, 5)])
AXM = club_frame.hand_local(rig)
AX = (AXM.to_3x3() @ Vector((0, 1, 0))).normalized(); GC = AXM.translation.copy()   # the club frame's axis (CLUB_FLIP)
_ax = club_frame.load_club(sc); _bv = np.array([tuple(v.co) for v in _ax.data.vertices]); bpy.data.objects.remove(_ax, do_unlink=True)
_bl = _bv[_bv[:, 1] > 0.12] if os.environ.get('ALLVERTS', '0') != '1' else _bv   # the thick part and the head; ALLVERTS: every part
BLADE = [AXM @ Vector(tuple(p)) for p in _bl[::max(1, len(_bl) // int(os.environ.get('NSAMP', '60')))]]
FLOOR = bool(int(os.environ.get('FLOOR', '0')))
MAXANG = int(os.environ.get('MAXANG', '45'))      # 7m452 Death: 90 (the 1.4 m pole swings across the front of the body)
# PARITY=1 (7m452 Death, review 2026-10-20): a shaft driven past the centre of a thigh is nearest to the far side of the
# leg and read as outside; a point is also inside when rays along +-X, +-Y and +Z (0.4 m) cross the kept surfaces an odd
# number of times in at least 3 of the 5 directions
PARITY = bool(int(os.environ.get('PARITY', '0')))
_DIRS = [Vector(v) for v in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1))]


def inside_parity(tree, p):
    odd = 0
    for dv in _DIRS:
        o, n, left = p.copy(), 0, 0.4
        while left > 0:
            loc, nrm, idx, dl = tree.ray_cast(o, dv, left)
            if loc is None:
                break
            n += 1; left -= dl + 1e-4; o = loc + dv * 1e-4
        odd += n % 2
    return odd >= 3


def depth(tree, H):
    g = H @ GC; d = (H.to_3x3() @ AX).normalized(); worst = 0.0
    for p in [g + d * t for t in T] + [H @ q for q in BLADE]:
        if FLOOR and p.z < 0.02:                           # the floor keeps a 2 cm margin whatever MARGIN is
            worst = max(worst, 0.02 - p.z)
        loc, nrm, idx, dist = tree.find_nearest(p, 0.2)       # m222: deep crossings (13 cm) are missed at 8 cm
        if loc is None: continue
        if (p - loc).dot(nrm) < -0.7 * dist or (PARITY and inside_parity(tree, p)): worst = max(worst, dist + MARGIN)
        elif dist < MARGIN: worst = max(worst, MARGIN - dist)
    return worst



CONSIST = os.environ.get('CONSIST', '0') == '1'
# CONSIST=1 (7m452 Death, review 2026-10-20): the per-frame search picked a different turn axis in neighbouring frames and
# the smoothing of the axis-angle vectors averaged them out (the shaft stayed 5 cm in the thigh). One axis in the hand's
# own frame (12 directions across the grip axis) for the whole clip, the one that clears every contact frame with the
# least summed turn; per frame the smallest clearing angle, dilated and smoothed as a scalar, then verified and raised
# where a frame still touches (3 rounds).
AXL = (AXM.to_3x3() @ Vector((0, 1, 0))).normalized()
_u = AXL.orthogonal().normalized(); _w = AXL.cross(_u)
LOCAL_AXES = [(_u * math.cos(2 * math.pi * k / 12) + _w * math.sin(2 * math.pi * k / 12)).normalized() for k in range(12)]


_CACHE = {}


def posed_depth(act, f, ang_deg, axis_l):
    if (act.name, f) not in _CACHE:                  # the kept surfaces do not move with the hand
        set_act(act); sc.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        P = [body.matrix_world @ v.co for v in m.vertices]; ev.to_mesh_clear()
        _CACHE[(act.name, f)] = (BVHTree.FromPolygons(P, faces), armik.W(rig, 'B_R_Hand').copy())
    tree, H = _CACHE[(act.name, f)]
    R = H.to_3x3().normalized() @ Quaternion(axis_l, math.radians(ang_deg)).to_matrix()
    H2 = R.to_4x4(); H2.translation = H.translation
    return depth(tree, H2), tree, H


def consist_clear(an):
    act = bpy.data.actions[an]; f0, f1 = int(act.frame_range[0]), int(act.frame_range[1]); frames = list(range(f0, f1 + 1))
    d0 = {f: posed_depth(act, f, 0, LOCAL_AXES[0])[0] for f in frames}
    hit = [f for f in frames if d0[f] > 0]
    spans = []                                                   # contiguous contact spans (gaps of 4+ frames split)
    for f in hit:
        if spans and f - spans[-1][-1] < 5:
            spans[-1].append(f)
        else:
            spans.append([f])
    angs, axis_of, chosen = {}, {}, []
    for sp in spans:
        best = None
        for ki, ax_ in enumerate(LOCAL_AXES):
            a_s = {}
            for f in sp:
                a_ = next((g for g in range(3, MAXANG + 1, 3) if posed_depth(act, f, g, ax_)[0] == 0.0), None)
                if a_ is None:
                    break
                a_s[f] = a_
            if len(a_s) == len(sp):
                cost = sum(v * v for v in a_s.values())
                if best is None or cost < best[0]:
                    best = (cost, ki, a_s)
        if best is None:                                         # fall back to the axis that clears the most frames
            print(f'SWORDCLEAR {an}: CONSIST span {sp[0]}-{sp[-1]} not fully clearable within {MAXANG} deg'); continue
        chosen.append((sp[0], sp[-1], best[1]))
        for f in range(max(f0, sp[0] - 6), min(f1, sp[-1] + 6) + 1):
            axis_of[f] = best[1]
        angs.update(best[2])
    ax_frame = {f: LOCAL_AXES[axis_of.get(f, 0)] for f in frames}
    raw = np.array([angs.get(f, 0.0) for f in frames], float)
    for rnd in range(4):
        n = len(raw); dil = np.array([raw[max(0, i - 3):i + 4].max() for i in range(n)])
        gk = np.exp(-0.5 * (np.arange(-4, 5) / 1.5) ** 2); gk /= gk.sum()
        pad = np.concatenate([np.repeat(dil[:1], 4), dil, np.repeat(dil[-1:], 4)])
        sm = np.maximum(np.convolve(pad, gk, 'valid'), raw)
        still = [i for i, f in enumerate(frames) if posed_depth(act, f, sm[i], ax_frame[f])[0] > 0]
        if not still or rnd == 3:
            break
        for i in still:
            raw[i] = min(MAXANG, raw[i] + 6)
    for i, f in enumerate(frames):
        set_act(act); sc.frame_set(f)
        pb = rig.pose.bones['B_R_Hand']; H = armik.W(rig, 'B_R_Hand')
        if sm[i] > 1e-3:
            R = H.to_3x3().normalized() @ Quaternion(ax_frame[f], math.radians(sm[i])).to_matrix()
            snap = {p.name: p.matrix_basis.copy() for p in rig.pose.bones}
            set_act(None)
            for p in rig.pose.bones: p.matrix_basis = snap[p.name]
            bpy.context.view_layer.update()
            armik.set_world(rig, 'B_R_Hand', armik.rot_world(H, R))
            qq = pb.rotation_quaternion.copy(); set_act(act); pb.rotation_quaternion = qq
        pb.keyframe_insert('rotation_quaternion', frame=f)
    set_act(None)
    print(f'SWORDCLEAR {an}: CONSIST spans/axes {chosen}, frames with contact {len(hit)} of {len(frames)}, worst {max(d0.values()) * 100:.1f} cm, '
          f'max turn {sm.max():.0f} deg, still touching after {rnd + 1} rounds: {len(still)}')


for an in acts:
    if CONSIST:
        consist_clear(an); continue
    act = bpy.data.actions[an]; f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    rots = []
    for f in range(f0, f1 + 1):
        set_act(act); sc.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        P = [body.matrix_world @ v.co for v in m.vertices]; ev.to_mesh_clear()
        tree = BVHTree.FromPolygons(P, faces)
        H = armik.W(rig, 'B_R_Hand'); d0 = depth(tree, H)
        best = (0.0, Quaternion())
        if d0 > 0:
            dax = (H.to_3x3() @ AX).normalized(); u = dax.orthogonal().normalized(); w = dax.cross(u)
            found = None
            for ang in range(3, MAXANG + 1, 3):
                for k in range(12):
                    th = 2 * math.pi * k / 12; axis = (u * math.cos(th) + w * math.sin(th))
                    q = Quaternion(axis, math.radians(ang))
                    R = q.to_matrix() @ H.to_3x3(); H2 = R.to_4x4(); H2.translation = H.translation
                    if depth(tree, H2) == 0.0:
                        found = (ang, q); break
                if found: break
            best = found if found else (float(MAXANG), Quaternion())
        if os.environ.get('SCDEBUG') and 14 <= f <= 24:
            print('SCDEBUG', an, f, 'd0 cm', round(d0 * 100, 1), 'turn', best[0])
        rots.append((d0, best))
    # dilate + smooth the rotation (as axis-angle vectors)
    vec = np.array([np.array(q.axis) * math.radians(ang) if ang else np.zeros(3) for d0, (ang, q) in rots])
    mag = np.linalg.norm(vec, axis=1)
    n = len(vec); vd = vec.copy()
    for i in range(n):
        j = max(range(max(0, i - 3), min(n, i + 4)), key=lambda k: mag[k]); vd[i] = vec[j] if mag[j] > mag[i] else vec[i]
    gk = np.exp(-0.5 * (np.arange(-4, 5) / 1.5) ** 2); gk /= gk.sum()
    pad = np.concatenate([np.repeat(vd[:1], 4, 0), vd, np.repeat(vd[-1:], 4, 0)])
    vs = np.array([sum(gk[k] * pad[i + k] for k in range(9)) for i in range(n)])
    for i, f in enumerate(range(f0, f1 + 1)):
        set_act(act); sc.frame_set(f)
        snap = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
        set_act(None)
        for pb in rig.pose.bones: pb.matrix_basis = snap[pb.name]
        bpy.context.view_layer.update()
        ang = np.linalg.norm(vs[i])
        if ang > 1e-4:
            q = Quaternion(Vector(vs[i] / ang), ang); H = armik.W(rig, 'B_R_Hand')
            armik.set_world(rig, 'B_R_Hand', armik.rot_world(H, q.to_matrix() @ H.to_3x3().normalized()))
        pb = rig.pose.bones['B_R_Hand']; qq = pb.rotation_quaternion.copy()
        set_act(act); pb.rotation_quaternion = qq; pb.keyframe_insert('rotation_quaternion', frame=f)
    set_act(None)
    hit = [i for i, (d0, _) in enumerate(rots) if d0 > 0]
    print(f'SWORDCLEAR {an}: frames with contact {len(hit)} of {n}, worst {max([d0 for d0, _ in rots] + [0]) * 100:.1f} cm, '
          f'max turn {math.degrees(float(np.linalg.norm(vs, axis=1).max())):.0f} deg, unresolved {sum(1 for d0, (ang, q) in rots if d0 > 0 and ang >= MAXANG)}')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
