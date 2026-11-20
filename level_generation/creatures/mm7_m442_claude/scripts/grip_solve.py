"""G5: solve a right-hand fist around a fixed handle, for OUR fingers (the source's tight curl leaves no room for a
handle inside our thicker fingers; scaling it did not work - TEST_DRIVE.md).
Handle: direction = the grip axis derived from the source curl (circle centres of our posed fingers at the source
grip, `action`/`frame`); position = that line moved along the palm normal until the palm skin clears R_HANDLE.
Fingers (index..pinky): from OUR rest finger pose (relative to the posed hand), each finger curls about one flex axis
(finger direction x palm normal) with three angles found by grid search, so that sample points along each phalanx
sit at R_HANDLE + the finger's measured half-thickness from the handle axis, never inside. The thumb closes over the
handle (one swing across the palm + flex of its two outer joints). Result: per-finger local rotations relative to the
hand in work/grip_pose.json and the handle in hand-local space; applied as a constant pose in every clip by
apply_grip.py. Args: -- <blend> <action> <frame>"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Quaternion, Matrix
blend, action, frame = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R_HANDLE = float(os.environ.get('R_HANDLE', '0.018'))      # goblin hand ~0.21 m at the 1.7 m working scale (bar1 0.012)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
W = rig.matrix_world
lab = np.zeros(len(me.vertices), np.int32); me.attributes['finger'].data.foreach_get('value', lab)
FING = (1, 2, 3, 4)
CH = {i: [f'B_R_Finger{i}', f'B_R_Finger{i}1', f'B_R_Finger{i}2'] for i in FING}
CH[0] = ['B_R_Finger0', 'B_R_Finger0.001', 'B_R_Finger0.002']
FJ = json.load(open(os.path.join(HERE, 'work', 'finger_joints.json')))['R']
rest_co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
# finger half-thickness from the rest mesh: median distance of its skin to its chain
half = {}
for i, ch in CH.items():
    pts = [np.array(rig.data.bones[n].head_local) for n in ch] + [np.array(FJ[ch[-1] + '_tip'])]
    sk = rest_co[(lab == i + 1) & (rest_co[:, 0] < 0)]          # right hand only (labels cover both)
    d = np.min([np.linalg.norm(np.cross(sk - a, (b - a) / np.linalg.norm(b - a)), axis=1) for a, b in zip(pts[:-1], pts[1:])], axis=0)
    half[i] = float(np.median(d))
# posed hand at the grip frame
act = bpy.data.actions[action]; rig.animation_data_create(); rig.animation_data.action = act
if getattr(act, 'slots', None) is not None and len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(frame))
src_pose = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}


def circle(pts):
    cc = pts.mean(0); vt = np.linalg.svd(pts - cc)[2]; e1, e2 = vt[0], vt[1]
    xy = np.stack([(pts - cc) @ e1, (pts - cc) @ e2], 1)
    sol = np.linalg.lstsq(np.column_stack([2 * xy, np.ones(len(xy))]), (xy ** 2).sum(1), rcond=None)[0]
    return cc + sol[0] * e1 + sol[1] * e2


cents = np.array([circle(np.array([tuple(W @ rig.pose.bones[n].head) for n in CH[i]])) for i in FING])
m0 = cents.mean(0)
# handle DIRECTION = the source's own grip axis (grip_from_source.py, source hand-local). Our hand bone rotates exactly
# like the source hand (world copy), so this axis points the blade wherever the animator's sword pointed. (An axis
# from our own posed fingers was 29 deg off and drove the blade into the legs - TEST_DRIVE.md.)
gsrc = json.load(open(os.path.join(HERE, 'work', 'grip_source.json')))
Hp = W @ rig.pose.bones['B_R_Hand'].matrix
A = np.array((Hp.to_3x3().normalized() @ Vector(gsrc['axis_hand'])).normalized())
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'; pb.matrix_basis = src_pose[pb.name]
for ch in CH.values():                                            # fingers back to OUR rest relative to the hand
    for n in ch:
        rig.pose.bones[n].matrix_basis = Matrix()
bpy.context.view_layer.update()
H = W @ rig.pose.bones['B_R_Hand'].matrix
wr = np.array(H.translation)
kn = np.mean([np.array(W @ rig.pose.bones[CH[i][0]].head) for i in FING], axis=0)
fdir = kn - wr; fdir /= np.linalg.norm(fdir)
# natm spear: a diagonal grip - the shaft crosses the palm from the thumb-index web (tip, +axis) to the heel of the
# hand, so the +axis end tilts GRIP_TILT deg toward the fingertips. With the source's square grip (axis across the
# knuckle line) a spear can only point along an extended forearm with a 60-90 deg wrist bend (author_attack.py).
TILT = math.radians(float(os.environ.get('GRIP_TILT', '0')))
if TILT:
    fp = fdir - A * (fdir @ A); fp /= np.linalg.norm(fp)
    A = A * math.cos(TILT) + fp * math.sin(TILT); A /= np.linalg.norm(A)
    print('GRIPTILT deg', round(math.degrees(TILT), 1))
# palm normal: perpendicular to the handle and the finger direction, on the side where the rest fingertips curl
nrm = np.cross(A, fdir); nrm /= np.linalg.norm(nrm)
tips = np.mean([np.array(W @ rig.pose.bones[CH[i][-1]].head) for i in FING], axis=0)
# m442 (user review 2026-10-20, the handle lay outside the fist): the A-pose fingertips lie level with the knuckles
# (dot 0.02), so the rest-tip test picked the BACK of the hand and the fingers bent backwards round the handle; the
# side is now taken from the source fist's own curl centres (dot -1.0 against the old choice), the tips only as fallback
_ref = cents.mean(0) - kn
if abs(_ref @ nrm) > 0.3 * np.linalg.norm(_ref):
    if _ref @ nrm < 0:
        nrm = -nrm
elif (tips - kn) @ nrm < 0:
    nrm = -nrm
print('PALMSIDE source curl centres vs palm normal', round(float((cents.mean(0) - kn) @ nrm / max(np.linalg.norm(cents.mean(0) - kn), 1e-9)), 2),
      'rest tips vs palm normal', round(float((tips - kn) @ nrm / max(np.linalg.norm(tips - kn), 1e-9)), 2))
# the handle sits in front of the palm at the finger bases (the source line through the curl centres is only a
# direction: its curl centres came from the source's over-tight fingers)
C0 = kn + fdir * float(os.environ.get('FIST_C0_FWD', '-0.015'))   # m442: FIST_C0_FWD moves the handle toward the fingers
m0 = C0


def posed():
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(deps); m = ev.to_mesh()
    c = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', c); ev.to_mesh_clear()
    return (np.array(body.matrix_world) @ np.c_[c.reshape(-1, 3), np.ones(len(lab))].T).T[:, :3]


def radial(P, C):
    v = P - C; return np.linalg.norm(v - np.outer(v @ A, A), axis=1), v @ A


# handle against the palm: slide the line along the palm normal until the palm skin (label 0, near) clears it
P = posed()
# m442 (user review 2026-10-20: the handle lay on the cupped fingers): only the right hand's own shell (piece
# HAND_PIECE) counts as palm; the wide sleeve hem hangs round the hand and pushed the handle 37 mm off the palm
_pc = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', _pc)
palm = (lab == 0) & (np.linalg.norm(P - kn, axis=1) < 0.06) & (rest_co[:, 0] < 0) & (_pc == int(os.environ.get('HAND_PIECE', '2')))
C = m0.copy()
for step in range(80):
    r, al = radial(P[palm], C)
    near = np.abs(al) < 0.04
    if not near.any() or r[near].min() >= R_HANDLE:
        break
    C = C + nrm * 0.001
print('HANDLE moved off the palm by', step, 'mm; finger half-thickness cm', {i: round(v * 100, 2) for i, v in half.items()})


def joints(i):
    pts = [np.array(W @ rig.pose.bones[n].head) for n in CH[i]]
    tail = np.array(W @ rig.pose.bones[CH[i][-1]].matrix @ rig.pose.bones[CH[i][-1]].bone.matrix_local.inverted() @ Vector(FJ[CH[i][-1] + '_tip']))
    return pts + [tail]


def fk(js, ax, angs):
    p = [j.copy() for j in js]
    for k, a in enumerate(angs):
        R = np.array(Matrix.Rotation(a, 3, Vector(ax)))
        for m in range(k + 1, len(p)):
            p[m] = p[k] + R @ (p[m] - p[k])
    return p


def cost(p, want, pull_from=0):
    """Sample points on each segment: inside the handle (r < want) is penalised everywhere; the pull toward r = want
    applies from segment pull_from on. m442 (user review 2026-10-20, the handle lay on the cupped fingers): the goblin
    knuckles sit ~4 cm from the handle axis (thick palm), so pulling the proximal phalanx onto the handle too laid the
    fingers along one side; with FIST_PULL_FROM=1 only the middle and distal phalanges wrap onto the handle."""
    c = 0.0
    for k, (a, b) in enumerate(zip(p[:-1], p[1:])):
        for t in (0.2, 0.5, 0.8, 1.0):
            q = a + (b - a) * t
            v = q - C; r = np.linalg.norm(v - A * (v @ A))
            c += ((r - want) ** 2 if k >= pull_from else 0.0) + (400 * (want - r) ** 2 if r < want - 0.001 else 0.0)
    return c


def turn(n, ax, ang):
    pb = rig.pose.bones[n]; bpy.context.view_layer.update()
    m = W @ pb.matrix; h = m.translation.copy()
    pb.matrix = W.inverted() @ (Matrix.Translation(h) @ Matrix.Rotation(ang, 4, Vector(ax)) @ Matrix.Translation(-h) @ m)
    bpy.context.view_layer.update()


grid = np.radians(np.arange(0, 121, 5))
report = {}
spread = {}
# m442: the independent spread closes alternated +38/-33 deg between neighbours and tore the webs (6.4x); each finger
# takes the fingers' mean spread plus at most SPREAD_DEV of its own
SPREAD_DEV = math.radians(float(os.environ.get('SPREAD_DEV', '10')))
_best = {}
for i in FING:
    js = joints(i); d = js[1] - js[0]
    _best[i] = min(np.radians(np.arange(-60, 61, 1)),
                   key=lambda a: (round(abs((np.array(Matrix.Rotation(a, 3, Vector(nrm))) @ d) @ A) / np.linalg.norm(d), 2), abs(a)))
_mean = float(np.mean(list(_best.values())))
for i in FING:
    js = joints(i)
    # goblin: the fingers are splayed 25-70 deg away from the handle's normal plane; flexing them about the handle
    # axis sweeps a cone past it. First close the spread at the knuckle (rotation about the palm normal) until the
    # proximal phalanx is perpendicular to the handle, then curl.
    d = js[1] - js[0]
    best_sp = _mean + float(np.clip(_best[i] - _mean, -SPREAD_DEV, SPREAD_DEV))
    turn(CH[i][0], nrm, best_sp); spread[i] = round(math.degrees(best_sp))
    js = joints(i)
    d = js[1] - js[0]; ax = A.copy()                  # every finger flexes about the handle axis (fist)
    if (np.array(Matrix.Rotation(0.3, 3, Vector(ax))) @ d) @ nrm < d @ nrm:
        ax = -ax
    want = R_HANDLE + half[i] + 0.002                    # 2 mm margin: skin, not the bone line, must clear
    best = (1e9, None)
    for a1 in grid:
        for a2 in grid:
            for a3 in grid[::2]:
                if a3 > a2 + 1e-6:
                    continue                              # anatomy: the fingertip joint bends no more than the middle one
                c = cost(fk(js, ax, (a1, a2, a3)), want, int(os.environ.get('FIST_PULL_FROM', '1')))
                if c < best[0]:
                    best = (c, (a1, a2, a3))
    for k, n in enumerate(CH[i]):
        turn(n, ax, best[1][k])
    report[i] = [round(math.degrees(x)) for x in best[1]]
# thumb: swing about the finger direction toward the handle, then flex the two outer joints. m442 (user review
# 2026-10-20): a second swing about the palm normal (SN, toward/away from the fingers) lets the goblin thumb, which sits
# far round the palm, close over the handle; the middle and distal segments are pulled onto it
# m442: the short goblin thumb (4.2 cm chain, rooted 8.4 cm from the handle axis) cannot reach the handle; as in a
# real hammer grip it closes over the index finger's middle phalanx instead (THUMB_TARGET=index; 'handle' = old rule)
_ij = joints(1)
_im = [_ij[1] + (_ij[2] - _ij[1]) * t for t in (0.25, 0.5, 0.75)] + [_ij[2] + (_ij[3] - _ij[2]) * 0.3]


def thumb_cost(p):
    if os.environ.get('THUMB_TARGET', 'index') == 'handle':
        return cost(p[1:], R_HANDLE + half[0] + 0.002)
    want_t = half[0] + half[1] + 0.003
    c = 0.0
    for a, b in zip(p[1:-1], p[2:]):
        for t in (0.3, 0.6, 1.0):
            q = a + (b - a) * t
            d = min(np.linalg.norm(q - m) for m in _im)
            c += (d - want_t) ** 2 * (2.0 if t == 1.0 else 1.0)
            v = q - C; r = np.linalg.norm(v - A * (v @ A))
            if r < R_HANDLE + half[0]:
                c += 400 * (R_HANDLE + half[0] - r) ** 2
    return c


js = joints(0)
_v = js[0] - C; _rb = np.linalg.norm(_v - A * (_v @ A)); _L = sum(np.linalg.norm(js[k + 1] - js[k]) for k in range(len(js) - 1))
print('THUMB base-to-axis cm', round(_rb * 100, 2), 'chain length cm', round(_L * 100, 2), 'want cm', round((R_HANDLE + half[0] + 0.002) * 100, 2),
      'along axis cm', round(float(_v @ A) * 100, 2))
best = (1e9, None)
for sn in np.radians(np.arange(-60, 61, 15)):
    Rn = np.array(Matrix.Rotation(sn, 3, Vector(nrm)))
    jn = [js[0]] + [js[0] + Rn @ (x - js[0]) for x in js[1:]]
    for sw in np.radians(np.arange(-180, 181, 15)):
        Rs = np.array(Matrix.Rotation(sw, 3, Vector(fdir)))
        pj = [jn[0]] + [jn[0] + Rs @ (x - jn[0]) for x in jn[1:]]
        d = pj[1] - pj[0]; ax = np.cross(d, nrm); ax /= max(np.linalg.norm(ax), 1e-9)
        for a1 in np.radians(np.arange(-60, 101, 20)):
            for a2 in np.radians(np.arange(-30, 91, 15)):
                for a3 in np.radians(np.arange(0, 81, 20)):
                    p = fk(pj, ax, (a1, a2, a3))
                    c = thumb_cost(p)
                    if c < best[0]:
                        best = (c, (sn, sw, ax, a1, a2, a3))
sn, sw, tax, a1, a2, a3 = best[1]
turn(CH[0][0], nrm, sn); turn(CH[0][0], fdir, sw); turn(CH[0][0], tax, a1); turn(CH[0][1], tax, a2); turn(CH[0][2], tax, a3)
report[0] = [round(math.degrees(sn)), round(math.degrees(sw)), round(math.degrees(a1)), round(math.degrees(a2)), round(math.degrees(a3))]
_tj = joints(0)
print('THUMBFIT tip to index middle phalanx cm', round(min(np.linalg.norm(_tj[-1] - m) for m in _im) * 100, 2), 'want', round((half[0] + half[1] + 0.003) * 100, 2))
P = posed()
clear = {}
for i in range(5):
    m = (lab == i + 1) & (rest_co[:, 0] < 0)
    r, al = radial(P[m], C); nr = np.abs(al) < 0.05
    clear[i] = round(float(r[nr].min()) * 100, 2) if nr.any() else None
r, al = radial(P[palm], C)
print('GRIPSOLVE spread deg', spread, 'curl deg', report, '| skin clearance cm (handle radius', R_HANDLE * 100, ')', clear,
      'palm', round(float(r[np.abs(al) < 0.04].min()) * 100, 2))
inv = (W @ rig.pose.bones['B_R_Hand'].matrix).inverted()
FL = {n: list(rig.pose.bones[n].rotation_quaternion) for ch in CH.values() for n in ch}
json.dump({'finger_local': FL,
           'handle_centre_hand_local': list(inv @ Vector(C)), 'handle_axis_hand_local': list((inv.to_3x3() @ Vector(A)).normalized()),
           'radius': R_HANDLE, 'curl_deg': report, 'clearance_cm': clear},
          open(os.path.join(HERE, 'work', 'grip_pose.json'), 'w'), indent=1)
# ---------------------------------------------------------------- review renders (posed hand cut + handle)
if os.environ.get('GRIP_RENDER'):
    import bmesh
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import common
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); bm2 = bmesh.new(); bm2.from_mesh(ev.to_mesh()); ev.to_mesh_clear()
    bm2.transform(body.matrix_world)
    bmesh.ops.delete(bm2, geom=[x for x in bm2.verts if (x.co - Vector(C)).length > 0.12], context='VERTS')
    mc = bpy.data.meshes.new('posed'); bm2.to_mesh(mc); bm2.free()
    o = bpy.data.objects.new('posedhand', mc); bpy.context.scene.collection.objects.link(o)
    for x in bpy.data.objects:
        if x.type == 'MESH' and x is not o:
            x.hide_render = True
    hb = bmesh.new(); bmesh.ops.create_cone(hb, cap_ends=True, segments=16, radius1=R_HANDLE, radius2=R_HANDLE, depth=0.16)
    hm_ = bpy.data.meshes.new('h'); hb.to_mesh(hm_); hb.free()
    ho = bpy.data.objects.new('handle', hm_); bpy.context.scene.collection.objects.link(ho)
    ho.location = Vector(C); ho.rotation_mode = 'QUATERNION'; ho.rotation_quaternion = Vector(A).to_track_quat('Z', 'Y')
    mat = bpy.data.materials.new('hm'); mat.diffuse_color = (0.75, 0.45, 0.2, 1); hm_.materials.append(mat)
    scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
    out = os.environ['GRIP_RENDER']
    # cameras in the hand's own frame: down the handle, from the palm side, from the back, from the finger side
    for vname, d in (('axis', A), ('palm', nrm), ('back', -nrm), ('side', np.cross(A, nrm)), ('tips', -fdir)):
        d = Vector(d).normalized(); up = Vector(fdir) if abs(Vector(fdir) @ d) < 0.9 else Vector(A)
        cam = common.ortho_camera('c_' + vname, Vector(C) + d * 1.0, (0, 0, 0), float(os.environ.get('GRIP_SCALE', '0.24')))
        cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = (-d).to_track_quat('-Z', 'Y')
        scene.camera = cam; scene.render.resolution_x = scene.render.resolution_y = 360
        scene.render.filepath = f'{out}_{vname}.png'; bpy.ops.render.render(write_still=True)
