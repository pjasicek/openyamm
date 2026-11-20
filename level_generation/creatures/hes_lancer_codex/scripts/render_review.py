"""Offline concept-coverage inspection of authoring poses."""
import bpy,sys,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];src,clip,frame=a[:3];view=a[3] if len(a)>3 else 'quarter'
bpy.ops.wm.open_mainfile(filepath=str(P/'work'/src))
sc=bpy.context.scene;rig=bpy.data.objects['Rig'];rig.animation_data_create()
act=bpy.data.actions[clip];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];sc.frame_set(int(frame))
for o in bpy.data.objects:
    if o.type=='MESH' and o.name not in (['Body','Thunder_Maul'] if clip.startswith('Forge_') else ['Body','Rifle']) and not o.name.startswith(('Arm_','Apron_')):o.hide_render=True
for name,col,em in [('HKR_Plate',(.72,.65,.48,1),0),('HKR_Glow',(1,.22,.01,1),1),('HKR_A',(.22,.06,.28,1),0)]:
    m=bpy.data.materials.get(name)
    if m:
        m.use_nodes=True;nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
        for link in list(nt.links):nt.links.remove(link)
        nt.links.new(bs.outputs['BSDF'],nt.nodes.get('Material Output').inputs['Surface'])
        bs.inputs['Base Color'].default_value=col;bs.inputs['Roughness'].default_value=.5
        bs.inputs['Emission Color'].default_value=col;bs.inputs['Emission Strength'].default_value=em
sc.render.engine='CYCLES';sc.cycles.samples=16
sc.render.resolution_x=900;sc.render.resolution_y=900;sc.render.resolution_percentage=100
sc.world=bpy.data.worlds.new('Review');sc.world.use_nodes=True
sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.12,.12,1)
sc.world.node_tree.nodes['Background'].inputs[1].default_value=.6
for name,pos,energy,size in [('key',(2,-4,5),500,4),('fill',(-3,-2,3),350,3)]:
    light=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'));sc.collection.objects.link(light)
    light.location=pos;light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler();light.data.energy=energy;light.data.shape='DISK';light.data.size=size
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam
cam.location=(3,-5,2.5);target=Vector((-.1,-.3,.95));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
if view=='front':
    transform=rig.pose.bones['B_Spine2'].matrix @ rig.data.bones['B_Spine2'].matrix_local.inverted()
    front=transform.to_3x3() @ Vector((0,-1,0));front.z=0;front.normalize()
    cam.location=target+front*5+Vector((0,0,1.1));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=3.3
sc.view_settings.view_transform='Standard'
sc.render.filepath=str(P/'review'/f'review2_{clip}_{frame}_{view}.png');bpy.ops.render.render(write_still=True)
