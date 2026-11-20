import bpy,json,traceback
from pathlib import Path
from mathutils import Vector
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/sword_attack_01');src=bpy.data.scenes['Goblin - Sword and Native Attack'];bpy.context.window.scene=src;r=src.objects['Goblin_Combat_Rig'];m=src.objects['Goblin_Combat_Body'];a=bpy.data.actions['MM6_Goblin_Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];src.frame_set(1);dg=bpy.context.evaluated_depsgraph_get();H=r.pose.bones['mixamorig:RightHand'].matrix.copy();handgroups={g.index for g in m.vertex_groups if g.name=='mixamorig:RightHand' or g.name.startswith('Finger.R.')};ids={v.index for v in m.data.vertices if sum(g.weight for g in v.groups if g.group in handgroups)>.4};ev=m.evaluated_get(dg);faces=[list(p.vertices) for p in m.data.polygons if all(i in ids for i in p.vertices)];used=sorted(set(i for f in faces for i in f));mp={i:j for j,i in enumerate(used)};s=bpy.data.scenes.new('Goblin - Grip Closeup');bpy.context.window.scene=s;s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.device='CPU';s.cycles.use_denoising=True;s.world=src.world;s.view_settings.view_transform='AgX';s.render.resolution_x=700;s.render.resolution_y=700;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';me=bpy.data.meshes.new('Grip posed surface');me.from_pydata([ev.matrix_world@ev.data.vertices[i].co for i in used],[],[[mp[i] for i in f] for f in faces]);me.update();o=bpy.data.objects.new('Grip posed surface',me);s.collection.objects.link(o);mat=bpy.data.materials.new('Grip review neutral');mat.diffuse_color=(.45,.45,.45,1);mat.use_nodes=True;mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.45,.45,.45,1);mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.65;me.materials.append(mat)
for p in me.polygons:p.use_smooth=True
for ob in src.objects:
 if ob.type=='MESH' and ob.get('goblin_weapon'):
  e=ob.evaluated_get(dg);mesh=bpy.data.meshes.new_from_object(e,depsgraph=dg);cp=bpy.data.objects.new(ob.name+' posed',mesh);s.collection.objects.link(cp);cp.matrix_world=e.matrix_world
 if ob.type in ['CAMERA','LIGHT']:
  cp=ob.copy();cp.data=ob.data.copy();s.collection.objects.link(cp)
  if cp.type=='CAMERA':s.camera=cp
center=H@Vector((.025,.09,0));jobs=[('grip_palm',(2,.5,.1)),('grip_side',(.2,.1,2)),('grip_back',(-2,.1,.1))]
def step():
 try:
  bpy.context.window.scene=s
  if not jobs:bpy.context.window.scene=src;(OUT/'grip_review_done.txt').write_text('complete');return None
  name,vec=jobs.pop(0);s.camera.location=center+H.to_quaternion()@Vector(vec);s.camera.rotation_euler=(center-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=.32;s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True);return .1
 except Exception:(OUT/'grip_review_error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.1);print('Rendering unobstructed grip views')
