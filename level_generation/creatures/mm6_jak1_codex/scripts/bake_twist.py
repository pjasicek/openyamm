import bpy,math
from mathutils import Vector,Quaternion
rig=bpy.data.objects["Rig"];FA=.6;UA=.5
def twist_about(q, axis):
    v = Vector((q.x, q.y, q.z)); a = 2 * math.atan2(v.dot(axis), q.w)
    return (a + math.pi) % (2 * math.pi) - math.pi


def bake_twist(act):
    rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    previous={}
    def continuous(key,a):
        if key in previous:a=previous[key]+(a-previous[key]+math.pi)%(2*math.pi)-math.pi
        previous[key]=a;return a
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f)
        for s in ('L', 'R'):
            # forearm twist: the hand's rotation relative to the forearm, twist part about the forearm axis (Y of the
            # twist bone = forearm frame, so local Y is not the segment; use the segment in the forearm's local frame)
            fb, hb = rig.data.bones[f'B_{s}_Forearm'], rig.data.bones[f'B_{s}_Hand']
            seg_local = (fb.matrix_local.inverted() @ hb.head_local).normalized()
            rel = (rig.pose.bones[f'B_{s}_Forearm'].matrix.inverted() @ rig.pose.bones[f'B_{s}_Hand'].matrix).to_quaternion()
            rest_rel = (fb.matrix_local.inverted() @ hb.matrix_local).to_quaternion()
            dq = rel @ rest_rel.inverted()
            ub=rig.data.bones[f'B_{s}_UpperArm'];neutral=(rig.pose.bones[f'B_{s}_UpperArm'].matrix@ub.matrix_local.inverted()@fb.matrix_local).to_3x3();actual=rig.pose.bones[f'B_{s}_Forearm'].matrix.to_3x3();axis=(actual@seg_local).normalized();neutral=(neutral@seg_local).rotation_difference(axis).to_matrix()@neutral
            main=twist_about((neutral.inverted()@actual).to_quaternion(),seg_local)
            total=continuous(s+'F',main+twist_about(dq,seg_local));tw=max(-math.radians(85),min(math.radians(85),total*FA))-main
            p = rig.pose.bones[f'B_{s}_ForearmTwist']; p.rotation_mode = 'QUATERNION'
            p.rotation_quaternion = Quaternion(seg_local, tw)
            p.keyframe_insert('rotation_quaternion', frame=f)
            # upper arm counter twist near the shoulder
            ub = rig.data.bones[f'B_{s}_UpperArm']
            useg = (ub.matrix_local.inverted() @ rig.data.bones[f'B_{s}_Forearm'].head_local).normalized()
            uq = rig.pose.bones[f'B_{s}_UpperArm'].matrix_basis.to_quaternion()
            p = rig.pose.bones[f'B_{s}_UpperArmTwist']; p.rotation_mode = 'QUATERNION'
            p.rotation_quaternion = Quaternion(useg, -UA * continuous(s+'U',twist_about(uq, useg)))
            p.keyframe_insert('rotation_quaternion', frame=f)
    for s in ('L','R'):
        for kind in ('ForearmTwist','UpperArmTwist'):
            pb=rig.pose.bones[f'B_{s}_{kind}'];samples=[]
            for f in range(f0,f1+1):
                bpy.context.scene.frame_set(f);samples.append(pb.rotation_quaternion.copy())
            for i in range(len(samples)):
                # Short spherical averaging and a 360 deg/s rate bound affects the deformation helper, not the hand or elbow motion.
                q=samples[max(0,i-8)].copy()
                for k,j in enumerate(range(i-7,i+9),2):q=q.slerp(samples[max(0,min(len(samples)-1,j))],1/k)
                if i:
                    delta=last.rotation_difference(q);ang=min(delta.angle,math.tau-delta.angle);limit=math.radians(360)/bpy.context.scene.render.fps
                    if ang>limit:q=last.slerp(q,limit/ang)
                last=q.copy();pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f0+i)
    rig.animation_data.action = None

