from pathlib import Path
import bpy,json,hashlib
P=Path(__file__).resolve().parents[1];V=P/'review/viewer'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/grounded.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
objects=[rig,bpy.data.objects['Body'],bpy.data.objects['StaffMesh']]
clips={a.name:{'label':a.name,'duration':float(a.frame_range[1])/30,'mode':'loop' if a.name in ['Standing','Walking','Running'] else 'once','anchors':[],'provenance':'Local humanoid-set / Mixamo clips, fitted source frames, native staff carry and fidget.'} for a in bpy.data.actions}
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    curves={}
    for fc in bag.fcurves:
     if fc.data_path.endswith('rotation_quaternion'):curves.setdefault(fc.data_path,{})[fc.array_index]=fc
     for k in fc.keyframe_points:k.interpolation='LINEAR'
    for cs in curves.values():
     if len(cs)!=4:continue
     keys=[cs[i].keyframe_points for i in range(4)];prev=None
     for j in range(min(len(x) for x in keys)):
      q=[keys[i][j].co.y for i in range(4)]
      if prev is not None and sum(x*y for x,y in zip(q,prev))<0:
       for i in range(4):keys[i][j].co.y*=-1
       q=[-x for x in q]
      prev=q
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.co.x*=4;k.handle_left.x*=4;k.handle_right.x*=4
 a.frame_start*=4;a.frame_end*=4
sc.render.fps=120
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];sc.frame_set(0)
for o in bpy.data.objects:o.select_set(o in objects)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(V/'pilot.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
assert set(clips)=={'Standing','Walking','Running','Attack','Cast','Hit','Fidget','Death','Dead'}
manifest={'revision':'m420_motion_v1','model':'pilot.glb','default_clip':'Standing','default_model':'pilot','models':[{'id':'pilot','label':'Equipped motion review','url':'pilot.glb','revision':'m420_motion_v1','sha256':hashlib.sha256((V/'pilot.glb').read_bytes()).hexdigest()}],'clips':clips,'issues':[],'feedback':'feedback.json'}
(V/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
