"""hkr G5: close the demon's open claw hands into fists around a carbine handle (rest pose, hand-local).

Hand frame from the rest mesh: f = wrist -> middle knuckle, palm normal n = the side the demon's curled claws already
bend toward (mean fingertip offset from the knuckle plane), the knuckle line k = pinky -> index knuckle made
perpendicular to f (toward the thumb). Handle: a cylinder of radius R_HANDLE along k (tilted TILT_DEG about n, the
butt toward the heel of the hand), centre = knuckle centre + f x CEN_F of the proximal phalanx + n x (R + the
fingers' half thickness), so the proximal phalanges lie over it.
Fingers 1-4: each joint flexes in turn (proximal first) about the finger's own lateral axis (segment x n), the angle
chosen on a 1-degree grid so the segment's skin samples (its vertices within the bone's reach, weight > 0.5) stay at
least CLEAR outside the handle surface while hugging it (mean radial gap minimised); the claw (rigid on the distal
bone) must not enter the handle or the palm. Thumb: swing about f toward the handle, then flex of its two outer
joints, same rule. Result per side: work/grip_pose_<S>.json = {finger_local: {bone: quat (matrix_basis)},
handle_centre_hand_local, handle_axis_hand_local, R}, plus a report. Args: -- <blend> [R_HANDLE]"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = float(a[1]) if len(a) > 1 else float(os.environ.get('R_HANDLE', '0.021'))
CLEAR = float(os.environ.get('CLEAR', '0.003'))
CEN_F = float(os.environ.get('CEN_F', '0.45'))
TILT = math.radians(float(os.environ.get('TILT_DEG', '12')))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
CO = np.array([v.co[:] for v in me.vertices])
gidx = {g.name: g.index for g in body.vertex_groups}
WT = np.zeros((len(CO), len(gidx)), np.float32)
for v in me.vertices:
    for g in v.groups: WT[v.index, g.group] = g.weight
claw_v = np.zeros(len(CO), bool)
for p in me.polygons:
    if body.material_slots[p.material_index].name.startswith('Demon_White_Claws'):
        claw_v[list(p.vertices)] = True


def chain(s, i):
    if s == 'R' and i == 0:
        return ['B_R_Finger0', 'B_R_Finger0.001', 'B_R_Finger0.002']
    return [f'B_{s}_Finger{i}', f'B_{s}_Finger{i}1', f'B_{s}_Finger{i}2']


def rest(n):
    return rig.data.bones[n].matrix_local.copy()


out_all = {}
for s in 'LR':
    hand = f'B_{s}_Hand'; Hm = rest(hand); wr = Vector(Hm.translation)
    kn = {i: rest(chain(s, i)[0]).translation for i in range(5)}
    tips = {}
    for i in range(5):
        tb = rig.data.bones[chain(s, i)[2]]
        tips[i] = tb.tail_local.copy()
    f = (kn[2] - wr).normalized()
    kmid = (kn[1] + kn[2] + kn[3] + kn[4]) / 4
    off = sum(((tips[i] - kmid) - f * (tips[i] - kmid).dot(f) for i in (1, 2, 3, 4)), Vector())
    k = kn[1] - kn[4]; k = (k - f * k.dot(f)).normalized()
    n = off - f * off.dot(f) - k * off.dot(k); n.normalize()
    # finger skin samples per bone (dominant weight > 0.5), split into skin and claw
    samp = {}
    for i in range(5):
        for b in chain(s, i):
            col = WT[:, gidx[b]]
            m = col > 0.5
            samp[b] = (CO[m & ~claw_v], CO[m & claw_v])
    def half_thick(i):
        b = chain(s, i)[0]; P = samp[b][0]
        if len(P) == 0: return 0.01
        h0 = np.array(rest(b).translation); h1 = np.array(rest(chain(s, i)[1]).translation)
        d = (h1 - h0) / np.linalg.norm(h1 - h0)
        rel = P - h0; perp = rel - np.outer(rel @ d, d)
        return float(np.median(np.linalg.norm(perp, axis=1)))
    ht = {i: half_thick(i) for i in range(5)}
    prox_len = (rest(chain(s, 2)[1]).translation - kn[2]).length
    hax = (Matrix.Rotation(TILT, 3, n) @ k).normalized()
    # tilt so the butt end (pinky side) moves toward the wrist
    if (Matrix.Rotation(TILT, 3, n) @ (-k)).dot(f) > 0:
        hax = (Matrix.Rotation(-TILT, 3, n) @ k).normalized()
    hc = kmid + f * (prox_len * CEN_F) + n * (R + np.mean([ht[i] for i in (1, 2, 3, 4)]))
    HC, HA = np.array(hc), np.array(hax)

    def radial(P):
        rel = P - HC; perp = rel - np.outer(rel @ HA, HA)
        return np.linalg.norm(perp, axis=1)

    palm_n = np.array(n)
    NEARA = float(os.environ.get('HANDLE_HALF', '0.07'))
    local = {}
    report = {}

    def xform(P, T):
        for pv_, Rm in T:
            P = (P - pv_) @ Rm.T + pv_
        return P

    def score_pts(sk, cl, own):
        rel = sk - HC; al = rel @ HA
        rk = radial(sk) - R
        nearm = np.abs(al) < NEARA
        pen = 0.0
        if nearm.any():
            pen += max(0.0, CLEAR - float(rk[nearm].min())) * 100
        if len(cl):
            rc = radial(cl) - R; alc = (cl - HC) @ HA
            mc = np.abs(alc) < NEARA
            if mc.any():
                pen += max(0.0, 0.002 - float(rc[mc].min())) * 100
            # claws must not dig into the palm (behind the knuckle plane, between wrist and knuckles)
            depth = (cl - np.array(kmid)) @ palm_n
            along = (cl - np.array(wr)) @ np.array(f)
            pen += float(((depth < -0.005) & (along > 0.02) & (along < float((kmid - wr).length))).sum()) * 0.002
        ro = radial(own) - R if len(own) else np.zeros(1)
        return pen + float(np.mean(np.clip(ro - CLEAR, 0, None)))

    for i in (1, 2, 3, 4, 0):
        bones = chain(s, i)
        T = []
        Racc = np.eye(3)
        res = []
        for j, b in enumerate(bones):
            piv = xform(np.array(rest(b).translation)[None], T)[0]
            sk = xform(np.vstack([samp[x][0] for x in bones[j:]] + [np.zeros((0, 3))]), T)
            cl = xform(np.vstack([samp[x][1] for x in bones[j:]] + [np.zeros((0, 3))]), T)
            own = xform(samp[b][0], T) if len(samp[b][0]) else np.zeros((0, 3))
            y = Racc @ np.array(rest(b).to_3x3().col[1])
            if i == 0:
                lat = HA.copy()
            else:
                lat = np.cross(y, palm_n); lat /= np.linalg.norm(lat)
            tipdir = np.cross(lat, y)
            toward = (HC - piv) if i == 0 else palm_n
            if tipdir @ toward < 0:
                lat = -lat
            best = None
            for deg in range(-25 if j == 0 else -5, 111):
                Rm = np.array(Matrix.Rotation(math.radians(deg), 3, Vector(lat)))
                sc_ = score_pts((sk - piv) @ Rm.T + piv, (cl - piv) @ Rm.T + piv, (own - piv) @ Rm.T + piv)
                if best is None or sc_ < best[0] - 1e-9:
                    best = (sc_, deg, Rm)
            _, deg, Rm = best
            T.append((piv, Rm)); Racc = Rm @ Racc
            local[b] = Racc.copy(); res.append((b, deg))
        report[i] = res
    # convert accumulated world rotations to matrix_basis quaternions (parents first)
    fl = {}
    world = {}
    for i in range(5):
        prevW = None
        for j, b in enumerate(chain(s, i)):
            Rb = rest(b).to_3x3()
            Wb = Matrix(local[b].tolist()) @ Rb                   # posed world orientation (hand at rest)
            P = rest(hand).to_3x3() if j == 0 else world[chain(s, i)[j - 1]]
            Pr = rest(rig.data.bones[b].parent.name).to_3x3()
            # matrix_basis = (Pr^-1 Rb)^-1 (P^-1 Wb)
            Bm = (Pr.inverted() @ Rb).inverted() @ (P.inverted() @ Wb)
            fl[b] = list(Bm.to_quaternion()); world[b] = Wb
    Hi = rest(hand).inverted()
    out = {'side': s, 'finger_local': fl, 'R': R, 'handle_centre_hand_local': list(Hi @ hc),
           'handle_axis_hand_local': list((rest(hand).to_3x3().inverted() @ hax).normalized()),
           'rest_centre_world': list(hc), 'rest_axis_world': list(hax), 'palm_normal_world': list(n),
           'half_thickness': ht, 'flex_deg': {str(k): v for k, v in report.items()}}
    json.dump(out, open(os.path.join(HERE, 'work', f'grip_pose_{s}.json'), 'w'), indent=1)
    out_all[s] = out
    print('FIST', s, 'R', R, 'half thickness mm', {k: round(v * 1000, 1) for k, v in ht.items()},
          'flex', {k: [d for _, d in v] for k, v in report.items()})
# apply to the rest pose for a check and save a preview blend
for s in 'LR':
    for b, q in out_all[s]['finger_local'].items():
        pb = rig.pose.bones[b]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion(q)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); m2 = ev.to_mesh()
P = np.array([v.co[:] for v in m2.vertices]); ev.to_mesh_clear()
for s in 'LR':
    o = out_all[s]; HC = np.array(o['rest_centre_world']); HA = np.array(o['rest_axis_world'])
    rel = P - HC; along = rel @ HA; perp = rel - np.outer(along, HA); rad = np.linalg.norm(perp, axis=1)
    near = np.abs(along) < 0.05
    print('FISTCHECK', s, 'verts inside the handle (r < R)', int(((rad < o['R']) & near).sum()), 'min radial mm',
          round(float((rad[near].min() - o['R']) * 1000), 1))
    cy = bpy.data.meshes.new('handle_' + s)
    import bmesh
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=o['R'], radius2=o['R'], depth=0.12)
    bm.to_mesh(cy); bm.free()
    ob = bpy.data.objects.new('Handle_' + s, cy); bpy.context.scene.collection.objects.link(ob)
    z = Vector(HA); Mx = z.to_track_quat('Z', 'Y').to_matrix().to_4x4(); Mx.translation = Vector(HC); ob.matrix_world = Mx
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'fist_preview.blend'))
