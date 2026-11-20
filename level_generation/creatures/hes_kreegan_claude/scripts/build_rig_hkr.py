"""hkr G3: the shared Kreegan rig = the MM6 Demon's skeleton re-framed onto the humanoid set's source frames.

Joints: every head is the demon's own bone head (work/demon_joints.json, the installed mm6_demon rig), so the demon's
skin weights apply unchanged (renamed mixamorig:* -> B_*). Frames: as build_rig.py, our rest frame = q @ R_src where
q is the smallest swing taking the set's (T-pose) segment onto the demon's segment; the pelvis keeps the source
frame; leaf bones take their parent's swing; the hands' swing comes from the demon's own finger joints (wrist ->
middle knuckle, index -> pinky knuckle line), the fingers' from their own joints (Thumb/Index/Middle/Ring/Pinky 1-3 ->
B_*_Finger0..4, the 4th joint = the tip). This keeps retarget.py's world rule exact (posed world = source world).
Extra demon bones keep their names and rest frames (rigid unless a clip moves them): the tail chain Bone_020..015
(B_Pelvis), the chest ornament Bone_024/023 (B_Spine2: it rides with the chest plate), the shoulder-spike bones Bone_041/040 (B_L_Clavicle) and
Bone_036/035 (B_R_Clavicle), the jaw Bone_025 and 'headfront' (B_Head). The demon's forearm twist weights (Twist0-2)
are merged into B_*_Forearm (twist_bones.py adds its own twist bone and ramp).
Writes work/rig_v1.blend ('Body', 'Rig', scene['rig_offsets'], scene['demon_map']). Args: none"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Matrix, Vector, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W_ = lambda *p: os.path.join(HERE, *p)
SRC = json.load(open(W_('work', 'source_rest.json')))
DJ = json.load(open(W_('work', 'demon_joints.json')))
MAP = {'B_Pelvis': 'Hips', 'B_Spine': 'Spine', 'B_Spine1': 'Spine1', 'B_Spine2': 'Spine2', 'B_Neck': 'Neck', 'B_Head': 'Head'}
for s, side in (('L', 'Left'), ('R', 'Right')):
    MAP.update({f'B_{s}_Clavicle': f'{side}Shoulder', f'B_{s}_UpperArm': f'{side}Arm', f'B_{s}_Forearm': f'{side}ForeArm',
                f'B_{s}_Hand': f'{side}Hand', f'B_{s}_Thigh': f'{side}UpLeg', f'B_{s}_Calf': f'{side}Leg',
                f'B_{s}_Foot': f'{side}Foot', f'B_{s}_Toe0': f'{side}ToeBase'})
    for i, f in enumerate(('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')):
        chain = [f'B_{s}_Finger{i}', f'B_{s}_Finger{i}1', f'B_{s}_Finger{i}2']
        if s == 'R' and i == 0:
            chain = ['B_R_Finger0', 'B_R_Finger0.001', 'B_R_Finger0.002']
        for j, n in enumerate(chain):
            MAP[n] = f'{side}Hand{f}{j + 1}'
MAP = {k: 'mixamorig:' + v for k, v in MAP.items()}
INV = {v: k for k, v in MAP.items()}
EXTRA_PARENT = {'Bone_020': 'B_Pelvis', 'Bone_024': 'B_Spine2', 'Bone_041': 'B_L_Clavicle', 'Bone_036': 'B_R_Clavicle',
                'Bone_025': 'B_Head', 'headfront': 'B_Head'}
EXTRA = [n for n in DJ if n.startswith('Bone_') or n == 'headfront']
MERGE = {}
for s, side in (('L', 'Left'), ('R', 'Right')):
    for k in range(3):
        MERGE[f'Demon_{side}_ForearmTwist{k}'] = f'B_{s}_Forearm'
    for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky'):
        MERGE[f'mixamorig:{side}Hand{f}4'] = INV[f'mixamorig:{side}Hand{f}3']
    MERGE[f'mixamorig:{side}Toe_End'] = f'B_{s}_Toe0'
MERGE['mixamorig:HeadTop_End'] = 'B_Head'

bpy.ops.wm.open_mainfile(filepath=W_('work', 'step1.blend'))
body = bpy.data.objects['Body']; demon = bpy.data.objects['Demon']
H = lambda dn: Vector(DJ[dn]['head'])
order = []
def visit(n):
    order.append(n)
    for c in [k for k, v in SRC.items() if v['parent'] == n]:
        visit(c)
visit('B_Pelvis')
head = {n: H(MAP[n]) for n in order}
head['B_Pelvis'].x = 0.0                          # the demon's hips sit 3 cm off-centre; the thighs are symmetric
tip = {}
for n in order:
    if 'Finger' in n and SRC[n]['child'] is None:
        dn = MAP[n]; tip[n] = H(dn[:-1] + '4')        # distal joint -> the 4th (end) joint
rot, swing = {}, {}
for n in order:
    s = SRC[n]; c = s['child']
    Rs = Matrix([Vector(r) for r in s['rot']])
    if n == 'B_Pelvis':
        q = Quaternion()
    elif n.endswith('_Hand'):
        sd = n[2]
        f_our = (head[f'B_{sd}_Finger2'] - head[n]).normalized(); t_our = head[f'B_{sd}_Finger1'] - head[f'B_{sd}_Finger4']
        f_src = (Vector(SRC[f'B_{sd}_Finger2']['head']) - Vector(s['head'])).normalized()
        t_src = Vector(SRC[f'B_{sd}_Finger1']['head']) - Vector(SRC[f'B_{sd}_Finger4']['head'])
        def basis(f, t):
            t = (t - f * t.dot(f)).normalized(); return Matrix((f, t, f.cross(t))).transposed()
        q = (basis(f_our, t_our) @ basis(f_src, t_src).transposed()).to_quaternion()
    elif c:
        q = Vector(s['seg']).rotation_difference(head[c] - head[n])
    elif 'Finger' in n:
        ps = swing[s['parent']]
        sseg = Vector(s['head']) - Vector(SRC[s['parent']]['head'])
        q = (ps @ sseg).rotation_difference(tip[n] - head[n]) @ ps
    else:
        q = swing[s['parent']].copy()
    if 'Finger' in n and c:
        hs = swing[s['parent']] if not s['parent'].endswith('_Hand') else swing[s['parent']]
        q = (hs @ Vector(s['seg'])).rotation_difference(head[c] - head[n]) @ hs     # keep the roll from the hand
    swing[n] = q; rot[n] = q.to_matrix() @ Rs
ad = bpy.data.armatures.new('Rig'); rig = bpy.data.objects.new('Rig', ad)
bpy.context.scene.collection.objects.link(rig); bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for n in order:
    eb = ad.edit_bones.new(n); R = rot[n]; c = SRC[n]['child']
    L = (head[c] - head[n]).length if c else ((tip[n] - head[n]).length if n in tip else 0.05)
    eb.head = head[n]; eb.tail = head[n] + R.col[1] * max(L, 0.01); eb.align_roll(R.col[2])
for n in order:
    if SRC[n]['parent'] in SRC:
        ad.edit_bones[n].parent = ad.edit_bones[SRC[n]['parent']]
for n in EXTRA:                                   # parents first: walk the demon hierarchy
    pass
done = set()
def add_extra(n):
    if n in done: return
    p = DJ[n]['parent']
    if p in EXTRA: add_extra(p)
    M = Matrix(DJ[n]['matrix']); eb = ad.edit_bones.new(n)
    eb.head = Vector(DJ[n]['head']); eb.tail = Vector(DJ[n]['tail']); eb.align_roll(M.to_3x3().col[2])
    eb.parent = ad.edit_bones[p] if p in EXTRA else ad.edit_bones[EXTRA_PARENT[n]]
    done.add(n)
for n in EXTRA: add_extra(n)
bpy.ops.object.mode_set(mode='OBJECT')
err = max(math.degrees(rig.data.bones[n].matrix_local.to_3x3().to_quaternion().rotation_difference(rot[n].to_quaternion()).angle) for n in order)
jerr = max((rig.data.bones[n].head_local - H(MAP[n])).length for n in order if n != 'B_Pelvis')
print('RIG bones', len(rig.data.bones), 'set bones', len(order), 'extra', len(EXTRA), 'max frame error deg', round(err, 3),
      'max joint offset from the demon mm', round(jerr * 1000, 3))
for sd in 'LR':
    print('HAND', sd, 'rest swing vs the forearm deg', round(math.degrees(swing[f'B_{sd}_Hand'].rotation_difference(swing[f'B_{sd}_Forearm']).angle), 1))
# ---------------------------------------------------------------- weights: rename / merge the demon's groups
old = {g.index: g.name for g in body.vertex_groups}
data = [[(old[g.group], g.weight) for g in v.groups] for v in body.data.vertices]
body.vertex_groups.clear()
names = order + EXTRA
groups = {n: body.vertex_groups.new(name=n) for n in names}
unm = set()
for vi, gs in enumerate(data):
    acc = {}
    for gn, w in gs:
        n = INV.get(gn) or MERGE.get(gn) or (gn if gn in groups else None)
        if n is None:
            unm.add(gn); continue
        acc[n] = acc.get(n, 0.0) + w
    for n, w in acc.items():
        if w > 1e-5: groups[n].add([vi], w, 'REPLACE')
print('WEIGHTS unmapped demon groups', sorted(unm))
body.modifiers.clear()
body.parent = rig
m = body.modifiers.new('Armature', 'ARMATURE'); m.object = rig
# garments from creature.json by piece
pv = np.zeros(len(body.data.vertices), np.int32); body.data.attributes['piece'].data.foreach_get('value', pv)
gv = np.array([cfg.LAB.get(int(p), 0) for p in pv], np.int32)
if 'garment' not in body.data.attributes:
    body.data.attributes.new('garment', 'INT', 'POINT')
body.data.attributes['garment'].data.foreach_set('value', gv)
bpy.context.scene['rig_offsets'] = json.dumps({n: {'q': list(swing[n]), 'R_src': [list(r) for r in SRC[n]['rot']]} for n in order})
bpy.context.scene['demon_map'] = json.dumps(MAP)
bpy.data.objects.remove(demon, do_unlink=True)                 # its clips live in work/demon_clips.blend
bpy.ops.wm.save_as_mainfile(filepath=W_('work', 'rig_v1.blend'))
