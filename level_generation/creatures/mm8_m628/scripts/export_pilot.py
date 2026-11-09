"""Export the retained pilot actions for review without changing the animated master."""
import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilot_bow.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
for a in bpy.data.actions:
    for layer in a.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                curves={}
                for fc in cb.fcurves:
                    for k in fc.keyframe_points:k.interpolation='LINEAR'
                    if fc.data_path.endswith('rotation_quaternion'):curves.setdefault(fc.data_path,{})[fc.array_index]=fc
                for cs in curves.values():
                    assert len(cs)==4
                    prior=None
                    for j in range(len(cs[0].keyframe_points)):
                        q=[cs[i].keyframe_points[j].co.y for i in range(4)]
                        if prior and sum(x*y for x,y in zip(q,prior))<0:
                            for i in range(4):cs[i].keyframe_points[j].co.y*=-1
                            q=[-x for x in q]
                        prior=q
                for fc in cb.fcurves:fc.update()
for ob in bpy.data.objects:ob.select_set(ob in [body,rig])
bpy.context.view_layer.objects.active=rig
out=P/'review/viewer';out.mkdir(exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(out/'m628_pilot.glb'),use_selection=True,export_format='GLB',
    export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,
    export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,
    export_reset_pose_bones=True,export_anim_slide_to_zero=True)
(P/'work/pilot_clips.json').write_text(json.dumps({a.name:float(a.frame_range[1])/30 for a in bpy.data.actions},indent=2))
