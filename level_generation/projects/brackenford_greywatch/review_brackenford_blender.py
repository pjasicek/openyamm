"""Reimport the written ODM and render terrain/town/castle with neutral inspection lighting.

Water previews composite an existing MM8 animated-water frame under the legacy magenta-key shore overlays.
This is explicitly a native geometry review, not a gameplay lighting or performance test.
"""
import csv
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector
import numpy as np

ROOT=Path('/home/pjasicek/github/OpenYAMM')
PROJECT=ROOT/'level_generation/projects/brackenford_greywatch'
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file
native=parse_odm_file(PROJECT/'runtime/worlds/mm8/maps/lg01.odm')['payload']
scene=bpy.data.scenes.new('Brackenford native review');bpy.context.window.scene=scene
scene.render.engine='CYCLES';scene.cycles.samples=12
scene.render.resolution_x=1280;scene.render.resolution_y=960;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Brackenford inspection world');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.38,.46,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
paths={}
for folder in [ROOT/'assets_dev/worlds/mm8/textures',ROOT/'assets_dev/engine/terrain',ROOT/'assets_dev/engine/textures']:
    for path in folder.glob('*'):
        if path.suffix.lower() in ['.bmp','.png']:
            paths.setdefault(path.stem.lower(),path)
materials={}


def material(key):
    key=key.lower()
    if key in materials:return materials[key]
    image=bpy.data.images.load(str(paths['hdwtr000' if key=='wtrtyl' else key]),check_existing=True)
    if key.startswith('wtrdr'):
        water=bpy.data.images.load(str(paths['hdwtr000']),check_existing=True)
        overlay=np.array(image.pixels[:],dtype=np.float32).reshape(-1,4)
        pixels=np.array(water.pixels[:],dtype=np.float32).reshape(water.size[1],water.size[0],4)
        rows=np.arange(image.size[1])*water.size[1]//image.size[1]
        columns=np.arange(image.size[0])*water.size[0]//image.size[0]
        base=pixels[rows[:,None],columns[None,:]].reshape(-1,4)
        transparent=(overlay[:,0]>.7)&(overlay[:,2]>.7)&(overlay[:,1]<.3)
        overlay[transparent]=base[transparent]
        composite=bpy.data.images.new('Native shore preview '+key,width=image.size[0],height=image.size[1])
        composite.pixels.foreach_set(overlay.ravel());image=composite
    mat=bpy.data.materials.new('BrackenfordNative_'+key);mat.use_nodes=True
    texture=mat.node_tree.nodes.new('ShaderNodeTexImage');texture.image=image;texture.interpolation='Closest'
    shader=mat.node_tree.nodes['Principled BSDF'];shader.inputs['Roughness'].default_value=1
    mat.node_tree.links.new(texture.outputs['Color'],shader.inputs['Base Color'])
    materials[key]=(mat,tuple(image.size));return materials[key]


def mesh_object(name,records):
    vertices=[];faces=[];uvs=[];keys=[]
    for points,key,coords in records:
        faces.append(tuple(range(len(vertices),len(vertices)+len(points))))
        vertices.extend(tuple(v/128 for v in p) for p in points);uvs.extend(coords);keys.append(key.lower())
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj)
    unique=list(dict.fromkeys(keys))
    for key in unique:mesh.materials.append(material(key)[0])
    slots={key:i for i,key in enumerate(unique)}
    for poly,key in zip(mesh.polygons,keys):poly.material_index=slots[key]
    layer=mesh.uv_layers.new(name='Native UV')
    for loop,point in zip(layer.data,uvs):loop.uv=point
    return obj


table={int(row[0]):row for row in csv.reader((ROOT/'assets_dev/engine/data_tables/terrain_tile_data.txt').open(),delimiter='\t')
       if row and row[0].isdigit()}
records=[]
for r in range(127):
    for c in range(127):
        coords=[(c,r),(c+1,r),(c,r+1),(c+1,r+1)]
        points=[((x-64)*512,(64-y)*512,native['height_map'][y*128+x]*32) for x,y in coords]
        raw=native['tile_map'][r*128+c];index=raw if raw<198 else raw-198+414;key=table[index][1]
        records.extend([([points[i] for i in [0,2,1]],key,[(0,1),(0,0),(1,1)]),
                        ([points[i] for i in [1,2,3]],key,[(1,1),(0,0),(1,0)])])
mesh_object('Native ODM terrain',records)
records=[]
for model in native['bmodels']:
    for face in model['faces']:
        points=[tuple(model['vertices'][i][k] for k in 'xyz') for i in face['vertex_indices']]
        key=face['texture_name'];_,size=material(key)
        coords=[((u+face['texture_delta_u'])/size[0],1-(v+face['texture_delta_v'])/size[1])
                for u,v in zip(face['texture_us'],face['texture_vs'])]
        records.append((points,key,coords))
mesh_object('Native ODM BModels',records)
sys.path.insert(0,str(ROOT/'level_generation/scripts'))
from blender_native_decorations import add_billboards
decoration_source=json.loads((PROJECT/'source/lg01.decorations.json').read_text())
decoration_records=[]
for source in decoration_source['records']:
    entity=native['entities'][source['index']]
    assert entity['name']==source['name'] and entity['decoration_list_id']==source['id']
    decoration_records.append(dict(source,position=[entity['position'][k] for k in 'xyz']))
billboards=add_billboards(scene,decoration_records,ROOT)
scene.cycles.transparent_max_bounces=16
sun_data=bpy.data.lights.new('Study sun',type='SUN');sun_data.energy=1.5;sun_data.angle=.2
sun=bpy.data.objects.new(sun_data.name,sun_data);scene.collection.objects.link(sun);sun.rotation_euler=(.4,-.3,-.4)
cam_data=bpy.data.cameras.new('Native Brackenford review camera');cam_data.type='ORTHO';cam_data.clip_end=3000
camera=bpy.data.objects.new(cam_data.name,cam_data);scene.collection.objects.link(camera);scene.camera=camera
views=globals().get('LEVELGEN_REVIEW_VIEWS',[('region',(0,0,1000),(47000,-56000,72000),65000),
       ('town',(-10240,0,800),(-25500,-22500,25000),23000),
       ('bridge',(5376,256,500),(13000,-8000,8500),11000),
       ('castle',(15360,17920,2300),(23000,6000,10500),10500)])
for name,target,position,scale in views:
    camera.location=Vector(position)/128
    camera.rotation_euler=(Vector(target)/128-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=scale/128
    for obj in billboards:
        direction=camera.location-obj.location
        direction.z=0
        obj.rotation_euler=direction.to_track_quat('Z','Y').to_euler()
    scene.render.filepath=str(PROJECT/'review'/('brackenford_native_'+name+'.png'))
    bpy.ops.render.render(write_still=True)
print(json.dumps({'source':'written lg01.odm','views':[v[0] for v in views],'lighting':'inspection only'}))
