import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_master.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
sockets={'Socket_Eye_Left': ('B_Head', [0.03319037705659866, -0.11743705719709396, 2.6463775634765625]), 'Socket_Eye_Right': ('B_Head', [-0.03909880295395851, -0.11648157238960266, 2.647841215133667])}
sockets['Socket_Gaze']=('B_Head',(np.array(sockets['Socket_Eye_Left'][1])+sockets['Socket_Eye_Right'][1])*.5)
for sd,label in [('L','Left'),('R','Right')]:
 n='B_'+sd+'_Hand';b=rig.data.bones[n];sockets['Socket_Palm_'+label]=(n,b.head_local+(b.tail_local-b.head_local).normalized()*.065)
for n,(bn,position) in sockets.items():
 obj=bpy.data.objects.new(n,None);sc.collection.objects.link(obj);obj.parent=rig;obj.parent_type='BONE';obj.parent_bone=bn;obj.matrix_world=Matrix.Translation(Vector(position));bpy.context.view_layer.update()
 parent_matrix=rig.matrix_world@rig.pose.bones[bn].matrix@Matrix.Translation((0,rig.data.bones[bn].length,0));obj.matrix_parent_inverse=parent_matrix.inverted();obj.matrix_basis=Matrix.Translation(Vector(position))
selection={'Body','Rig','FlameTail','FlameTail_LOD1','FlameTail_LOD2','FlaskRemains'}|set(sockets)
for o in bpy.data.objects:
 o.select_set(False)
 if o.name in selection:o.hide_set(False);o.hide_viewport=False;o.select_set(True)
assert all(n in bpy.data.objects for n in selection)
bpy.context.view_layer.objects.active=rig;sc.render.fps=30;rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
for im in bpy.data.images:
 if im.source=='FILE':im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm8_m536.blend'))
# 120 Hz retains all 30 Hz source knots and exact fractional native endpoints.
for action in bpy.data.actions:
 for layer in action.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for kp in fc.keyframe_points:
      for point in [kp.co,kp.handle_left,kp.handle_right]:point.x=1+(point.x-1)*4
sc.render.fps=120
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm8_m536_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=False)
report={'bones':len(rig.data.bones),'sockets':{n:{'bone':bn,'rest_position':list(map(float,v))} for n,(bn,v) in sockets.items()},'body_triangles':len(body.data.polygons),'arm_lengths':{sd:[(rig.data.bones['B_'+sd+'_'+n].tail_local-rig.data.bones['B_'+sd+'_'+n].head_local).length for n in ['UpperArm','Forearm']] for sd in ['L','R']},'fitted_joints':'work/joints_final.json','fingers':'work/fingers_fit.json','anatomy':'Legless upper-body source-frame rig; five connectivity-fitted digits per hand, eight tail bones and separate flask.'}
assert report['bones']==55
(P/'review/rig_export.json').write_text(json.dumps(report,indent=2)+'\n')
