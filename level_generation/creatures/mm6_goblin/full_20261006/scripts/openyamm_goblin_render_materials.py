import bpy,math
from pathlib import Path
from mathutils import Vector
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/full_20261006');bpy.ops.wm.open_mainfile(filepath=str(OUT/'work/native_textured_v1.blend'))
arm=bpy.data.objects['Goblin_Rig'];action=bpy.data.actions['Standing'];arm.animation_data.action=action;arm.animation_data.action_slot=action.slots[0];bpy.context.scene.frame_set(1)
scene=bpy.context.scene;scene.view_layers[0].material_override=None;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.resolution_x=768;scene.render.resolution_y=768;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('UV neutral');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.15,.15,1)
for p,power in [((2,-4,4),500),((-3,-2,2),240),((3,4,3),300)]:
 data=bpy.data.lights.new('UV light','AREA');data.energy=power;data.size=4;o=bpy.data.objects.new(data.name,data);scene.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector((0,0,.85))-o.location).to_track_quat('-Z','Y').to_euler()
camera=bpy.data.objects.new('UV camera',bpy.data.cameras.new('UV camera'));scene.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO'
folder=OUT/'review/materials_v2';folder.mkdir(exist_ok=True)
for name,center,offset,scale in [('front',(0,0,.83),(0,-5,0),1.85),('right',(0,0,.83),(-5,0,0),1.85),('back',(0,0,.83),(0,5,0),1.85),('quarter',(0,0,.83),(-3,-4,0),1.85),('head',(0,-.01,1.48),(0,-5,0),.65),('hand',tuple(arm.pose.bones['LeftHand'].head+Vector((.025,-.04,-.05))),(0,-5,0),.42)]:
 c=Vector(center);camera.location=c+Vector(offset);camera.rotation_euler=(c-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale;scene.render.filepath=str(folder/(name+'.png'));bpy.ops.render.render(write_still=True)
