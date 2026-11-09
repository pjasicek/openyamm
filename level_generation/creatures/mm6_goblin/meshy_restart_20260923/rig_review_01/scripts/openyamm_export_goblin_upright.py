import bpy,json,traceback,math
from pathlib import Path
from mathutils import Vector
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923');OUT=ROOT/'rig_review_01';work=bpy.data.scenes['Goblin - Posture Alignment v2'];oldarm=work.objects['MM6_Goblin_Upright_Rig'];oldmesh=work.objects['MM6_Goblin_Upright_10577']
s=bpy.data.scenes.new('Goblin - Upright Rig Review');bpy.context.window.scene=s;s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.device='CPU';s.cycles.use_denoising=True;s.world=work.world;s.view_settings.view_transform='AgX';s.render.resolution_x=850;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.fps=24
arm=oldarm.copy();arm.data=oldarm.data.copy();arm.name='MM6_Goblin_Upright_Review_Rig';s.collection.objects.link(arm);arm.animation_data_clear();arm.animation_data_create()
mesh=oldmesh.copy();mesh.data=oldmesh.data.copy();mesh.name='MM6_Goblin_10577';s.collection.objects.link(mesh);mesh.hide_render=False;mesh.hide_set(False);mat=oldmesh.matrix_world.copy();mesh.parent=arm;mesh.matrix_world=mat
for m in mesh.modifiers:
 if m.type=='ARMATURE':m.object=arm
for o in work.objects:
 if o.type in ['CAMERA','LIGHT']:
  cp=o.copy();cp.data=o.data.copy();s.collection.objects.link(cp)
  if cp.type=='CAMERA':s.camera=cp
acts=[];continuity_flips=0
for key in ['Idle_3','Walking','Running','Right_Hand_Sword_Slash','restpose']:
 a=bpy.data.actions['Goblin_Upright_'+key];acts.append(a)
 for layer in a.layers:
  for strip in layer.strips:
   bag=strip.channelbag(a.slots[0]);curves=list(bag.fcurves) if bag else []
   for fc in curves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
   paths={fc.data_path for fc in curves if fc.data_path.endswith('rotation_quaternion')}
   for path in paths:
    group=sorted([fc for fc in curves if fc.data_path==path],key=lambda fc:fc.array_index);prev=None
    if len(group)!=4:continue
    for i in range(len(group[0].keyframe_points)):
     q=[fc.keyframe_points[i].co.y for fc in group]
     if prev is not None and sum(x*y for x,y in zip(prev,q))<0:
      q=[-x for x in q];continuity_flips+=1
      for fc,x in zip(group,q):fc.keyframe_points[i].co.y=x
     prev=q
 track=arm.animation_data.nla_tracks.new();track.name=key;strip=track.strips.new(key,int(a.frame_range[0]),a);strip.action_slot=a.slots[0];track.mute=True
arm.animation_data.action=acts[0];arm.animation_data.action_slot=acts[0].slots[0];s.frame_start=int(acts[0].frame_range[0]);s.frame_end=int(acts[0].frame_range[1]);s.frame_set(61)
report={'triangles':sum(len(p.vertices)-2 for p in mesh.data.polygons),'bones':len(arm.data.bones),'actions':[a.name for a in acts],'quaternion_sign_continuity_fixes':continuity_flips,'status':'Local rig repair candidate; original-action recreation, grip/fingers, materials and production acceptance remain.'}

def run():
 try:
  bpy.context.window.scene=s;bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=arm
  bpy.ops.export_scene.gltf(filepath=str(OUT/'mm6_goblin_10577_rig_upright_v2.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=True,export_animation_mode='ACTIONS',export_anim_single_armature=False,export_force_sampling=True,export_tangents=True)
  for area in bpy.context.screen.areas:
   if area.type=='VIEW_3D':
    sp=area.spaces.active;sp.shading.type='MATERIAL';sp.region_3d.view_location=(0,0,.85);sp.region_3d.view_distance=2.5;sp.region_3d.view_rotation=Vector((0,-4,0)).to_track_quat('Z','Y');sp.region_3d.view_perspective='ORTHO'
  bpy.data.libraries.write(str(OUT/'mm6_goblin_rig_upright_v2.blend'),{s},fake_user=True,compress=True);(OUT/'upright_export_report.json').write_text(json.dumps(report,indent=2));(OUT/'upright_export_done.txt').write_text('complete')
 except Exception:(OUT/'upright_export_error.txt').write_text(traceback.format_exc())
 return None
bpy.app.timers.register(run,first_interval=.1);print('Exporting repaired skeleton, original geometry, and five animation clips.')
