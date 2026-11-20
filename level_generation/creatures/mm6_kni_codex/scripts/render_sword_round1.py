import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'work/round1/sword_linked_canonical.glb'));scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.world=bpy.data.worlds.new('Neutral studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.09,.09,.09,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
for name,pos,power,size in [('Key',(.0,-1.1,1.5),60,2.0),('Fill',(.7,.8,.8),25,1.5),('Rim',(.3,.1,-1.2),15,1.3)]:
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((.3,0,.06))-o.location).to_track_quat('-Z','Y').to_euler()
for name,direction,centre,scale,rez in [('sword_closeup',(-.22,-1,.36),(.30,0,.065),1.30,(1600,700)),('sword_side',(0,-1,.05),(.30,0,.065),1.30,(1600,700)),('sword_grip_closeup',(-.15,-1,.3),(-.065,0,0),.46,(1100,700))]:
 d=Vector(direction).normalized();c=Vector(centre);cam=common.ortho_camera('ReviewCamera',c+d*3,(0,0,0),scale);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');scene.camera=cam;scene.render.resolution_x,scene.render.resolution_y=rez;scene.render.filepath=str(P/f'review/round1/{name}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round1/sword_review.blend'))
