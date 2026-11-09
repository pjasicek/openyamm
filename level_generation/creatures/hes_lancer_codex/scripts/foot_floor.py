"""hkr: the demon's long clawed feet against the floor in the locomotion clips (sole_probe: the set's walk pushed the
toe claws 17 cm into the floor at toe-off: the source foot is short, ours reaches 20 cm past the ball). Per frame and
foot, on the evaluated mesh: the toes first return to their rest relation (playbook rule: the source toe channels
curl our toes); then, if the foot's lowest vertex (Foot/Toe weight > 0.5, claws included) is below FLOOR, the foot turns
about the ankle's lateral axis by the smallest angle (1 deg grid, +-MAXP) that lifts it to the floor; what remains is
taken out by lifting the ankle (thigh/calf two-bone IK, the knee keeping its side) - only for the remaining depth,
so the other leg's contact is untouched. The pitch is chosen over the whole clip (Viterbi: depth + pitch change, the loop seam closed with
CYCLIC=1); the lift is smoothed over time (Gaussian, SIG frames, never below the frame's own need). Keys B_<S>_Foot, B_<S>_Toe0, B_<S>_Thigh, B_<S>_Calf. Args: -- <in> <out> <Action> [...]"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
FLOOR, MAXP, SIG = float(os.environ.get('FLOOR', '0.0')), float(os.environ.get('MAXP', '35')), 1.0
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
AW = rig.matrix_world; AWi = AW.inverted()
vg = [g.name for g in body.vertex_groups]
FOOTV = {s: np.array([sum(e.weight for e in v.groups if vg[e.group] in (f'B_{s}_Foot', f'B_{s}_Toe0')) > 0.5 for v in me.vertices]) for s in 'LR'}


def world(n):
    return AW @ rig.pose.bones[n].matrix


def evaluated():
    e = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); e.to_mesh_clear()
    return co.reshape(-1, 3)


def two_bone(s, target):
    """thigh/calf so the ankle reaches target, the knee in its current plane; the foot keeps its world rotation"""
    th, ca, ft = f'B_{s}_Thigh', f'B_{s}_Calf', f'B_{s}_Foot'
    Mf = world(ft).to_3x3().normalized()
    H, K, A = world(th).translation, world(ca).translation, world(ft).translation
    L1, L2 = (K - H).length, (A - K).length; d = target - H; dist = min(d.length, (L1 + L2) * 0.999)
    u = d.normalized(); pole = (K - H) - u * (K - H).dot(u); pole = pole.normalized() if pole.length > 1e-6 else Vector((0, -1, 0))
    ca_ = max(-1.0, min(1.0, (L1 * L1 + dist * dist - L2 * L2) / (2 * L1 * dist)))
    Knew = H + L1 * (u * ca_ + pole * math.sqrt(max(0.0, 1 - ca_ * ca_)))
    q = (K - H).normalized().rotation_difference((Knew - H).normalized())
    M = world(th); R = q.to_matrix() @ M.to_3x3().normalized(); N = R.to_4x4(); N.translation = M.translation
    rig.pose.bones[th].matrix = AWi @ N; bpy.context.view_layer.update()
    M = world(ca); A2 = world(ft).translation
    q = (A2 - M.translation).normalized().rotation_difference((H + d.normalized() * dist - M.translation).normalized())
    R = q.to_matrix() @ M.to_3x3().normalized(); N = R.to_4x4(); N.translation = M.translation
    rig.pose.bones[ca].matrix = AWi @ N; bpy.context.view_layer.update()
    M = world(ft); N = Mf.to_4x4(); N.translation = M.translation
    rig.pose.bones[ft].matrix = AWi @ N; bpy.context.view_layer.update()


BONES = [f'B_{s}_{b}' for s in 'LR' for b in ('Thigh', 'Calf', 'Foot', 'Toe0')]
for name in acts:
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); frames = list(range(f0, f1 + 1))
    need, hover = {}, {}
    for f in frames:                                       # pass 1: the pitch and lift each foot needs
        sc.frame_set(f)
        for s in 'LR':
            rig.pose.bones[f'B_{s}_Toe0'].matrix_basis = Matrix()
        bpy.context.view_layer.update()
        P = evaluated()
        for s in 'LR':
            pts = P[FOOTV[s]]; ank = np.array(world(f'B_{s}_Foot').translation)
            fd = np.array(world(f'B_{s}_Foot').to_3x3().col[1]); lat = np.cross(fd, [0, 0, 1.0]); lat /= np.linalg.norm(lat) + 1e-9
            grid = np.arange(-int(MAXP), int(MAXP) + 1, dtype=float)
            dep = np.empty(len(grid)); hov = np.empty(len(grid)); low0 = pts[:, 2].min()
            for i, deg in enumerate(grid):
                R = np.array(Matrix.Rotation(math.radians(deg), 3, Vector(lat)))
                q = (pts - ank) @ R.T + ank; lo = q[:, 2].min()
                dep[i] = max(0.0, FLOOR - lo); hov[i] = max(0.0, lo - max(low0, FLOOR))   # below / lifted off
            need[(f, s)] = dep; hover[(f, s)] = hov
    # the pitch per frame by a global choice (Viterbi): residual depth (cm) + a small pitch cost + the pitch change
    # between frames, so a foot neither snaps between heel-down and toe-up nor jumps at the loop seam (CYCLIC: the
    # last frame repeats the first, its pitch is forced equal). The depth the pitch leaves is lifted at the ankle.
    grid = np.arange(-int(MAXP), int(MAXP) + 1, dtype=float); CYC = bool(os.environ.get('CYCLIC'))
    KD, KP, KC = float(os.environ.get('KDEPTH', '1')), 0.02, float(os.environ.get('KCHANGE', '0.3'))
    KH = float(os.environ.get('KHOVER', '3'))          # per cm the pitch lifts the foot's lowest point off its own height
    trans = KC * np.abs(grid[:, None] - grid[None, :])
    choice = {}
    for s in 'LR':
        unary = [KD * 100 * need[(f, s)] + KH * 100 * hover[(f, s)] + KP * np.abs(grid) for f in frames]
        def viterbi(start=None):
            c = unary[0].copy()
            if start is not None: c = np.where(np.arange(len(grid)) == start, c, 1e9)
            back = []
            for u in unary[1:]:
                t = c[:, None] + trans; b = t.argmin(0); back.append(b); c = t[b, np.arange(len(grid))] + u
            if start is not None: c = np.where(np.arange(len(grid)) == start, c, 1e9)
            i = int(c.argmin()); path = [i]
            for b in reversed(back): i = int(b[i]); path.append(i)
            return float(c.min()), path[::-1]
        if CYC:
            best = min((viterbi(st) for st in range(len(grid))), key=lambda r: r[0])
        else:
            best = viterbi()
        for f, i in zip(frames, best[1]):
            choice[(f, s)] = (float(grid[i]), float(need[(f, s)][i]))
    need = choice
    print('FOOTPITCH', name, {s: [round(need[(f, s)][0]) for f in frames] for s in 'LR'})
    keys = {}
    for f in frames:
        sc.frame_set(f)
        for s in 'LR':
            rig.pose.bones[f'B_{s}_Toe0'].matrix_basis = Matrix()
        bpy.context.view_layer.update()
        for s in 'LR':
            n_ = len(frames) - 1
            dist = (lambda g: min(abs(g - f), n_ - abs(g - f))) if os.environ.get('CYCLIC') else (lambda g: abs(g - f))
            k = [math.exp(-0.5 * (dist(g) / SIG) ** 2) for g in frames]
            pit = need[(f, s)][0]
            lift = max(need[(f, s)][1], sum(kk * need[(g, s)][1] for kk, g in zip(k, frames)) / sum(k))
            ft = f'B_{s}_Foot'; M = world(ft)
            fd = M.to_3x3().col[1]; lat = fd.cross(Vector((0, 0, 1))).normalized()
            if abs(pit) > 1e-3:
                R = Matrix.Rotation(math.radians(pit), 3, lat) @ M.to_3x3().normalized(); N = R.to_4x4(); N.translation = M.translation
                rig.pose.bones[ft].matrix = AWi @ N; bpy.context.view_layer.update()
            if lift > 1e-4:
                two_bone(s, world(ft).translation + Vector((0, 0, lift)))
        keys[f] = {n: rig.pose.bones[n].matrix_basis.to_quaternion() for n in BONES}
    prev = {}
    for f in frames:
        for n in BONES:
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; q = keys[f][n]
            if n in prev and q.dot(prev[n]) < 0: q = -q
            prev[n] = q; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
    worst = max(v[1] for v in need.values()); maxp = max(abs(v[0]) for v in need.values())
    print('FOOTFLOOR', name, 'pitch max deg', round(maxp, 1), 'ankle lift max cm', round(worst * 100, 1))
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
