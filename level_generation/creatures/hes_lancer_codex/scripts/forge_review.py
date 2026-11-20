"""Offline concept-coverage inspection of authoring poses."""
import bpy,sys,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];src,clip,frame=a[:3];view=a[3] if len(a)>3 else 'quarter'
bpy.ops.wm.open_mainfile(filepath=str(P/'work'/src))
sc=bpy.context.scene;rig=bpy.data.objects['Rig'];rig.animation_data_create()
act=bpy.data.actions[clip];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];sc.frame_set(int(float(frame)),subframe=float(frame)%1)
for o in bpy.data.objects:
    if o.type=='MESH' and o.name not in (['Body','Thunder_Maul'] if clip.startswith('Forge_') else ['Body','Rifle']) and not o.name.startswith(('Arm_','Apron_')):o.hide_render=True
for name,col,em in [('HKR_Glow',(1,.20,.015,1),1)]:
    m=bpy.data.materials.get(name)
    if m:
        m.use_nodes=True;nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
        for link in list(nt.links):nt.links.remove(link)
        nt.links.new(bs.outputs['BSDF'],nt.nodes.get('Material Output').inputs['Surface'])
        bs.inputs['Base Color'].default_value=(.08,.008,.001,1) if name=='HKR_Glow' else col;bs.inputs['Roughness'].default_value=.5
        bs.inputs['Emission Color'].default_value=col;bs.inputs['Emission Strength'].default_value=em
m=bpy.data.materials['HKR_Plate'];m.use_nodes=True;nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
for node in list(nt.nodes):
 if node.type in ('TEX_IMAGE','NORMAL_MAP','SEPARATE_COLOR'):nt.nodes.remove(node)
for suffix,space,socket in [('basecolor','sRGB','Base Color'),('normal','Non-Color','Normal'),('metal_rough','Non-Color','Roughness')]:
 node=nt.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(P/f'textures/forge_armour_{suffix}.png'));node.image.colorspace_settings.name=space
 if suffix=='normal':
  cv=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(node.outputs['Color'],cv.inputs['Color']);nt.links.new(cv.outputs['Normal'],bs.inputs[socket])
 elif suffix=='metal_rough':
  cv=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(node.outputs['Color'],cv.inputs['Color']);nt.links.new(cv.outputs['Green'],bs.inputs['Roughness']);nt.links.new(cv.outputs['Blue'],bs.inputs['Metallic'])
 else:nt.links.new(node.outputs['Color'],bs.inputs[socket])
sc.render.engine='CYCLES' ;sc.cycles.samples=16
sc.render.resolution_x=900;sc.render.resolution_y=900;sc.render.resolution_percentage=100
sc.world=bpy.data.worlds.new('Review');sc.world.use_nodes=True
sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.12,.12,1)
sc.world.node_tree.nodes['Background'].inputs[1].default_value=.6
for name,pos,energy,size in [('key',(2,-4,5),500,4),('fill',(-3,-2,3),350,3)]:
    light=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'));sc.collection.objects.link(light)
    light.location=pos;light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler();light.data.energy=energy;light.data.shape='DISK';light.data.size=size
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam
cam.location=(3,-5,2.5);target=Vector((-.1,-.3,.95));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
if view in ('front','back'):
    transform=rig.pose.bones['B_Spine2'].matrix @ rig.data.bones['B_Spine2'].matrix_local.inverted()
    front=transform.to_3x3() @ Vector((0,-1,0));front.z=0;front.normalize()
    cam.location=target+front*(5 if view=='front' else -5)+Vector((0,0,.6));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
if view=='side':
    target=Vector((0,-.65,1.15));cam.location=target+Vector((5,0,.3));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=3.5
sc.view_settings.view_transform='Standard'
sc.render.filepath=str(P/'review'/f'forge_concept_{clip}_{frame}_{view}.png');bpy.ops.render.render(write_still=True)

import os
sys.stdout.flush();os._exit(0)
