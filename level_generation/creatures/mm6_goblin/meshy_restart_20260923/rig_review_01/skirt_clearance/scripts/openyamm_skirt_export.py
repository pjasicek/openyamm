import bpy,json,traceback
from pathlib import Path
from mathutils import Vector
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/rig_review_01/skirt_clearance');s=bpy.data.scenes['Goblin - Skirt Clearance v3'];bpy.context.window.scene=s;arm=s.objects['Goblin_SkirtClearance_Rig'];mesh=s.objects['Goblin_SkirtClearance_10577'];a=bpy.data.actions['Goblin_Skirt_Walking'];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];s.frame_start=1;s.frame_end=26;s.frame_set(15);bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=mesh
bpy.ops.export_scene.gltf(filepath=str(OUT/'mm6_goblin_10577_skirt_v3.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=True,export_animation_mode='ACTIONS',export_anim_single_armature=False,export_force_sampling=True,export_tangents=True)
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':
  sp=area.spaces.active;sp.shading.type='MATERIAL';sp.overlay.show_overlays=False;sp.region_3d.view_location=(0,0,.85);sp.region_3d.view_distance=2.6;sp.region_3d.view_rotation=Vector((0,-4,0)).to_track_quat('Z','Y');sp.region_3d.view_perspective='ORTHO'
bpy.data.libraries.write(str(OUT/'mm6_goblin_skirt_v3.blend'),{s},fake_user=True,compress=True)
v=bpy.data.scenes.new('Goblin - Skirt Export Check');v.render.fps=24;bpy.context.window.scene=v;before=set(bpy.data.actions);bpy.ops.import_scene.gltf(filepath=str(OUT/'mm6_goblin_10577_skirt_v3.glb'));acts=[a for a in bpy.data.actions if a not in before];ar=next(o for o in v.objects if o.type=='ARMATURE');me=next(o for o in v.objects if o.type=='MESH');report={'triangles':sum(len(p.vertices)-2 for p in me.data.polygons),'bones':len(ar.data.bones),'animations':[a.name for a in acts]};assert report['triangles']==10577 and report['bones']==45 and len(acts)==5
for tr in ar.animation_data.nla_tracks:tr.mute=True
worst=0
for aa in acts:
 key=next(k for k in ['Idle_3','Walking','Running','Right_Hand_Sword_Slash','restpose'] if 'Goblin_Skirt_'+k in aa.name);orig=bpy.data.actions['Goblin_Skirt_'+key];arm.animation_data.action=orig;arm.animation_data.action_slot=orig.slots[0];ar.animation_data.action=aa;ar.animation_data.action_slot=aa.slots[0]
 for i in range(9):
  f=orig.frame_range[0]+(orig.frame_range[1]-orig.frame_range[0])*i/8;bpy.context.window.scene=s;s.frame_set(int(f),subframe=f-int(f));points={p.name:arm.matrix_world@p.head for p in arm.pose.bones};bpy.context.window.scene=v;v.frame_set(int(f),subframe=f-int(f))
  for p in ar.pose.bones:worst=max(worst,((ar.matrix_world@p.head)-points[p.name]).length)
report['max_joint_roundtrip_distance_m']=worst;assert worst<.00002;(OUT/'export_report.json').write_text(json.dumps(report,indent=2))
v.render.engine='CYCLES';v.cycles.samples=12;v.cycles.device='CPU';v.cycles.use_denoising=True;v.world=s.world;v.view_settings.view_transform='AgX';v.render.resolution_x=850;v.render.resolution_y=1000;v.render.resolution_percentage=100;v.render.image_settings.file_format='PNG'
for o in s.objects:
 if o.type in ['CAMERA','LIGHT']:
  cp=o.copy();cp.data=o.data.copy();v.collection.objects.link(cp)
  if cp.type=='CAMERA':v.camera=cp
jobs=[('front',0,15),('quarter',.55,15),('opposite',-.55,3)]
def step():
 try:
  if not jobs:
   bpy.context.window.scene=s;a=bpy.data.actions['Goblin_Skirt_Walking'];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];s.frame_set(15);(OUT/'export_done.txt').write_text('complete');return None
  name,angle,f=jobs.pop(0);bpy.context.window.scene=v;a=next(a for a in acts if 'Goblin_Skirt_Walking' in a.name);ar.animation_data.action=a;ar.animation_data.action_slot=a.slots[0];v.frame_set(f);import math;v.camera.location=(5*math.sin(angle),-5*math.cos(angle),.85);v.camera.rotation_euler=(Vector((0,0,.85))-v.camera.location).to_track_quat('-Z','Y').to_euler();v.render.filepath=str(OUT/('export_'+name+'.png'));bpy.ops.render.render(write_still=True);return .1
 except Exception:(OUT/'export_error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.1);print(json.dumps(report))
