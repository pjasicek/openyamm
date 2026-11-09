"""Static material and silhouette review of the exact viewer GLBs, without opening a browser."""
from pathlib import Path
import bpy,json,math
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
for tier in ('a','b','c','boss'):
 bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;bpy.ops.import_scene.gltf(filepath=str(P/f'review/viewer/hes_harrower_{tier}.glb'))
 action=next(a for a in bpy.data.actions if 'standing' in a.name.lower());rig=next(o for o in sc.objects if o.type=='ARMATURE');rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];sc.frame_set(0)
 sc.world=bpy.data.worlds.new('Review world');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.06,.06,.06,1);sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
 for name,pos,power,size in [('Key',(2,-4,5),800,4),('Fill',(-3,-2,2),350,3),('Rim',(1,3,4),650,3)]:
  light=bpy.data.lights.new(name,'AREA');light.energy=power;light.shape='DISK';light.size=size;ob=bpy.data.objects.new(name,light);sc.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector((0,0,1))-ob.location).to_track_quat('-Z','Y').to_euler()
 cd=bpy.data.cameras.new('Review');cam=bpy.data.objects.new('Review',cd);sc.collection.objects.link(cam);sc.camera=cam;cd.type='ORTHO';cd.ortho_scale=2.55
 sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.render.resolution_x=sc.render.resolution_y=1024;sc.render.resolution_percentage=100;sc.render.film_transparent=False;sc.view_settings.view_transform='AgX'
 for name,direction in [('front',(0,-4,1)),('back',(0,4,1))]:
  if name=='back' and tier not in ('a','boss'):continue
  centre=Vector((0,-.1,.93));cam.location=centre+Vector(direction);cam.rotation_euler=(centre-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(P/f'review/r2/material_{tier}_{name}.png');bpy.ops.render.render(write_still=True)
