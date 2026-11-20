"""Inspect the written Greywatch BLV. Cutaways use study lighting and omit ceilings; they do not prove runtime lighting."""
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT=Path('/home/pjasicek/github/OpenYAMM')
PROJECT=ROOT/'level_generation/projects/brackenford_greywatch'
REVIEW=PROJECT/'review'
REVIEW.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_blv_file
native=parse_blv_file(PROJECT/'runtime/worlds/mm8/maps/lg02.blv')['payload']
scene=bpy.data.scenes.new('Greywatch native review')
bpy.context.window.scene=scene
scene.render.engine='CYCLES'
scene.cycles.samples=16
scene.render.resolution_x=1280
scene.render.resolution_y=960
scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Greywatch inspection world')
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.25,.28,.32,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
paths={p.stem.lower():p for p in (ROOT/'assets_dev/worlds/mm8/textures').iterdir() if p.suffix.lower()=='.bmp'}
materials={}
for key in sorted({f['texture_name'] for f in native['faces'] if not f['is_portal']}):
    bitmap=bpy.data.images.load(str(paths[key.lower()]),check_existing=True)
    material=bpy.data.materials.new('NativeReview_'+key)
    material.use_nodes=True
    nodes=material.node_tree.nodes; links=material.node_tree.links
    shader=nodes['Principled BSDF']
    texture=nodes.new('ShaderNodeTexImage'); texture.image=bitmap; texture.interpolation='Closest'
    links.new(texture.outputs['Color'],shader.inputs['Base Color'])
    # Legacy indoor faces are one-sided. Avoid rendering or shadowing their back sides in the cutaway.
    geometry=nodes.new('ShaderNodeNewGeometry')
    transparent=nodes.new('ShaderNodeBsdfTransparent')
    mix=nodes.new('ShaderNodeMixShader')
    links.new(geometry.outputs['Backfacing'],mix.inputs[0])
    links.new(shader.outputs[0],mix.inputs[1]); links.new(transparent.outputs[0],mix.inputs[2])
    links.new(mix.outputs[0],nodes['Material Output'].inputs['Surface'])
    materials[key]=(material,tuple(bitmap.size))
vertices=[]; faces=[]; uvs=[]; keys=[]
for face in native['faces']:
    if face['is_portal'] or face['facet_type'] in (5,6):
        continue
    offset=len(vertices)
    vertices.extend(tuple(native['vertices'][i][axis]/128 for axis in 'xyz') for i in face['vertex_indices'])
    faces.append(tuple(range(offset,len(vertices))))
    width,height=materials[face['texture_name']][1]
    uvs.extend((u/width,1-v/height) for u,v in zip(face['texture_us'],face['texture_vs']))
    keys.append(face['texture_name'])
data=bpy.data.meshes.new('Native Greywatch faces'); data.from_pydata(vertices,[],faces); data.update()
obj=bpy.data.objects.new('BLV reimport, ceilings excluded',data); scene.collection.objects.link(obj)
for material,_ in materials.values():
    data.materials.append(material)
for face,key in zip(data.polygons,keys):
    face.material_index=list(materials).index(key)
layer=data.uv_layers.new()
for loop,uv in zip(layer.data,uvs):
    loop.uv=uv
sys.path.insert(0,str(ROOT/'level_generation/scripts'))
from blender_native_decorations import add_billboards
source_records=json.loads((PROJECT/'source/lg02.decorations.json').read_text())['records']
native_records=[]
for entity in native['entities']:
    position=[entity['position'][k] for k in 'xyz']
    source=next(r for r in source_records if r['id']==entity['decoration_list_id'] and r['position']==position)
    native_records.append(dict(source,index=entity['index'],position=position))
billboards=add_billboards(scene,native_records,ROOT)
scene.cycles.transparent_max_bounces=16
sun_data=bpy.data.lights.new('Study sun','SUN'); sun_data.energy=1.8
sun=bpy.data.objects.new('Study sun',sun_data); scene.collection.objects.link(sun)
sun.rotation_euler=(.4,-.5,-.7)
camera_data=bpy.data.cameras.new('Native review camera'); camera_data.type='ORTHO'; camera_data.ortho_scale=176
camera=bpy.data.objects.new('Native review camera',camera_data); scene.collection.objects.link(camera); scene.camera=camera
target=Vector((3200,3000,500))/128
for name,position in [('greywatch_native_south',(20500,-19000,26000)),
                       ('greywatch_native_north',(-17000,24000,26000))]:
    camera.location=Vector(position)/128
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    for billboard in billboards:billboard.rotation_euler=camera.rotation_euler
    scene.render.filepath=str(REVIEW/(name+'.png'))
    bpy.ops.render.render(write_still=True)
print(json.dumps({'review':str(REVIEW),'native_faces':len(native['faces']),
                  'scope':'native geometry/decorations with study lighting; runtime actors and lighting not pictured'}))
