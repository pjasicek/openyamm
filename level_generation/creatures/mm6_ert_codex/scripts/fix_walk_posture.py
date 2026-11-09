"""Remove the foreign walk's fixed shoulder shrug and spinal hunch, retaining cyclic motion."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Quaternion
P=Path(__file__).resolve().parents[1];out=P/'review/walk_posture_v2'
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()));import common
bpy.ops.wm.open_mainfile(filepath=str(out/'before/export/mm6_ert.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['EarthElemental'];scene=bpy.context.scene
walk=bpy.data.actions['Walking'];rig.animation_data.action=walk;rig.animation_data.action_slot=walk.slots[0]
# Remove the static posture from the complete shoulder/spine/head chain, avoiding a compensating neck kink.
names=['B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head','B_L_Clavicle','B_R_Clavicle']
frames=range(round(walk.frame_range[1])+1);old=[]
for f in frames:
 scene.frame_set(f);old.append({n:rig.pose.bones[n].rotation_quaternion.copy() for n in names})
means={}
for n in names:
 q=np.array([list(row[n]) for row in old[:-1]]);_,vec=np.linalg.eigh(q.T@q);means[n]=Quaternion(vec[:,-1]);means[n].normalize()
rig.animation_data.action=None
previous={}
for f,row in zip(frames,old):
 for n in names:
  q=means[n].inverted()@row[n]
  if n in previous and q.dot(previous[n])<0:q.negate()
  previous[n]=q.copy();pb=rig.pose.bones[n];pb.rotation_quaternion=q
  rig.animation_data.action=walk;rig.animation_data.action_slot=walk.slots[0];pb.keyframe_insert('rotation_quaternion',frame=f,group=n);rig.animation_data.action=None
for layer in walk.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
rig.animation_data.action=walk;rig.animation_data.action_slot=walk.slots[0];scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'candidate.blend'))
for obj in bpy.data.objects:obj.select_set(obj in (rig,body))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(out/'candidate.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
common.workbench_clay(scene);scene.display.shading.color_type='OBJECT';body.color=(.6,.6,.6,1)
for i,t in enumerate([0,.35,.7,1.05,43/30]):
 scene.frame_set(int(t*60),subframe=t*60%1);common.render_views(str(out/f'candidate_{i}'),1.2,2.75,views=('front','left','three_quarter'),resolution=(450,550))
(out/'correction.json').write_text(json.dumps({'bones':names,'removed_mean_angles_deg':{n:math.degrees(q.angle if q.angle<math.pi else 2*math.pi-q.angle) for n,q in means.items()},'duration':walk.frame_range[1]/60},indent=2))
