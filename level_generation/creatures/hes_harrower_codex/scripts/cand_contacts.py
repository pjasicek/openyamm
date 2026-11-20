"""Last armour contacts of the picked attacks (after cand_polish.py, before cand_finish.py). The global passes left a few
plate contacts on single frames (the cross cut's right arm through the chest plate, the belt in the leading thigh,
a pauldron in the head, the back plates of a deep arch). Per clip and frame this measures the plates exactly as
armour_gate.py does (same candidates, rest baselines, signed nearest face with ray parity) and, where one is deeper
than TOL, applies the smallest pose change of the remedy that owns the contact, re-measured on the posed mesh:
- an arm or its clavicle against a torso plate (arm skin in the plate, or the plate in the arm): the upper arm's
  rotation relative to the chest blends toward Standing frame 0's by the smallest weight (5 .. 60 %) that clears (fixed
  turns about the chest axes flipped direction from frame to frame in a cross-body follow-through);
- the belt or a torso plate in a thigh: the thigh turns out about the pelvis's forward axis, the foot keeps its world
  rotation;
- a pauldron or the chest plate in the head, jaw or neck: the head rolls about the chest's forward axis and pitches
  about its lateral axis (either way, the smallest that clears);
- back plates against each other or the back skin: B_Spine1 bends about its lateral axis while B_Spine2 keeps its
  world rotation (the arch moves to the lower joint).
A change is accepted only if it also leaves every other contact on the related plates no deeper than before (turning
an arm out about the forward axis alone pressed the chest plate into the clavicle skin). The per-frame needs are Gaussian-smoothed (never below a frame's own need) and keyed; the pass repeats on what is left.
Args: -- <in blend> <out blend> <spec json>   (env TOL 0.0025, PASSES 3)"""
from pathlib import Path
import sys, os, json, math
import bpy, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P / 'scripts')); import armik
src, out, specp = sys.argv[sys.argv.index('--') + 1:][:3]
TOL, PASSES = float(os.environ.get('TOL', '0.0025')), int(os.environ.get('PASSES', '3'))
PRE = 0.08
bpy.ops.wm.open_mainfile(filepath=str(Path(src).resolve()))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; sc = bpy.context.scene
SPECJ = json.loads(Path(specp).read_text()); SPEC = {p['name']: p for p in SPECJ['plates']}; ATLAS = SPECJ.get('atlas', 1024)
plates = sorted([o for o in bpy.data.objects if o.name.startswith(('Arm_', 'Cuff_'))], key=lambda o: o.name)
me = body.data; nv = len(me.vertices)
PIECE = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', PIECE)
GI = {g.index: g.name for g in body.vertex_groups}
DOM = np.array([GI[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in me.vertices])
BF = [tuple(p.vertices) for p in me.polygons]
HID = np.zeros(nv, np.int32)
if 'shell_hidden' in me.attributes: me.attributes['shell_hidden'].data.foreach_get('value', HID)
HIDF = {k for k, f in enumerate(BF) if all(HID[i] for i in f)}
KEEPF = [k for k, f in enumerate(BF) if not (k in HIDF and PIECE[f[0]] != 0)]
BFK = [BF[k] for k in KEEPF]
HIDFK = {j for j, k in enumerate(KEEPF) if k in HIDF}
DIRS = [Vector(d).normalized() for d in ((0.0123, 0.0217, 1.0), (0.71, -0.33, -0.62), (-0.55, 0.81, 0.2),
                                         (0.12, -0.97, 0.21), (-0.83, -0.18, -0.52))]


# the measures of armour_gate.py
def ev(ob):
    e = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); e.to_mesh_clear()
    return co.reshape(-1, 3) @ np.array(ob.matrix_world.to_3x3()).T + np.array(ob.matrix_world.translation)


def parity(tree, p, maxd=1.0):
    votes = 0
    for d in DIRS:
        o = Vector(p); n = 0; travelled = 0.0
        while travelled < maxd:
            loc, nrm, fi, dist = tree.ray_cast(o, d, maxd - travelled)
            if loc is None: break
            n += 1; travelled += dist + 1e-5; o = loc + d * 1e-5
        votes += n % 2
    return votes * 2 > len(DIRS)


def inside_closed(tree, pts, maxd=0.5, skipf=()):
    best, arg = 0.0, -1
    for k, p in enumerate(pts):
        loc, n, fi, d = tree.find_nearest(Vector(p), 0.06)
        if loc is None or d <= best or fi in skipf: continue
        if (Vector(p) - loc).dot(n) < 0 and parity(tree, p, maxd): best, arg = d, k
    return best, arg


def through_depth(tree, pts):
    best, arg = 0.0, -1
    for k, p in enumerate(pts):
        loc, n, fi, d = tree.find_nearest(Vector(p), 0.03)
        if loc is None or d <= best: continue
        v = Vector(p) - loc
        if v.dot(n) < -0.9 * v.length: best, arg = d, k
    return best, arg


rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
B0 = ev(body)
cand, pfaces, ifaces, PV = {}, {}, {}, {}
for pl in plates:
    P0 = ev(pl); F = [tuple(p.vertices) for p in pl.data.polygons if p.material_index == 0]; pfaces[pl.name] = F
    uvd = pl.data.uv_layers[0].data; DK = (1 - 12 / ATLAS)
    ifaces[pl.name] = [tuple(p.vertices) for p in pl.data.polygons if p.material_index == 0 and
                       all(abs(uvd[li].uv[0] - DK) < 1e-3 for li in p.loop_indices)]
    PV[pl.name] = np.array(sorted({k for f in F for k in f}), int)
    t = BVHTree.FromPolygons(P0.tolist(), F)
    spec = SPEC.get(pl.name[4:], {}); xb, xp = set(spec.get('exclude_bones', [])), set(spec.get('exclude_pieces', []))
    ok = ~(np.isin(DOM, list(xb)) | np.isin(PIECE, list(xp))) & (HID == 0)
    for b_ in [b for b in xb if b.startswith('Bone_') and b in body.vertex_groups]:
        gi_ = body.vertex_groups[b_].index
        ok &= np.array([not any(g.group == gi_ and g.weight > 0.05 for g in v.groups) for v in me.vertices])
    cand[pl.name] = np.array([i for i in np.nonzero(ok)[0] if t.find_nearest(Vector(B0[i]), PRE)[0] is not None], int)
BONE = {pl.name: pl.get('bone', pl.vertex_groups[0].name) for pl in plates}
TORSO_BONES = {'B_Spine2', 'B_Spine1', 'B_Spine', 'B_Pelvis', 'B_Groin', 'B_L_Thigh', 'B_R_Thigh', 'B_L_Calf', 'B_R_Calf'}
ARMV = np.nonzero(np.array([any(t in d for t in ('UpperArm', 'Forearm', 'Hand', 'Finger')) for d in DOM]) & (HID == 0))[0]
OVERLAY = [{f'B_{s}_{x}', f'B_{s}_{y}'} for s in 'LR' for x, y in (('Pauldron', 'Carapace'), ('Pauldron', 'Spikes'), ('Carapace', 'Spikes'))]
FULLB = BVHTree.FromPolygons(B0.tolist(), BFK)
BASE_PLATE = {}
for pl in plates:
    P0 = ev(pl); t = BVHTree.FromPolygons(P0.tolist(), pfaces[pl.name]); ti = BVHTree.FromPolygons(P0.tolist(), ifaces[pl.name])
    cand[pl.name] = np.array([i for i in cand[pl.name] if not parity(t, B0[i], 0.5) and through_depth(ti, B0[i:i + 1])[0] == 0], int)
    BASE_PLATE[pl.name] = np.array([k for k in PV[pl.name] if not parity(FULLB, P0[k], 0.8)], int)
NAMES = [pl.name for pl in plates]


def side_of(part):
    return part[2] if part and part.startswith(('B_L_', 'B_R_')) else None


def measure(only=None):
    """[(depth, plate, kind, part)] deeper than TOL on the current pose; part = the body bone or plate it is in"""
    B = ev(body); BL = B.tolist(); PL = {n: ev(bpy.data.objects[n]) for n in NAMES}
    PT = {n: BVHTree.FromPolygons(PL[n].tolist(), pfaces[n]) for n in NAMES}
    btree = BVHTree.FromPolygons(BL, BFK); out = []
    for n in (only or NAMES):
        ti = BVHTree.FromPolygons(PL[n].tolist(), ifaces[n])
        if len(cand[n]):
            d1, k1 = through_depth(ti, B[cand[n]]); d1b, k1b = inside_closed(PT[n], B[cand[n]])
            if d1b > d1: d1, k1 = d1b, k1b
            if d1 > TOL: out.append((d1, n, 'skin_in_plate', DOM[cand[n][k1]]))
        d2, k2 = inside_closed(btree, PL[n][BASE_PLATE[n]], 1.2, HIDFK)
        if d2 > TOL:
            fi2 = btree.find_nearest(Vector(PL[n][BASE_PLATE[n]][k2]))[2]; out.append((d2, n, 'plate_in_skin', DOM[BFK[fi2][0]]))
        for m in NAMES:
            if m == n or BONE[m] == BONE[n] or {BONE[m], BONE[n]} in OVERLAY: continue
            d3, _ = inside_closed(PT[m], PL[n][PV[n]])
            if d3 > TOL: out.append((d3, n, 'plate_in_plate', m))
        if BONE[n] in TORSO_BONES:
            lo_, hi_ = PL[n].min(0) - 0.01, PL[n].max(0) + 0.01
            near = ARMV[np.all((B[ARMV] > lo_) & (B[ARMV] < hi_), axis=1)]
            if len(near):
                d5, k5 = inside_closed(PT[n], B[near])
                if d5 > TOL: out.append((d5, n, 'arm_in_plate', DOM[near[k5]]))
    return out


HEAD_PARTS = ('B_Head', 'B_Neck', 'Bone_025', 'headfront')   # Bone_025: the jaw


def remedy_of(c):
    d, n, kind, part = c
    if n.startswith('Arm_spine_') and (kind == 'plate_in_plate' or (kind == 'skin_in_plate' and part.startswith('B_Spine'))):
        return 'spine'
    if (n.startswith('Arm_pauldron_') or n == 'Arm_chest') and part in HEAD_PARTS:
        return 'head'
    s = side_of(part)
    if s and any(x in part for x in ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger')) and BONE[n] in TORSO_BONES:
        return 'arm_' + s
    if s and ('Thigh' in part or 'Calf' in part) and BONE[n] in ('B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2'):
        return 'thigh_' + s
    return None


CHEST_FWD = rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))
CHEST_LAT = rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted() @ Vector((1, 0, 0))
CHEST_UP = rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted() @ Vector((0, 0, 1))
PELV_FWD = rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))
S1_LAT = rig.data.bones['B_Spine1'].matrix_local.to_3x3().inverted() @ Vector((1, 0, 0))
ARM_GRID = [(w,) for w in np.arange(.05, .601, .05)]
FAMILY = {'arm_L': ARM_GRID, 'arm_R': ARM_GRID, 'thigh_L': [(a,) for a in range(2, 15, 2)], 'thigh_R': [(a,) for a in range(2, 15, 2)],
          'head': sorted([(a, b) for a in range(-14, 15, 2) for b in range(-12, 13, 3) if (a, b) != (0, 0)], key=lambda x: math.hypot(*x)),
          'spine': sorted([(a,) for a in range(-12, 13, 2) if a], key=lambda x: abs(x[0]))}
BONES = {'arm_L': ['B_L_UpperArm'], 'arm_R': ['B_R_UpperArm'], 'thigh_L': ['B_L_Thigh', 'B_L_Foot'], 'thigh_R': ['B_R_Thigh', 'B_R_Foot'],
         'head': ['B_Head'], 'spine': ['B_Spine1', 'B_Spine2']}


TORSO_PLATES = {'Arm_chest', 'Arm_belt', 'Arm_spine_0', 'Arm_spine_1', 'Arm_spine_2', 'Arm_spine_3'}
RELATED = {'arm_L': TORSO_PLATES | {'Arm_pauldron_L'}, 'arm_R': TORSO_PLATES | {'Arm_pauldron_R'},
           'thigh_L': {'Arm_belt', 'Arm_knee_R', 'Arm_shin_R'}, 'thigh_R': {'Arm_belt', 'Arm_knee_L', 'Arm_shin_L'},
           'head': {'Arm_chest', 'Arm_pauldron_L', 'Arm_pauldron_R'}, 'spine': TORSO_PLATES}


def apply(r, p):
    """pose change of remedy r with parameters p (degrees; the arm's blend weight), on the current pose"""
    if r.startswith('arm_'):
        s = r[-1]; Mc = armik.W(rig, 'B_Spine2').to_3x3().normalized(); M = armik.W(rig, f'B_{s}_UpperArm')
        q = (Mc.inverted() @ M.to_3x3().normalized()).to_quaternion().slerp(STAND_ARM[s], float(p[0]))
        armik.set_world(rig, f'B_{s}_UpperArm', armik.rot_world(M, Mc @ q.to_matrix()))
    elif r.startswith('thigh_'):
        s = r[-1]; sg = 1 if s == 'L' else -1; Rf = armik.W(rig, f'B_{s}_Foot').to_3x3().normalized()
        R = Matrix.Rotation(math.radians(sg * p[0]), 3, (armik.W(rig, 'B_Pelvis').to_3x3() @ PELV_FWD).normalized())
        M = armik.W(rig, f'B_{s}_Thigh'); armik.set_world(rig, f'B_{s}_Thigh', armik.rot_world(M, R @ M.to_3x3().normalized()))
        armik.set_world(rig, f'B_{s}_Foot', armik.rot_world(armik.W(rig, f'B_{s}_Foot'), Rf))
    elif r == 'head':
        Mc = armik.W(rig, 'B_Spine2').to_3x3()
        R = Matrix.Rotation(math.radians(p[1]), 3, (Mc @ CHEST_LAT).normalized()) @ Matrix.Rotation(math.radians(p[0]), 3, (Mc @ CHEST_FWD).normalized())
        M = armik.W(rig, 'B_Head'); armik.set_world(rig, 'B_Head', armik.rot_world(M, R @ M.to_3x3().normalized()))
    elif r == 'spine':
        R2 = armik.W(rig, 'B_Spine2').to_3x3().normalized()
        R = Matrix.Rotation(math.radians(p[0]), 3, (armik.W(rig, 'B_Spine1').to_3x3() @ S1_LAT).normalized())
        M = armik.W(rig, 'B_Spine1'); armik.set_world(rig, 'B_Spine1', armik.rot_world(M, R @ M.to_3x3().normalized()))
        armik.set_world(rig, 'B_Spine2', armik.rot_world(armik.W(rig, 'B_Spine2'), R2))


def snapshot():
    return {b: rig.pose.bones[b].rotation_quaternion.copy() for bs in BONES.values() for b in bs}


def restore(snap):
    for b, q in snap.items(): rig.pose.bones[b].rotation_quaternion = q
    bpy.context.view_layer.update()


rig.animation_data.action = bpy.data.actions['Harrower_Standing']; rig.animation_data.action_slot = rig.animation_data.action.slots[0]; sc.frame_set(0)
STAND_ARM = {s: (armik.W(rig, 'B_Spine2').to_3x3().normalized().inverted() @ armik.W(rig, f'B_{s}_UpperArm').to_3x3().normalized()).to_quaternion() for s in 'LR'}
report = {}
for act in [a for a in bpy.data.actions if a.name.startswith('Harrower_Cand')]:
    rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]; n = int(act.frame_range[1])
    for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'
    rep = {'before': [], 'applied_max': {}, 'left': []}
    for it in range(PASSES):
        need = {}
        found = 0
        for f in range(n + 1):
            sc.frame_set(f); cs = measure()
            if it == 0: rep['before'] += [[round(c[0] * 100, 2), f, c[1], c[2], c[3]] for c in cs]
            if not cs: continue
            found += 1
            rem = {}
            for c in cs:
                r = remedy_of(c)
                if r: rem.setdefault(r, set()).add(c[1])
            for r, pls in rem.items():
                base = snapshot(); hit = None; pls = sorted(pls | RELATED[r])
                before = {(c[1], c[2], c[3]): c[0] for c in measure(pls)}
                for p in FAMILY[r]:
                    apply(r, p); left = measure(pls); restore(base)
                    if not any(remedy_of(c) == r or c[0] > before.get((c[1], c[2], c[3]), TOL) + 5e-4 for c in left): hit = p; break
                need.setdefault(r, np.zeros((n + 1, len(FAMILY[r][0]))))[f] = hit if hit else FAMILY[r][-1]
                # keep this frame's choice in place for the next remedy of the same frame
                apply(r, need[r][f])
            print('CONTACT', act.name, 'pass', it, 'frame', f, [[round(c[0] * 100, 2), c[1], c[2], c[3]] for c in cs],
                  {r: need[r][f].tolist() for r in rem}, flush=True)
        if not found: break
        k_ = np.exp(-.5 * (np.arange(-4, 5) / 1.5) ** 2); k_ /= k_.sum()
        for r in need:
            v = need[r]; sm = np.stack([np.convolve(np.pad(v[:, j], 4, mode='edge'), k_, mode='valid') for j in range(v.shape[1])], 1)
            big = np.linalg.norm(v, axis=1) > np.linalg.norm(sm, axis=1); need[r] = np.where(big[:, None], v, sm)
            rep['applied_max'][r] = [round(float(x), 1) for x in np.abs(need[r]).max(0)]
        keys = {}
        for f in range(n + 1):
            todo = [r for r in need if np.linalg.norm(need[r][f]) > 1e-3]
            if not todo: continue
            sc.frame_set(f)
            for r in todo: apply(r, need[r][f])
            keys[f] = {b: rig.pose.bones[b].rotation_quaternion.copy() for r in todo for b in BONES[r]}
        for f, kv in keys.items():
            for b, q in kv.items():
                pb = rig.pose.bones[b]; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
    for f in range(n + 1):
        sc.frame_set(f); rep['left'] += [[round(c[0] * 100, 2), f, c[1], c[2], c[3]] for c in measure()]
    report[act.name] = rep
    print('CONTACTS', act.name, json.dumps({'applied_max': rep['applied_max'], 'left': rep['left']}), flush=True)
rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(Path(out).resolve()))
(P / 'review/cand_contacts.json').write_text(json.dumps(report, indent=2) + '\n')
