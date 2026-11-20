"""Portable animated master; PBR body, breath effect and nine authored clips."""
from pathlib import Path
import bpy,bmesh,json
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/uv_reweighted.blend'))
mesh=bpy.data.objects['Unicorn'];rig=bpy.data.objects['Unicorn_Rig'];sc=bpy.context.scene
# Native horn release point and a small breath cloud, both following the animated head.
from mathutils import Vector
import math
rig.animation_data.action=None
for bone in rig.pose.bones:bone.matrix_basis.identity()
bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
for name,point in [('HornTip',(-.009,-.495,.638)),('Breath',(0,-.416,.463))]:
    bone=rig.data.edit_bones.new(name);bone.head=point
    bone.tail=Vector(point)+Vector((0,-.02,0));bone.parent=rig.data.edit_bones['Head']
bpy.ops.object.mode_set(mode='OBJECT')
size=128
image=bpy.data.images.new('UnicornBreath',width=size,height=size,alpha=True)
pixels=[]
for y in range(size):
    for x in range(size):
        r=math.hypot((x+.5-size/2)/(size/2),(y+.5-size/2)/(size/2))
        alpha=.22*max(0,1-r*r)**2
        pixels.extend((.83,.87,.91,alpha))
image.pixels=pixels;image.filepath_raw=str(P/'textures/unicorn_breath.png');image.file_format='PNG';image.save()
verts=[];faces=[]
center=Vector((0,-.432,.463))
for a,b in [(Vector((.7071,.7071,0)),Vector((0,0,1))),
            (Vector((-.7071,.7071,0)),Vector((0,0,1)))]:
    start=len(verts)
    for u,v in [(-1,-1),(1,-1),(1,1),(-1,1)]:verts.append(center+.028*(a*u+b*v))
    faces.extend([(start,start+1,start+2),(start,start+2,start+3)])
data=bpy.data.meshes.new('BreathCloud');data.from_pydata(verts,[],faces);data.update()
cloud=bpy.data.objects.new('BreathCloud',data);sc.collection.objects.link(cloud)
uv=data.uv_layers.new(name='UVMap');coords=[(0,0),(1,0),(1,1),(0,1)]
for polygon in data.polygons:
    for loop in polygon.loop_indices:uv.data[loop].uv=coords[data.loops[loop].vertex_index%4]
cloud.vertex_groups.new(name='Breath').add(list(range(len(verts))),1,'REPLACE')
cloud.parent=rig;mod=cloud.modifiers.new('Armature','ARMATURE');mod.object=rig
mist=bpy.data.materials.new('BreathCloud');mist.use_nodes=True;mist.surface_render_method='BLENDED'
mist.use_backface_culling=False
nodes=mist.node_tree.nodes;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
texnode=nodes.new('ShaderNodeTexImage');texnode.image=image
mist.node_tree.links.new(texnode.outputs['Color'],bs.inputs['Base Color'])
mist.node_tree.links.new(texnode.outputs['Alpha'],bs.inputs['Alpha'])
bs.inputs['Roughness'].default_value=1;data.materials.append(mist)
breath=rig.pose.bones['Breath'];breath.rotation_mode='QUATERNION'
axis=rig.data.bones['Breath'].matrix_local.to_3x3().inverted()
for act in bpy.data.actions:
    rig.animation_data.action=act
    for f in range(int(act.frame_range[0]),int(act.frame_range[1])+1):
        t=(f-1)/sc.render.fps;u=(t-.10)/.5
        active=act.name=='Fidget' and 0<u<1
        scale=math.sin(math.pi*u)**.6 if active else .0001
        breath.scale=(scale,)*3
        breath.location=axis@Vector((0,-.09*u,.025*u)) if active else Vector()
        breath.keyframe_insert('scale',frame=f);breath.keyframe_insert('location',frame=f)

bm=bmesh.new();bm.from_mesh(mesh.data)
dead=[f for f in bm.faces if f.calc_area()<1e-10]
bmesh.ops.delete(bm,geom=dead,context='FACES');bm.to_mesh(mesh.data);bm.free()
mat=bpy.data.materials.new('Unicorn_A');mat.use_nodes=True;nt=mat.node_tree
bsdf=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
def tex(name,cs):
 img=bpy.data.images.load(str(P/'textures'/name));img.colorspace_settings.name=cs
 node=nt.nodes.new('ShaderNodeTexImage');node.image=img;return node
bc=tex('unicorn_basecolor.png','sRGB');nt.links.new(bc.outputs['Color'],bsdf.inputs['Base Color'])
nm=tex('unicorn_normal_1k.png','Non-Color');nmap=nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(nm.outputs['Color'],nmap.inputs['Color']);nt.links.new(nmap.outputs['Normal'],bsdf.inputs['Normal'])
mr=tex('unicorn_metal_rough_1k.png','Non-Color');sep=nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(mr.outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bsdf.inputs['Roughness'])
nt.links.new(sep.outputs['Blue'],bsdf.inputs['Metallic'])
mesh.data.materials.clear();mesh.data.materials.append(mat)
for act in bpy.data.actions:
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for curve in bag.fcurves:
     for key in curve.keyframe_points:key.interpolation='LINEAR'
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
for obj in sc.objects:obj.select_set(obj in (mesh,rig,cloud))
bpy.context.view_layer.objects.active=rig
(P/'export').mkdir(exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm8_m544_lod0.glb'),use_selection=True,
 export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',
 export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,
 export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,
 export_anim_slide_to_zero=True,export_extras=True)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'unicorn_master.blend'))
(P/'work/export_geometry.json').write_text(json.dumps({'triangles':len(mesh.data.polygons),'removed_zero_area_faces':len(dead),'bones':len(rig.data.bones),'fps':sc.render.fps},indent=2)+'\n')

import subprocess
subprocess.run(['/usr/bin/python3',str(P/'scripts/material_contract.py'),str(P/'export/mm8_m544_lod0.glb')],check=True)
