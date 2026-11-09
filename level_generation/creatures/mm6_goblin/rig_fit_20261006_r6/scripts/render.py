import bpy
from pathlib import Path
from mathutils import Vector
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin');OUT=ROOT/'rig_fit_20261006_r6'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'goblin_r6.blend'))
arm=bpy.data.objects['Goblin_Rig'];scene=bpy.context.scene
# Fixed-camera shoulder and skirt review.
a=bpy.data.actions['Standing'];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];scene.frame_set(1)
scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.resolution_x=800;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Shoulder neutral');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.18,.18,1)
for pos,power in [((2,4,4),500),((-3,2,2),300),((1,-3,3),180)]:
 light=bpy.data.lights.new('Shoulder light','AREA');light.energy=power;light.size=4;o=bpy.data.objects.new(light.name,light);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((.08,.04,1.12))-o.location).to_track_quat('-Z','Y').to_euler()
camera=bpy.data.objects.new('Shoulder camera',bpy.data.cameras.new('Shoulder camera'));scene.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO'
for name,rest_pose,center,offset,scale in [('after_back',False,(.08,.04,1.17),(0,4,.2),.8),('after_front',False,(.08,.04,1.17),(0,-4,.2),.8),('after_skirt_back',False,(.08,.025,.74),(0,4,-1.3),.9),('after_skirt_front',False,(.08,.025,.74),(0,-4,-1.3),.9),('after_skirt_right',False,(.08,.025,.74),(-4,0,0),.70)]:
 arm.data.pose_position='REST' if rest_pose else 'POSE';bpy.context.view_layer.update();target=Vector(center);camera.location=target+Vector(offset);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale;scene.render.filepath=str(OUT/'review'/f'{name}.png');bpy.ops.render.render(write_still=True)

for clip,t in [("Meshy_Walk",.5),("Meshy_Run",.31),("Attack",.25),("Hit",.375),("Corpse",0)]:
 a=bpy.data.actions[clip];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];f=1+t*192;scene.frame_set(int(f),subframe=f-int(f));center=(arm.pose.bones["Spine"].head+arm.pose.bones["Spine01"].head)*.5;camera.location=center+Vector((0,4,.3));camera.rotation_euler=(center-camera.location).to_track_quat("-Z","Y").to_euler();camera.data.ortho_scale=.95;scene.render.filepath=str(OUT/"review"/f"after_{clip}_back.png");bpy.ops.render.render(write_still=True)

# Additional skirt views at the previously problematic motion poses.
for clip,t in [('Walk',.4583333333),('Meshy_Walk',.1875),('Meshy_Run',.375),('Death',.2291666667),('Corpse',0)]:
 a=bpy.data.actions[clip];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];f=1+t*192;scene.frame_set(int(f),subframe=f-int(f))
 center=arm.pose.bones['Hips'].head+Vector((0,0,-.09));camera.location=center+Vector((-3,-3,1));camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=.85;scene.render.filepath=str(OUT/'review'/f'after_{clip}_skirt.png');bpy.ops.render.render(write_still=True)
