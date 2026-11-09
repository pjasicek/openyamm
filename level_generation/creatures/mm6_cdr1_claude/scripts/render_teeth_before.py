import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_cdr1.blend'));sc=bpy.context.scene;rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
sc.render.engine='CYCLES';sc.cycles.samples=12;sc.cycles.device='CPU';sc.render.resolution_x=1000;sc.render.resolution_y=750;sc.render.resolution_percentage=100;sc.world=bpy.data.worlds.new('Studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.20,.20,.20,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.8
for name,loc,energy,size in [('Key',(2,-3,4),320,3),('Fill',(-3,-1,2),180,3),('Rim',(0,3,3),280,2)]:
 l=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'));sc.collection.objects.link(l);l.location=loc;l.data.energy=energy;l.data.shape='DISK';l.data.size=size;l.rotation_euler=(Vector((0,-.5,.8))-l.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
for name,offset in [('side',(5,0,0)),('quarter',(4,-3,1.5)),('lower',(3,-4,4)),('upper',(3,-4,-4))]:
 target=Vector((0,-1.44,.90));cam.location=target+Vector(offset);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.27;sc.render.filepath=str(P/'review'/f'teeth_before_{name}.png');bpy.ops.render.render(write_still=True)
