"""hkr G5 (second route): a uniform power-grip curl of the demon's fingers, then the handle tunnel measured on the
curled mesh. Fingers 1-4 flex each joint about the finger's own lateral axis (bone Y x palm normal; the palm normal =
the side the demon's claws already curl toward) by CURL = 'a,b,c' degrees (pinky side + SPREAD per finger); the
thumb (Finger0) turns about the hand axis toward the palm by THUMB_SWING and flexes its outer joints by THUMB_FLEX.
The tunnel: as grip_from_fist.py (enclosure of 16 sectors, clearance), on the posed hand vertices, candidate axes
within 25 deg of the knuckle line. Writes work/grip_pose_<S>.json (finger_local quaternions, handle centre/axis in
B_<S>_Hand rest-local space = the posed hand at rest) and saves work/curl_preview.blend with handle cylinders.
Args: -- <blend>"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURL = [float(x) for x in os.environ.get('CURL', '45,75,45').split(',')]
# the supporting left hand may hold the handguard diagonally across the fingers (a straight wrist under a level gun):
# its own curl, the tunnel axis allowed AXIS_DEV_L deg off the knuckle line, preferring the one nearest the hand axis
CURL_S = {'L': [float(x) for x in os.environ.get('CURL_L', os.environ.get('CURL', '45,75,45')).split(',')], 'R': CURL}
AXIS_DEV = {'L': float(os.environ.get('AXIS_DEV_L', '25')), 'R': 25.0}
MIN_CLEAR = float(os.environ.get('MIN_CLEAR_L', '0.0'))
SPREAD = float(os.environ.get('SPREAD', '4'))
TSW, TFL = float(os.environ.get('THUMB_SWING', '35')), [float(x) for x in os.environ.get('THUMB_FLEX', '10,35,35').split(',')]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity(); pb.rotation_mode = 'QUATERNION'
bpy.context.view_layer.update()
rest = lambda n: rig.data.bones[n].matrix_local.copy()
def chain(s, i):
    if s == 'R' and i == 0:
        return ['B_R_Finger0', 'B_R_Finger0.001', 'B_R_Finger0.002']
    return [f'B_{s}_Finger{i}', f'B_{s}_Finger{i}1', f'B_{s}_Finger{i}2']
out = {}
for s in 'LR':
    hand = f'B_{s}_Hand'; wr = rest(hand).translation
    kn = {i: rest(chain(s, i)[0]).translation for i in range(5)}
    tips = {i: rig.data.bones[chain(s, i)[2]].tail_local for i in range(5)}
    f = (kn[2] - wr).normalized(); kmid = (kn[1] + kn[2] + kn[3] + kn[4]) / 4
    off = sum(((tips[i] - kmid) - f * (tips[i] - kmid).dot(f) for i in (1, 2, 3, 4)), Vector())
    k = kn[1] - kn[4]; k = (k - f * k.dot(f)).normalized()
    n = off - f * off.dot(f) - k * off.dot(k); n.normalize()
    world = {}
    for i in range(5):
        Wacc = Matrix.Identity(3)
        for j, b in enumerate(chain(s, i)):
            y = Wacc @ rest(b).to_3x3().col[1]
            if i == 0:
                if j == 0:
                    ax = f.copy(); ang = TSW
                    if (Matrix.Rotation(math.radians(ang), 3, ax) @ y - y).dot(n) < 0: ax = -ax
                    Rm = Matrix.Rotation(math.radians(ang), 3, ax)
                    lat = y.cross(n).normalized()
                    if lat.cross(y).dot(n) < 0: lat = -lat
                    Rm = Matrix.Rotation(math.radians(TFL[0]), 3, lat) @ Rm
                else:
                    lat = y.cross(n).normalized()
                    if lat.cross(y).dot(n) < 0: lat = -lat
                    Rm = Matrix.Rotation(math.radians(TFL[j]), 3, lat)
            else:
                lat = y.cross(n).normalized()
                if lat.cross(y).dot(n) < 0: lat = -lat
                Rm = Matrix.Rotation(math.radians(CURL_S[s][j] + SPREAD * (i - 2)), 3, lat)
            Wacc = Rm @ Wacc; world[b] = Wacc @ rest(b).to_3x3()
    fl = {}
    for i in range(5):
        for j, b in enumerate(chain(s, i)):
            Rb = rest(b).to_3x3(); Pr = rest(rig.data.bones[b].parent.name).to_3x3()
            P = Pr if j == 0 else world[chain(s, i)[j - 1]]
            Bm = (Pr.inverted() @ Rb).inverted() @ (P.inverted() @ world[b])
            fl[b] = list(Bm.to_quaternion())
            rig.pose.bones[b].rotation_quaternion = Bm.to_quaternion()
    out[s] = {'finger_local': fl, 'f': list(f), 'n': list(n), 'k': list(k), 'kmid': list(kmid), 'wr': list(wr)}
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); m2 = ev.to_mesh()
P = np.array([v.co[:] for v in m2.vertices]); ev.to_mesh_clear()
gidx = {g.name: g.index for g in body.vertex_groups}
WT = np.zeros((len(P), len(gidx)), np.float32)
for v in me.vertices:
    for g in v.groups: WT[v.index, g.group] = g.weight
import bmesh
for s in 'LR':
    o = out[s]; f, n, k, kmid, wr = (np.array(o[x]) for x in ('f', 'n', 'k', 'kmid', 'wr'))
    hb = [gidx[b] for b in gidx if b.startswith(f'B_{s}_Finger') or b == f'B_{s}_Hand']
    hv = P[WT[:, hb].sum(1) > 0.5]
    best = None
    c0 = kmid + n * 0.03 + f * 0.02
    rng = np.random.default_rng(1)
    for t in range(3000 if AXIS_DEV[s] <= 25 else 12000):
        d = k + rng.normal(size=3) * (0.25 if AXIS_DEV[s] <= 25 else 0.9); d /= np.linalg.norm(d)
        if math.degrees(math.acos(min(1, abs(d @ k)))) > AXIS_DEV[s]: continue
        c = c0 + rng.uniform(-0.035, 0.035, 3)
        u = np.cross(d, f); u /= np.linalg.norm(u); w = np.cross(d, u)
        rel = hv - c; al = rel @ d; sl = rel[np.abs(al) < 0.035]
        if len(sl) < 20: continue
        perp = sl - np.outer(sl @ d, d); dist = np.linalg.norm(perp, axis=1)
        near = dist < 0.07
        if near.sum() < 10: continue
        ang = np.arctan2(perp[near] @ w, perp[near] @ u)
        enc = len(set(((ang + math.pi) / (2 * math.pi) * 16).astype(int) % 16)) / 16
        clear = float(dist.min())
        if s == 'L' and AXIS_DEV['L'] > 25:
            # enclosed and clear enough, then as near the hand axis as possible
            score = (round(enc * 8) / 8 >= 0.875, clear >= MIN_CLEAR, -math.degrees(math.acos(min(1, abs(float(d @ f))))), clear)
        else:
            score = (round(enc, 2), clear)
        if best is None or score > best[0]: best = (score, d, c, enc, clear)
    _, d, c, enc, clear = best
    if d @ k < 0: d = -d                               # toward the thumb (index side)
    H = rest(f'B_{s}_Hand'); Hi = H.inverted()
    o.update({'side': s, 'handle_centre_hand_local': list(Hi @ Vector(c)), 'handle_axis_hand_local': list((H.to_3x3().inverted() @ Vector(d)).normalized()),
              'rest_centre_world': list(c), 'rest_axis_world': list(d), 'enclosure': enc, 'clearance_m': clear,
              'curl_deg': CURL, 'spread_deg': SPREAD, 'thumb_swing_deg': TSW, 'thumb_flex_deg': TFL})
    json.dump(o, open(os.path.join(HERE, 'work', f'grip_pose_{s}.json'), 'w'), indent=1)
    print('CURL', s, 'enclosure', enc, 'clearance mm', round(clear * 1000, 1), 'axis to knuckle line deg',
          round(math.degrees(math.acos(min(1, abs(float(d @ k))))), 1), 'axis to hand deg', round(math.degrees(math.acos(abs(float(d @ f)))), 1))
    cy = bpy.data.meshes.new('handle_' + s); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=clear, radius2=clear, depth=0.14); bm.to_mesh(cy); bm.free()
    ob = bpy.data.objects.new('Handle_' + s, cy); bpy.context.scene.collection.objects.link(ob)
    Mx = Vector(d).to_track_quat('Z', 'Y').to_matrix().to_4x4(); Mx.translation = Vector(c); ob.matrix_world = Mx
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'curl_preview.blend'))
