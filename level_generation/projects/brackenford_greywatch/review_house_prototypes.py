"""Run through Blender MCP before town authoring; isolated original house-kit prototypes.

Preserves the current scene. House views use a 2600-unit scale; the temple uses 3200 to include both tower tips.
"""
from pathlib import Path
import importlib
import json
import sys
import bpy
from mathutils import Vector

PROJECT=Path('/home/pjasicek/github/OpenYAMM/level_generation/projects/brackenford_greywatch')
ROOT=PROJECT.parents[2]
sys.path.insert(0,str(PROJECT))
import brackenford_house_kit
importlib.reload(brackenford_house_kit)
previous=bpy.context.window.scene
scene=bpy.data.scenes.new('Brackenford facade prototypes')
out=PROJECT/'review/facade_revision';out.mkdir(parents=True,exist_ok=True)
plan=json.loads((PROJECT/'outdoor_plan.json').read_text())
paths={p.stem.lower():p for p in (ROOT/'assets_dev/worlds/mm8/textures').glob('*.bmp')}
mats={}


def material(key):
    key=key.lower()
    if key not in mats:
        mat=bpy.data.materials.new('Calibrated facade '+key);mat.use_nodes=True
        node=mat.node_tree.nodes.new('ShaderNodeTexImage')
        node.image=bpy.data.images.load(str(paths[key]),check_existing=True);node.interpolation='Closest'
        shader=mat.node_tree.nodes['Principled BSDF'];shader.inputs['Roughness'].default_value=1
        mat.node_tree.links.new(node.outputs['Color'],shader.inputs['Base Color']);mats[key]=mat
    return mats[key]


def object_for(identity,offset=0):
    b=dict(next(b for b in plan['buildings'] if b['id']==identity),floor_z=0)
    kit=brackenford_house_kit.house(b)
    panels=kit['panels']+[(kit['door'],kit['door_texture'])]
    coords=kit['uvs']+[(0,0),(1,0),(1,1),(0,1)]
    points=[];faces=[]
    for polygon,key in panels:
        faces.append(tuple(range(len(points),len(points)+len(polygon))))
        points.extend(((x+offset)/128,y/128,z/128) for x,y,z in polygon)
    mesh=bpy.data.meshes.new(identity);mesh.from_pydata(points,[],faces);mesh.update()
    obj=bpy.data.objects.new(identity,mesh);scene.collection.objects.link(obj)
    keys=list(dict.fromkeys(key.lower() for _,key in panels))
    for key in keys:mesh.materials.append(material(key))
    for polygon,(_,key) in zip(mesh.polygons,panels):polygon.material_index=keys.index(key.lower())
    layer=mesh.uv_layers.new(name='Facade modules')
    for loop,uv in zip(layer.data,coords):loop.uv=uv
    return obj


try:
    bpy.context.window.scene=scene
    scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True
    scene.render.resolution_x=960;scene.render.resolution_y=720;scene.render.resolution_percentage=100
    scene.view_settings.view_transform='Standard'
    scene.world=bpy.data.worlds.new('Facade study background');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.21,.25,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.8
    sun_data=bpy.data.lights.new('Facade sun','SUN');sun_data.energy=2
    sun=bpy.data.objects.new(sun_data.name,sun_data);scene.collection.objects.link(sun)
    sun.rotation_euler=Vector((-.8,1,-1.2)).to_track_quat('-Z','Y').to_euler()
    cam_data=bpy.data.cameras.new('Facade camera');cam_data.type='ORTHO';cam_data.ortho_scale=2600/128
    camera=bpy.data.objects.new(cam_data.name,cam_data);scene.collection.objects.link(camera);scene.camera=camera
    for identity in ['teacher_1','teacher_2','teacher_3','magic_shop','tavern','temple','weapon_shop']:
        for obj in scene.objects:
            if obj.type=='MESH':obj.hide_render=True
        object_for(identity)
        if identity=='weapon_shop':object_for('armor_shop',768)
        center=Vector((384 if identity=='weapon_shop' else 0,0,700 if identity=='temple' else 400))/128
        cam_data.ortho_scale=(3200 if identity=='temple' else 2600)/128
        camera.location=center+Vector((1900,-3100,1800))/128
        camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(out/('prototype_'+identity+'.png'));bpy.ops.render.render(write_still=True)
    print('Rendered seven house prototypes at equal 2600-unit view scale.')
finally:
    bpy.context.window.scene=previous
