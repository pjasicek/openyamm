"""Accepted/reduced staff under identical light, plus eight full-actor views at every switch size."""
import bpy,sys,json,math,runpy
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];R=P/'review/round4';sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'source/mm6_jak1_staff.blend'))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
scene.world=bpy.data.worlds.new('Neutral staff review');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.18,.18,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.6
for name,pos,power,size in [('Key',(-1.5,-2,2),150,2),('Fill',(1.5,-1,0),65,2),('Rim',(.5,1.5,1),80,1.5)]:
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=pos;obj.rotation_euler=(Vector((0,0,.1))-obj.location).to_track_quat('-Z','Y').to_euler()
for mat in bpy.data.materials:
 if not mat.node_tree:continue
 bs=mat.node_tree.nodes.get('Principled BSDF')
 if bs:
  for link in list(bs.inputs['Metallic'].links):mat.node_tree.links.remove(link)
  bs.inputs['Metallic'].default_value=0
for key,name in [('accepted','AcceptedStaff'),('reduced','Staff')]:
 for obj in scene.objects:
  if obj.type=='MESH':obj.hide_render=obj.name!=name;obj.hide_set(False)
 for label,center,scale,res in [('ingame',(.05,0,-.174),1.8840271218214184*800/700,(180,800)),('hook',(.055,0,.575),.49,(480,700)),('grip',(0,0,.145),.57,(350,700))]:
  for view,direction in [('front',(0,-1,0)),('quarter',(.7,-1,.1))]:
   d=Vector(direction).normalized();c=Vector(center);cam=common.ortho_camera('ReviewCamera',c+d*3,(0,0,0),scale);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');scene.camera=cam;scene.render.resolution_x,scene.render.resolution_y=res;scene.render.filepath=str(R/f'{key}_{label}_{view}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
height=1.8840271218214184
for level,pixels in enumerate([700,550,220,88]):
 for key in ['accepted','reduced']:
  bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/f'work/round4/{key}_lod{level}.glb'))
  rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');ac=bpy.data.actions['Standing'];rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0];bpy.context.scene.frame_set(0)
  for mat in bpy.data.materials:
   if not mat.node_tree:continue
   bs=mat.node_tree.nodes.get('Principled BSDF')
   if not bs or not bs.inputs['Base Color'].links:continue
   node=bs.inputs['Base Color'].links[0].from_node
   if mat.name.startswith('Jackalman'):
    tag='JackalmanHead_A'if mat.name.startswith('JackalmanHead')else'Jackalman_A';node.image=bpy.data.images.load(str(P/f'work/tier_jak1_a_{tag}.png'),check_existing=True)
   mat.node_tree.nodes.active=node
  scene=bpy.context.scene;common.workbench_clay(scene,True);scene.render.film_transparent=True;scene.render.resolution_x=scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.view_settings.view_transform='Standard';scene.display.render_aa='16';center=Vector((0,0,height/2+.003))
  for i in range(8):
   a=i*math.pi/4;d=Vector((math.sin(a),-math.cos(a),.05)).normalized();cam=common.ortho_camera('MetricCamera',center+d*6,(0,0,0),height*1000/pixels);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');scene.camera=cam;scene.render.filepath=str(R/f'{key}_lod{level}_view{i}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
runpy.run_path(str(P/'scripts/render_final.py'),run_name='__main__')
