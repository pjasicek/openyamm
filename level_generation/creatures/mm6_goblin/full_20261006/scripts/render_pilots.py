"""Fixed native-scale pilot and close deformation checks. No shared GUI scene."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/full_20261006')
bpy.ops.wm.open_mainfile(filepath=str(OUT/'work/native_pilots_v1.blend'))
scene=bpy.context.scene;arm=bpy.data.objects['Goblin_Rig'];scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
scene.render.resolution_x=710;scene.render.resolution_y=578;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Pilot neutral lighting');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.17,.17,.17,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
scene.view_settings.view_transform='AgX';scene.view_settings.look='None'
center=Vector((0,0,1.65*289/256/2))
for name,pos,power,size in [('key',(3,-4,4),500,4),('fill',(-4,-2,2),240,4),('rim',(2,4,3),280,3)]:
    light=bpy.data.lights.new(name,'AREA');light.energy=power;light.size=size;obj=bpy.data.objects.new(name,light);scene.collection.objects.link(obj);obj.location=Vector(pos);obj.rotation_euler=(center-obj.location).to_track_quat('-Z','Y').to_euler()
camera=bpy.data.objects.new('Fixed native camera',bpy.data.cameras.new('Fixed native camera'));scene.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=1.65*355/256
clay=bpy.data.materials.new('Pilot clay');clay.use_nodes=True;clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.25,.28,.25,1);clay.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.8;scene.view_layers[0].material_override=clay
directory=OUT/'review/pilots_v6';directory.mkdir(parents=True,exist_ok=True)
views={'front':(0,-5,0),'right':(-5,0,0),'back':(0,5,0),'quarter':(-3,-4,0),'rear_quarter':(-3,4,0)}
tests=[('Standing',1,'front'),('Standing',1,'right'),('Attack',7,'front'),('Attack',13,'front'),('Attack',25,'front'),('Walk',7,'right')]
for clip,frame,view in tests:
    a=bpy.data.actions[clip];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];scene.frame_set(frame)
    camera.location=center+Vector(views[view]);camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(directory/f'{clip}_{frame:02d}_{view}.png');bpy.ops.render.render(write_still=True)
arm.animation_data.action=bpy.data.actions['Standing'];scene.frame_set(1)
scene.render.resolution_x=640;scene.render.resolution_y=640;camera.data.ortho_scale=.38
for side in ('Right',):
    wrist=arm.pose.bones[side+'Hand'].head.copy();center=wrist+Vector((0,-.015,-.045))
    for view,offset in [('front',(0,-2,0)),('quarter',(-2,-2,.6)),('back',(0,2,0))]:
        camera.location=center+Vector(offset);camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(directory/f'hand_{side}_{view}.png');bpy.ops.render.render(write_still=True)
center=arm.pose.bones['Head'].head+Vector((0,-.055,.11));camera.data.ortho_scale=.56
for view,offset in [('front',(0,-2,0)),('right',(-2,0,0))]:
    camera.location=center+Vector(offset);camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(directory/f'head_{view}.png');bpy.ops.render.render(write_still=True)
(directory/'camera.json').write_text(json.dumps({'canvas_px':[710,578],'native_canvas_px':[355,289],'ortho_height_m':1.65*289/256,'scale_m_per_source_pixel':1.65/256,'common_target':[0,0,1.65*289/256/2],'review_status':'renders_need_agent_review'},indent=2)+'\n')
