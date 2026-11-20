"""Remove unkeyed numerical scale drift from matrix fitting before final review export."""
from pathlib import Path
import bpy, json, math
from mathutils import Vector, Quaternion
p=Path(__file__).resolve().parents[1];out=p/'review/motion_options'
bpy.ops.wm.open_mainfile(filepath=str(out/'ogre_motion_options.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Ogre']
for pb in rig.pose.bones:pb.scale=(1,1,1)
new_names=json.loads((out/'sources.json').read_text())
def continuous_keys(act):
    curves={}
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    if fc.data_path.endswith('rotation_quaternion'):
                        curves.setdefault(fc.data_path,{})[fc.array_index]=fc
    for components in curves.values():
        if len(components)!=4:continue
        keys=[components[i].keyframe_points for i in range(4)];previous=None
        for k in range(min(map(len,keys))):
            q=[keys[i][k].co[1] for i in range(4)]
            if previous is not None and sum(a*b for a,b in zip(q,previous))<0:
                q=[-v for v in q]
                for i in range(4):keys[i][k].co[1]=q[i]
            previous=q
        for fc in components.values():
            for key in fc.keyframe_points:key.interpolation='LINEAR'
            fc.update()
def twist(q,axis):
    angle=2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w)
    return (angle+math.pi)%(2*math.pi)-math.pi
for name in new_names:
    a=bpy.data.actions[name];continuous_keys(a)
    rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];previous={}
    for f in range(int(a.frame_range[1])+1):
        bpy.context.scene.frame_set(f)
        for side in 'LR':
            fb,hb=rig.data.bones[f'B_{side}_Forearm'],rig.data.bones[f'B_{side}_Hand']
            fa=(fb.matrix_local.inverted()@hb.head_local).normalized()
            rel=(rig.pose.bones[fb.name].matrix.inverted()@rig.pose.bones[hb.name].matrix).to_quaternion()
            rest=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion()
            ub=rig.data.bones[f'B_{side}_UpperArm'];ua=(ub.matrix_local.inverted()@fb.head_local).normalized()
            values=[(f'B_{side}_ForearmTwist',fa,twist(rel@rest.inverted(),fa),.5),
                    (f'B_{side}_UpperArmTwist',ua,twist(rig.pose.bones[ub.name].matrix_basis.to_quaternion(),ua),-.5)]
            for bone,axis,angle,share in values:
                if bone in previous:angle=previous[bone]+(angle-previous[bone]+math.pi)%(2*math.pi)-math.pi
                previous[bone]=angle
                pb=rig.pose.bones[bone];pb.rotation_quaternion=Quaternion(axis,angle*share)
                pb.keyframe_insert('rotation_quaternion',frame=f)
    continuous_keys(a)

rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=bpy.data.actions['Standing'].slots[0]
bpy.context.scene.frame_set(0)
for o in bpy.data.objects:o.select_set(o in (body,rig))
bpy.context.view_layer.objects.active=rig
bpy.ops.wm.save_as_mainfile(filepath=str(out/'ogre_motion_options.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'ogre_motion_options.glb'),use_selection=True,export_format='GLB',
 export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,
 export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,
 export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
