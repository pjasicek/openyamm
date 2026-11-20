"""hkr armour helper bones (non-weighted joints the rigid plate attachments ride; baked into every action):
- B_<S>_Pauldron (child of B_<S>_Clavicle, head at the shoulder joint, the upper arm's rest frame): turns by K_PAUL
  (0.8; 0.65 before the skinned shell) of the upper arm's swing relative to the clavicle (twist removed). A pauldron on the clavicle let the raised
  arm push 4 cm into it; on the upper arm it would scrape the neck. The shoulder-spike bone (Bone_041 / Bone_036)
  is re-parented to it, so the spikes stay where they pierce the pauldron (their roots slide under it).
- (the v3 central tasset's B_Groin is gone: the v4 tassets are shell pieces riding their thighs)
Args: -- <in> <out>"""
import bpy, sys, os, math
from mathutils import Quaternion, Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]
K_PAUL = float(os.environ.get('K_PAUL', '0.8'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
bpy.context.view_layer.objects.active = rig
rig.animation_data_create(); rig.animation_data.action = None
bpy.ops.object.mode_set(mode='EDIT'); eb = rig.data.edit_bones
for s, spk in (('L', 'Bone_041'), ('R', 'Bone_036')):
    n = f'B_{s}_Pauldron'
    if n in eb: eb.remove(eb[n])
    ua = eb[f'B_{s}_UpperArm']
    b = eb.new(n); b.head = ua.head.copy(); b.tail = ua.head + (ua.tail - ua.head).normalized() * 0.08; b.roll = ua.roll
    b.parent = eb[f'B_{s}_Clavicle']; b.use_deform = True
    eb[spk].parent = b
for s in 'LR':                                     # overlay nodes riding the pauldron (own nodes to split): tier B's
    for n in (f'B_{s}_Carapace', f'B_{s}_Spikes'):  # carapace (it replaces the ivory cap) and the spikes every tier wears
        if n in eb: eb.remove(eb[n])
        p_ = eb[f'B_{s}_Pauldron']; c_ = eb.new(n); c_.head = p_.head.copy(); c_.tail = p_.tail.copy(); c_.roll = p_.roll
        c_.parent = p_; c_.use_deform = True
if 'B_L_Buckler' in eb: eb.remove(eb['B_L_Buckler'])
fa_ = eb['B_L_Forearm']; bk = eb.new('B_L_Buckler')                 # the buckler's node (rigid on the forearm)
bk.head = fa_.head + (fa_.tail - fa_.head) * 0.0 + (eb['B_L_Hand'].head - fa_.head) * 0.45; bk.tail = bk.head + (fa_.tail - fa_.head).normalized() * 0.06
bk.roll = fa_.roll; bk.parent = fa_; bk.use_deform = True
if 'B_Groin' in eb: eb.remove(eb['B_Groin'])          # the v3 central tasset's hinge (gone)
for s in 'LR':                                     # the v4 hinged tassets (tried, gone)
    if f'B_{s}_Tasset' in eb: eb.remove(eb[f'B_{s}_Tasset'])
bpy.ops.object.mode_set(mode='OBJECT')
REST = lambda n: rig.data.bones[n].matrix_local.to_3x3()


def basis_from_parent_rot(child, parent, q):
    """matrix_basis quaternion of `child` for a rotation q expressed in the parent's rest-local space"""
    Rb = REST(parent).inverted() @ REST(child)
    return (Rb.inverted() @ q.to_matrix() @ Rb).to_quaternion()


for act in [x for x in bpy.data.actions if x.use_fake_user]:
    rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    keys = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        for s in 'LR':
            ua = rig.pose.bones[f'B_{s}_UpperArm']; cl = rig.pose.bones[f'B_{s}_Clavicle']
            d_rest = REST(cl.name).inverted() @ REST(ua.name).col[1]
            d_pose = cl.matrix.to_3x3().inverted() @ ua.matrix.to_3x3().col[1]
            q = d_rest.rotation_difference(d_pose)
            q = Quaternion(q.axis, q.angle * K_PAUL) if q.angle > 1e-6 else Quaternion()
            keys.append((f, f'B_{s}_Pauldron', basis_from_parent_rot(f'B_{s}_Pauldron', cl.name, q)))
    for f, n, q in keys:
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q
        pb.keyframe_insert('rotation_quaternion', frame=f)
    print('HELPERS baked', act.name, f0, f1)
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a[1]))
