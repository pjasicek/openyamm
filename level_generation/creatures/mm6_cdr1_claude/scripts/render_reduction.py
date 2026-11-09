import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];OUT=P/'review/reduction';step=json.loads((OUT/'next_step.json').read_text())['step'];label=f'step_{step:02d}';bpy.ops.wm.open_mainfile(filepath=str(OUT/f'{label}.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
sc.render.engine='CYCLES';sc.cycles.samples=8;sc.cycles.device='CPU';sc.render.resolution_x=1000;sc.render.resolution_y=750;sc.render.resolution_percentage=100;sc.world=bpy.data.worlds.new('Studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.20,.20,.20,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.8
for name,loc,energy,size in [('Key',(2,-3,4),320,3),('Fill',(-3,-1,2),180,3),('Rim',(0,3,3),280,2)]:
 l=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'));sc.collection.objects.link(l);l.location=loc;l.data.energy=energy;l.data.shape='DISK';l.data.size=size;l.rotation_euler=(Vector((0,-.5,.8))-l.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
for name,clip,frame,offset,target,size in [('whole','Standing',0,(4,-6,2),(0,-.4,.8),3.7),('front','Standing',13,(0,-6,0),(0,-.4,.7),3.7),('head','Standing',0,(2,-5,1),(0,-1.2,1.55),1.1),('attack','Attack',16,(4,-6,2),(0,-.4,.8),3.7)]:
 rig.animation_data.action=bpy.data.actions[clip];sc.frame_set(frame);target=Vector(target);cam.location=target+Vector(offset);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=size;sc.render.filepath=str(OUT/f'{label}_{name}.png');bpy.ops.render.render(write_still=True)
