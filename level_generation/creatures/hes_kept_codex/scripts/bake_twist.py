"""Rebake twist after motion-only corrections, preserving fitted mesh weights."""
import bpy,sys,os,math
import numpy as np
from mathutils import Vector,Quaternion,Matrix
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src));rig=bpy.data.objects['Rig'];FA=.6;UA=.5
def twist_about(q, axis):
    v = Vector((q.x, q.y, q.z)); a = 2 * math.atan2(v.dot(axis), q.w)
    return (a + math.pi) % (2 * math.pi) - math.pi


def bake_twist(act):
    rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    for f in np.arange(f0, f1 + .01,.5):
        bpy.context.scene.frame_set(int(f),subframe=float(f%1))
        for s in ('L', 'R'):
            # forearm twist: the hand's rotation relative to the forearm, twist part about the forearm axis (Y of the
            # twist bone = forearm frame, so local Y is not the segment; use the segment in the forearm's local frame)
            fb, hb = rig.data.bones[f'B_{s}_Forearm'], rig.data.bones[f'B_{s}_Hand']
            seg_local = (fb.matrix_local.inverted() @ hb.head_local).normalized()
            rel = (rig.pose.bones[f'B_{s}_Forearm'].matrix.inverted() @ rig.pose.bones[f'B_{s}_Hand'].matrix).to_quaternion()
            rest_rel = (fb.matrix_local.inverted() @ hb.matrix_local).to_quaternion()
            dq = rel @ rest_rel.inverted()
            tw = twist_about(dq, seg_local) * FA
            p = rig.pose.bones[f'B_{s}_ForearmTwist']; p.rotation_mode = 'QUATERNION'
            p.rotation_quaternion = Quaternion(seg_local, tw)
            p.keyframe_insert('rotation_quaternion', frame=f)
            # upper arm counter twist near the shoulder
            ub = rig.data.bones[f'B_{s}_UpperArm']
            useg = (ub.matrix_local.inverted() @ rig.data.bones[f'B_{s}_Forearm'].head_local).normalized()
            uq = rig.pose.bones[f'B_{s}_UpperArm'].matrix_basis.to_quaternion()
            p = rig.pose.bones[f'B_{s}_UpperArmTwist']; p.rotation_mode = 'QUATERNION'
            p.rotation_quaternion = Quaternion(useg, -UA * twist_about(uq, useg))
            p.keyframe_insert('rotation_quaternion', frame=f)
    rig.animation_data.action = None


for act in [a for a in bpy.data.actions if a.use_fake_user]:
    bake_twist(act)
    print('BAKED twist', act.name)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

sys.stdout.flush();sys.stderr.flush();os._exit(0)
