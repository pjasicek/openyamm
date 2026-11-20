import bpy,math
from pathlib import Path
from mathutils import Vector
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/full_20261006');bpy.ops.wm.open_mainfile(filepath=str(OUT/'work/reimported_delivery_v1.blend'))
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');action=bpy.data.actions['Standing'];arm.animation_data.action=action;arm.animation_data.action_slot=action.slots[0];bpy.context.scene.frame_set(1)
scene=bpy.context.scene;scene.view_layers[0].material_override=None;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.resolution_x=768;scene.render.resolution_y=768;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('UV neutral');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.15,.15,1)
for p,power in [((2,-4,4),500),((-3,-2,2),240),((3,4,3),300)]:
 data=bpy.data.lights.new('UV light','AREA');data.energy=power;data.size=4;o=bpy.data.objects.new(data.name,data);scene.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector((0,0,.85))-o.location).to_track_quat('-Z','Y').to_euler()
camera=bpy.data.objects.new('UV camera',bpy.data.cameras.new('UV camera'));scene.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO'
folder=OUT/'review/export_materials';folder.mkdir(exist_ok=True)
checks=[('Standing',0,'front',(0,0,.83),(0,-5,0),1.85),('Standing',0,'back',(0,0,.83),(0,5,0),1.85),('Standing',0,'right',(0,0,.83),(-5,0,0),1.85),('Attack',.25,'raised',(0,0,1.05),(0,-5,0),1.85),('Attack',.375,'strike',(0,0,.93),(0,-5,0),2.05),('Attack',.25,'grip',None,(0,-5,0),.80),('Hit',.45,'guard',(0,-.1,1.2),(0,-5,0),1.20),('Hit',.60,'release',(0,0,.95),(-3,-4,0),1.85),('Death',.375,'prone',(.08,.40,.30),(-3,-4,3),2.55),('Death',.375,'palm',None,(0,-5,2),.52)]
checks += [('Death',.125,'fold_front',(0,0,.83),(0,-5,0),1.85),('Death',.125,'fold_right',(0,0,.83),(-5,0,0),1.85),('Death',.125,'fold_grip',(.01,-.23,.69),(0,-5,0),.65)]
for clip,t,name,center,offset,scale in checks:
 a=bpy.data.actions[clip];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];frame=a.frame_range[0]+t*192;scene.frame_set(int(frame),subframe=frame-int(frame))
 if center is None:center=tuple(arm.pose.bones['RightHand' if clip=='Attack' else 'LeftHand'].head)
 c=Vector(center);camera.location=c+Vector(offset);camera.rotation_euler=(c-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale;scene.render.filepath=str(folder/f'{clip}_{name}.png');bpy.ops.render.render(write_still=True)
