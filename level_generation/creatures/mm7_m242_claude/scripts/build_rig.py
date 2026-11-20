"""G3 / H4: our armature with the source's bone frames (m242 copy: joints from the bone pieces, rigid piece weights).

Joint positions: work/joints_final.json (composed from Meshy's auto-rig and ring centres). For every source bone with a
child, the smallest swing q taking the source segment (T-pose) onto ours gives our rest frame R = q @ R_src, so our
bone differs from the source only by a swing perpendicular to the segment (no roll offset). Leaf bones take their
parent's swing. Fingers (no mesh fit yet; G5) are the source fingers carried rigidly by the hand's swing and scaled by
the hand-length ratio. Bones keep the source names (B_*, plus the right thumb's B_R_Finger0.001/.002 quirk).
Weights: Meshy's auto-rig weights mapped by bone name (nearest-vertex transfer from the rigged GLB); the Meshy hand
weight goes to B_*_Hand (fingers get theirs at G5).
Writes work/rig_v1.blend (objects 'Body', 'Rig') and scene['rig_offsets'] (per bone q and R_src for the retarget).
Args: none"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Matrix, Vector, Quaternion
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W_ = lambda *p: os.path.join(HERE, *p)
SRC = json.load(open(W_('work', 'source_rest.json')))
J = {k: Vector(v) for k, v in json.load(open(W_('work', 'joints_final.json')))['joints'].items()}
NAME = {'B_Pelvis': 'Pelvis', 'B_Spine': 'Spine', 'B_Spine1': 'Spine1', 'B_Spine2': 'Spine2', 'B_Neck': 'Neck', 'B_Head': 'Head'}
for s in ('L', 'R'):
    for b in ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Thigh', 'Calf', 'Foot', 'Toe0'):
        NAME[f'B_{s}_{b}'] = f'{s}_{b}'
bpy.ops.wm.open_mainfile(filepath=W_('work', 'step1.blend'))
body = bpy.data.objects['Body']

# ---------------------------------------------------------------- heads and frames
order = []
def visit(n):
    order.append(n)
    for c in [k for k, v in SRC.items() if v['parent'] == n]:
        visit(c)
visit('B_Pelvis')
head, rot, swing = {}, {}, {}
for n in order:
    s = SRC[n]
    Rs = Matrix([Vector(r) for r in s['rot']])
    if n in NAME:
        head[n] = J[NAME[n]].copy()                             # fingers are placed after the hand's swing is known
    rot[n] = Rs
for n in order:
    s = SRC[n]
    c = s['child']
    if c and n in NAME and c in NAME:
        q = Vector(s['seg']).rotation_difference(head[c] - head[n])
    elif s['parent'] in swing:
        q = swing[s['parent']]
    else:
        q = Quaternion()
    if n == 'B_Pelvis':
        q = Quaternion()                                        # root keeps the source frame (Meshy's hips sit higher)
    swing[n] = q
    rot[n] = q.to_matrix() @ rot[n]
# hands: the rest swing comes from OUR mesh hand (finger direction + thumb side), not from the forearm (TEST_DRIVE:
# the inherited swing left the mesh hand 36 deg bent and 26 deg rolled against the source hand -> palm-up idle)
CO = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
HAND_FRAME = {}
for sd in ('L', 'R'):
    hn, fa = f'B_{sd}_Hand', f'B_{sd}_Forearm'
    wr = np.array(head[hn]); fd = np.array(head[hn] - head[fa]); fd /= np.linalg.norm(fd)
    rel = CO - wr
    hv = CO[(rel @ fd > 0.01) & (np.linalg.norm(rel, axis=1) < 0.22) & (np.sign(CO[:, 0]) == np.sign(wr[0]))]
    c = hv.mean(0); U = np.linalg.svd(hv - c, full_matrices=False)[2]
    f_our = U[0] if U[0] @ (c - wr) > 0 else -U[0]
    pr = (hv - c) @ U[1]
    t_our = U[1] if np.abs(pr.max()) > np.abs(pr.min()) else -U[1]           # toward the thumb (the wider side)
    FJ0 = json.load(open(W_('work', 'finger_joints.json'))) if os.path.exists(W_('work', 'finger_joints.json')) else None
    if FJ0 is not None:
        # the mesh's own knuckle line (fitted fingers) instead of the PCA width axis: PCA was 35-37 deg off in roll,
        # which put the derived sword grip 29 deg away from the fist's natural axis (TEST_DRIVE.md)
        kn = {i: np.array(FJ0[sd][f'B_{sd}_Finger{i}']) for i in (1, 2, 4)}
        f_our = kn[2] - wr; f_our /= np.linalg.norm(f_our)
        t_our = kn[1] - kn[4]
    h0 = np.array(SRC[hn]['head'])
    f_src = np.array(SRC[f'B_{sd}_Finger2']['head']) - h0; f_src /= np.linalg.norm(f_src)
    t_src = np.array(SRC[f'B_{sd}_Finger1']['head']) - np.array(SRC[f'B_{sd}_Finger4']['head'])
    def basis(f, t):
        t = t - f * (t @ f); t /= np.linalg.norm(t)
        return np.column_stack([f, t, np.cross(f, t)])
    Rq = basis(f_our, t_our) @ basis(f_src, t_src).T
    swing[hn] = Matrix(Rq.tolist()).to_quaternion()
    if os.environ.get('HAND_FROM_FOREARM', '1') == '1':
        # m242: the claws are rigid bone pieces held palm-down like the source T-pose hand; the PCA thumb-side guess
        # of a spread claw is unreliable (batch B: 150 deg flips), so the hand keeps the forearm's minimal swing
        swing[hn] = swing[fa].copy()
    rot[hn] = swing[hn].to_matrix() @ Matrix([Vector(r) for r in SRC[hn]['rot']])
    # hand length: wrist -> farthest vertex along the finger direction (middle fingertip); source: wrist -> middle
    # distal joint + one distal segment (its imported tail is unusable)
    our_len = float(((hv - wr) @ f_our).max())
    m1, m2 = np.array(SRC[f'B_{sd}_Finger21']['head']), np.array(SRC[f'B_{sd}_Finger22']['head'])
    src_len = float(((m2 + (m2 - m1)) - h0) @ f_src)
    HAND_FRAME[sd] = {'verts': int(len(hv)), 'k': our_len / src_len, 'our_len': our_len, 'src_len': src_len}
    print('HAND', sd, 'mesh-measured rest swing', round(math.degrees(swing[hn].angle), 1), 'deg;',
          'differs from the inherited forearm swing by',
          round(math.degrees(swing[hn].rotation_difference(swing[fa]).angle), 1), 'deg;', len(hv), 'hand verts;',
          'hand length ours', round(HAND_FRAME[sd]['our_len'], 3), 'source', round(HAND_FRAME[sd]['src_len'], 3))
for n in order:
    if n not in NAME and SRC[n]['parent'] in swing and 'Finger' in n:
        swing[n] = swing['B_L_Hand' if '_L_' in n else 'B_R_Hand']
        rot[n] = swing[n].to_matrix() @ Matrix([Vector(r) for r in SRC[n]['rot']])
FJ = json.load(open(W_('work', 'finger_joints.json'))) if os.path.exists(W_('work', 'finger_joints.json')) else None
for n in order:
    if n not in NAME and FJ is not None and n in FJ['L' if '_L_' in n else 'R']:
        sd = 'L' if '_L_' in n else 'R'
        head[n] = Vector(FJ[sd][n])
        c = SRC[n]['child']
        tgt = Vector(FJ[sd][c]) if c else Vector(FJ[sd][n + '_tip'])
        sseg = Vector(SRC[n]['seg']) if c else (Vector(SRC[n]['head']) - Vector(SRC[SRC[n]['parent']]['head']))
        q = sseg.rotation_difference(tgt - head[n])
        # keep the finger's roll from the hand: apply the minimal swing on top of the hand's swing
        qh = swing['B_L_Hand' if sd == 'L' else 'B_R_Hand']
        q = (qh @ sseg).rotation_difference(tgt - head[n]) @ qh
        swing[n] = q
        rot[n] = q.to_matrix() @ Matrix([Vector(r) for r in SRC[n]['rot']])
        continue
    if n not in NAME:
        hand = 'B_L_Hand' if '_L_' in n else 'B_R_Hand'
        k = HAND_FRAME[hand[2]]['k']                            # measured hand length ratio (not the forearm's)
        head[n] = head[hand] + swing[hand] @ ((Vector(SRC[n]['head']) - Vector(SRC[hand]['head'])) * k)

# ---------------------------------------------------------------- armature
ad = bpy.data.armatures.new('Rig'); rig = bpy.data.objects.new('Rig', ad)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for n in order:
    eb = ad.edit_bones.new(n)
    R = rot[n]
    c = SRC[n]['child']
    L = (head[c] - head[n]).length if c in head and (head[c] - head[n]).length > 1e-4 else 0.04
    eb.head = head[n]; eb.tail = head[n] + R.col[1] * L
    eb.align_roll(R.col[2])
for n in order:
    if SRC[n]['parent'] in SRC:                                # B_Pelvis's parent is the source's Motion root (dropped)
        ad.edit_bones[n].parent = ad.edit_bones[SRC[n]['parent']]
bpy.ops.object.mode_set(mode='OBJECT')
# frame check: edit-bone matrices must equal the intended frames
err = max(math.degrees((rig.data.bones[n].matrix_local.to_3x3().to_quaternion()).rotation_difference(rot[n].to_quaternion()).angle)
          for n in order)
print('RIG bones', len(order), 'max frame error deg', round(err, 3))

# ---------------------------------------------------------------- m242: rigid piece weights (no Meshy auto-rig)
# every piece goes 100 % to the deforming bone whose segment is nearest its centroid (fingers excluded: the claws
# stay rigid on the hand); the cloth pieces get the same provisional weight, replaced by weights_fix.py's robe rules
DEFORM = [n for n in order if 'Finger' not in n and not any(k in n for k in ('Thigh', 'Calf', 'Foot', 'Toe'))]
segs = {}
for n in DEFORM:
    c = SRC[n]['child']
    h0 = np.array(head[n]); h1 = np.array(head[c]) if c in head and c in DEFORM else h0 + np.array(rot[n].col[1]) * 0.05
    if n.endswith('_Hand'):
        h1 = h0 + (h0 - np.array(head[n.replace('Hand', 'Forearm')])) * 0.8
    segs[n] = (h0, h1)
def seg_d(p, a, b):
    t = np.clip(((p - a) @ (b - a)) / max((b - a) @ (b - a), 1e-9), 0, 1)
    return np.linalg.norm(p - (a + t * (b - a)))
pv = np.zeros(len(body.data.vertices), np.int32); body.data.attributes['piece'].data.foreach_get('value', pv)
CO = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
body.vertex_groups.clear()
groups = {n: body.vertex_groups.new(name=n) for n in order}
count = {}
SK = CO[pv == 0]; sk_lo, sk_hi = SK.min(0) - 0.01, SK.max(0) + 0.01                 # the skull P00 (teeth, jaw inside)
cl = np.zeros(len(CO), np.int32); body.data.attributes['cloth'].data.foreach_get('value', cl)
for p in sorted(set(pv.tolist())):
    ids = np.where(pv == p)[0]; c = CO[ids].mean(0)
    if not cl[ids[0]] and np.all(c > sk_lo) and np.all(c < sk_hi):
        groups['B_Head'].add(ids.tolist(), 1.0, 'REPLACE'); count['B_Head'] = count.get('B_Head', 0) + 1; continue
    cands = [n for n in DEFORM
             if not (c[2] < head['B_Neck'][2] and n in ('B_Neck', 'B_Head'))            # ribs stay on the trunk
             and not (abs(c[0] - head['B_Pelvis'][0]) < 0.12 and 'Clavicle' in n)]    # sternum/ribs not on a shrug
    best = min(cands, key=lambda n: seg_d(c, *segs[n]))
    groups[best].add(ids.tolist(), 1.0, 'REPLACE'); count[best] = count.get(best, 0) + 1
print('WEIGHTS rigid pieces per bone', count)
body.parent = rig
m = body.modifiers.new('Armature', 'ARMATURE'); m.object = rig
bpy.context.scene['rig_offsets'] = json.dumps({n: {'q': list(swing[n]), 'R_src': [list(r) for r in SRC[n]['rot']]} for n in order})
bpy.ops.wm.save_as_mainfile(filepath=W_('work', 'rig_v1.blend'))
