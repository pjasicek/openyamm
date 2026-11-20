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
R_HANDLE = 0.012
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
W = rig.matrix_world
lab = np.zeros(len(me.vertices), np.int32); me.attributes['finger'].data.foreach_get('value', lab)
CH = {i: [f'B_L_Finger{i}', f'B_L_Finger{i}1', f'B_L_Finger{i}2'] for i in (1, 2, 3, 4)}
CH[0] = ['B_L_Finger0', 'B_L_Finger01', 'B_L_Finger02']
FJ = json.load(open(os.path.join(HERE, 'work', 'finger_joints.json')) )['L']
rest_co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
# finger half-thickness from the rest mesh: median distance of its skin to its chain
half = {}
for i, ch in CH.items():
    pts = [np.array(rig.data.bones[n].head_local) for n in ch] + [np.array(FJ[ch[-1] + '_tip'])]
    sk = rest_co[(lab == i + 1) & (rest_co[:, 0] > 0)]          # right hand only (labels cover both)
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


cents = np.array([circle(np.array([tuple(W @ rig.pose.bones[n].head) for n in CH[i]])) for i in (1, 2, 3, 4)])
m0 = cents.mean(0)
# handle DIRECTION = the source's own grip axis (grip_from_source.py, source hand-local). Our hand bone rotates exactly
# like the source hand (world copy), so this axis points the blade wherever the animator's sword pointed. (An axis
# from our own posed fingers was 29 deg off and drove the blade into the legs - TEST_DRIVE.md.)
hm0=rig.data.bones['B_L_Hand'].matrix_local
gsrc={'axis_hand':list(hm0.to_3x3().inverted()@(rig.data.bones['B_L_Finger1'].head_local-rig.data.bones['B_L_Finger4'].head_local).normalized())}
Hp = W @ rig.pose.bones['B_L_Hand'].matrix
A = np.array((Hp.to_3x3().normalized() @ Vector(gsrc['axis_hand'])).normalized())
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'; pb.matrix_basis = src_pose[pb.name]
for ch in CH.values():                                            # fingers back to OUR rest relative to the hand
    for n in ch:
        rig.pose.bones[n].matrix_basis = Matrix()
bpy.context.view_layer.update()
H = W @ rig.pose.bones['B_L_Hand'].matrix
wr = np.array(H.translation)
kn = np.mean([np.array(W @ rig.pose.bones[CH[i][0]].head) for i in (1, 2, 3, 4)], axis=0)
fdir = kn - wr; fdir /= np.linalg.norm(fdir)
# palm normal: perpendicular to the handle and the finger direction, on the side where the rest fingertips curl
nrm = np.cross(A, fdir); nrm /= np.linalg.norm(nrm)
tips = np.mean([np.array(W @ rig.pose.bones[CH[i][-1]].head) for i in (1, 2, 3, 4)], axis=0)
if (tips - kn) @ nrm < 0:
    nrm = -nrm
# the handle sits in front of the palm at the finger bases (the source line through the curl centres is only a
# direction: its curl centres came from the source's over-tight fingers)
C0 = kn - fdir * 0.015
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
palm = (lab == 0) & (np.linalg.norm(P - kn, axis=1) < 0.06) & (rest_co[:, 0] > 0)
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


def cost(p, want):
    c = 0.0
    for a, b in zip(p[:-1], p[1:]):
        for t in (0.2, 0.5, 0.8, 1.0):
            q = a + (b - a) * t
            v = q - C; r = np.linalg.norm(v - A * (v @ A))
            c += (r - want) ** 2 + (400 * (want - r) ** 2 if r < want - 0.001 else 0.0)
    return c


def turn(n, ax, ang):
    pb = rig.pose.bones[n]; bpy.context.view_layer.update()
    m = W @ pb.matrix; h = m.translation.copy()
    pb.matrix = W.inverted() @ (Matrix.Translation(h) @ Matrix.Rotation(ang, 4, Vector(ax)) @ Matrix.Translation(-h) @ m)
    bpy.context.view_layer.update()


grid = np.radians(np.arange(0, 111, 5))
report = {}
for i in (1, 2, 3, 4):
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
                c = cost(fk(js, ax, (a1, a2, a3)), want)
                if c < best[0]:
                    best = (c, (a1, a2, a3))
    for k, n in enumerate(CH[i]):
        turn(n, ax, best[1][k])
    report[i] = [round(math.degrees(x)) for x in best[1]]
# thumb: swing about the finger direction toward the handle, then flex the two outer joints
js = joints(0)
best = (1e9, None)
for sw in np.radians(np.arange(-50, 61, 5)):
    Rs = np.array(Matrix.Rotation(sw, 3, Vector(fdir)))
    pj = [js[0]] + [js[0] + Rs @ (x - js[0]) for x in js[1:]]
    d = pj[1] - pj[0]; ax = np.cross(d, nrm); ax /= max(np.linalg.norm(ax), 1e-9)
    for a2 in np.radians(np.arange(0, 81, 5)):
        for a3 in np.radians(np.arange(0, 81, 10)):
            p = fk(pj, ax, (0.0, a2, a3))
            c = cost(p[1:], R_HANDLE + half[0] + 0.002)
            if c < best[0]:
                best = (c, (sw, ax, a2, a3))
sw, tax, a2, a3 = best[1]
turn(CH[0][0], fdir, sw); turn(CH[0][1], tax, a2); turn(CH[0][2], tax, a3)
report[0] = [round(math.degrees(sw)), round(math.degrees(a2)), round(math.degrees(a3))]
P = posed()
clear = {}
for i in range(5):
    m = (lab == i + 1) & (rest_co[:, 0] > 0)
    r, al = radial(P[m], C); nr = np.abs(al) < 0.05
    clear[i] = round(float(r[nr].min()) * 100, 2) if nr.any() else None
r, al = radial(P[palm], C)
print('GRIPSOLVE curl deg', report, '| skin clearance cm (handle radius', R_HANDLE * 100, ')', clear,
      'palm', round(float(r[np.abs(al) < 0.04].min()) * 100, 2))
inv = (W @ rig.pose.bones['B_L_Hand'].matrix).inverted()
json.dump({'finger_local': {n: list(rig.pose.bones[n].rotation_quaternion) for ch in CH.values() for n in ch},
           'handle_centre_hand_local': list(inv @ Vector(C)), 'handle_axis_hand_local': list((inv.to_3x3() @ Vector(A)).normalized()),
           'radius': R_HANDLE, 'curl_deg': report, 'clearance_cm': clear},
          open(os.path.join(HERE, 'work', 'shield_grip.json'), 'w'), indent=1)
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
    for vname in ('front', 'left', 'back', 'right'):
        common.render_views(f'{out}_{vname}', C[2], 0.2, views=(vname,), resolution=(360, 360), target=(C[0], C[1]))
