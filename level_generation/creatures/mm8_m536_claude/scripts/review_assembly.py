import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_bar1_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/assembled.blend'));sc=common.setup_render();rig=bpy.data.objects['Rig'];sc.view_settings.view_transform='Standard';sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.12,.12,.12,1);sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6
for name,loc,power,size in [('Key',(3,-4,5),600,5),('Fill',(-3,-2,3),350,4),('Rim',(1,3,4),450,3)]:
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;o=bpy.data.objects.new(name,data);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1.8))-o.location).to_track_quat('-Z','Y').to_euler()
for role,frame in [('Standing',1),('Attack',31),('Cast',28),('Death',13),('Dead',1)]:
 rig.animation_data.action=bpy.data.actions[role];sc.frame_set(frame);common.render_views(str(P/'review'/f'assembled_{role}'),1.6,3.6,views=('front','three_quarter'),resolution=(600,800))
