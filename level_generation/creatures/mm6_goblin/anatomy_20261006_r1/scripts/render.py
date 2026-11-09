import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin')
OUT=ROOT/'anatomy_20261006_r1'
for revision,path in [('before',ROOT/'review_20261006/goblin_review.blend'),('after',OUT/'goblin_anatomy.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(path))
 arm=bpy.data.objects['Goblin_Rig'];scene=bpy.context.scene
 scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100
 scene.world=bpy.data.worlds.new('Head neutral');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.15,.15,1)
 for p,power in [((2,-4,4),500),((-3,-2,2),240),((3,4,3),300)]:
  light=bpy.data.lights.new('Head light','AREA');light.energy=power;light.size=4;o=bpy.data.objects.new(light.name,light);scene.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector((0,0,1.45))-o.location).to_track_quat('-Z','Y').to_euler()
 camera=bpy.data.objects.new('Head camera',bpy.data.cameras.new('Head camera'));scene.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO'
 clay=bpy.data.materials.new('Head neutral clay');clay.use_nodes=True;bsdf=clay.node_tree.nodes['Principled BSDF'];bsdf.inputs['Base Color'].default_value=(.35,.38,.32,1);bsdf.inputs['Roughness'].default_value=.8
 entries=[('Standing',0,'front',(0,-5,0),False),('Standing',0,'right',(-5,0,0),False),('Standing',0,'quarter',(-3,-4,0),False),('Standing',0,'front_clay',(0,-5,0),True),('Standing',0,'right_clay',(-5,0,0),True)]
 if revision=='after':entries += [('Meshy_Walk',.50,'walk_right',(-5,0,0),False),('Meshy_Run',.31,'run_right',(-5,0,0),False),('Attack',.25,'attack',(0,-5,0),False),('Hit',.375,'hit',(-3,-4,0),False),('Corpse',0,'corpse',(-3,-4,2),False)]
 for clip,time,name,offset,use_clay in entries:
  a=bpy.data.actions[clip];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];frame=1+time*192;scene.frame_set(int(frame),subframe=frame-int(frame))
  center=Vector((.08,.01,1.465)) if clip!='Corpse' else arm.pose.bones['Head'].head+Vector((0,0,.08))
  if name in ['attack','hit']:center=arm.pose.bones['Head'].head+Vector((0,0,.13))
  camera.location=center+Vector(offset);camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=.59 if clip!='Corpse' else .80
  scene.view_layers[0].material_override=clay if use_clay else None
  scene.render.filepath=str(OUT/'review'/f'{revision}_{name}.png');bpy.ops.render.render(write_still=True)
 print('Rendered',revision,len(entries),'fixed-camera head checks.',flush=True)
