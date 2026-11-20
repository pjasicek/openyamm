"""Blender-only material/lighting revision on retained, registered map geometry."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def texture(nodes, path, name, data=False):
    node = nodes.new('ShaderNodeTexImage')
    node.name = name
    node.image = bpy.data.images.load(str(path),check_existing=True)
    node.image.colorspace_settings.name = 'Non-Color' if data else 'sRGB'
    node.interpolation = 'Linear'
    node.extension = 'EXTEND'
    return node


def render(row, recipe):
    settings = {**recipe,**recipe['worlds'][row['world']]}
    out = HERE/row['directory']
    prepared = read(out/'prepared.json')
    assert prepared['recipe_sha256']==sha(HERE/'recipe.json')
    source = Path(row['source'])
    assert sha(source/'scene.blend')==prepared['source_scene_sha256']
    provenance = {'prepared_sha256':sha(out/'prepared.json'),'script_sha256':sha(__file__)}
    if (out/'capture.json').exists():
        report = read(out/'capture.json')
        if report['provenance']==provenance and all(sha(out/n)==h for n,h in report['outputs'].items()):
            return report
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(source/'scene.blend'),link=False) as (src,dst):
        dst.scenes = list(src.scenes)
    assert len(dst.scenes)==1
    scene = dst.scenes[0]
    scene.name = row['world']+' '+row['stem']+' shoreline calibration'
    bpy.context.window.scene = scene
    scene.render.resolution_x = scene.render.resolution_y = recipe['master_size']
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.film_transparent = True
    scene.cycles.samples = 48
    scene.cycles.use_denoising = False
    scene.cycles.diffuse_bounces = 0
    terrain = next(o for o in scene.objects if o.name=='Exact terrain')
    old_coordinates = [tuple(v.co) for v in terrain.data.vertices]
    normals = read(out/'normals.json')
    for polygon in terrain.data.polygons:
        polygon.use_smooth = True
    terrain.data.normals_split_custom_set([normals[l.vertex_index] for l in terrain.data.loops])
    mat = bpy.data.materials.new('Rounded shore, water distance colors and blended land')
    mat.use_nodes = True
    nodes,links = mat.node_tree.nodes,mat.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    land = nodes.new('ShaderNodeBsdfDiffuse')
    land.inputs['Roughness'].default_value = 0
    water = nodes.new('ShaderNodeEmission')
    water.inputs['Strength'].default_value = 1
    mix = nodes.new('ShaderNodeMixShader')
    land_color = texture(nodes,out/'land_color.png','Blended land materials with light grain')
    water_color = texture(nodes,out/'water_color.png','World-specific water depth gradient')
    mask = texture(nodes,out/'water_mask.png','Rounded shoreline coverage',data=True)
    links.new(land_color.outputs['Color'],land.inputs['Color'])
    links.new(water_color.outputs['Color'],water.inputs['Color'])
    links.new(mask.outputs['Color'],mix.inputs[0])
    links.new(land.outputs[0],mix.inputs[1])
    links.new(water.outputs[0],mix.inputs[2])
    links.new(mix.outputs[0],output.inputs['Surface'])
    for obj in scene.objects:
        if obj.type=='MESH' and not obj.name.startswith('BModel '):
            obj.data.materials.clear()
            obj.data.materials.append(mat)
    models = [o for o in scene.objects if o.name.startswith('BModel ')]
    materials = {m for obj in models for m in obj.data.materials}
    for material in materials:
        nodes,links = material.node_tree.nodes,material.node_tree.links
        shader = next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
        tex = next(n for n in nodes if n.type=='TEX_IMAGE')
        key = material.name.split(' ',1)[1]
        info = prepared['textures'][key]
        assert sha(info['path'])==info['sha256']
        tex.image = bpy.data.images.load(info['path'],check_existing=True)
        shader.inputs['Roughness'].default_value = .8
        shader.inputs['Specular IOR Level'].default_value = .12
        bevel = nodes.new('ShaderNodeBevel')
        bevel.inputs['Radius'].default_value = .18
        bevel.samples = 4
        relief = nodes.new('ShaderNodeVectorMath')
        relief.operation = 'MULTIPLY'
        relief.inputs[1].default_value = (recipe['building_normal_relief_scale'],recipe['building_normal_relief_scale'],1)
        normalize = nodes.new('ShaderNodeVectorMath')
        normalize.operation = 'NORMALIZE'
        links.new(bevel.outputs['Normal'],relief.inputs[0])
        links.new(relief.outputs[0],normalize.inputs[0])
        links.new(normalize.outputs[0],shader.inputs['Normal'])
        ao = nodes.new('ShaderNodeAmbientOcclusion')
        ao.inputs['Distance'].default_value = 1.5
        ao.samples = 16
        ao.only_local = True
        multiply = nodes.new('ShaderNodeMixRGB')
        multiply.blend_type = 'MULTIPLY'
        multiply.inputs[0].default_value = .35
        links.new(tex.outputs['Color'],multiply.inputs[1])
        links.new(ao.outputs['Color'],multiply.inputs[2])
        links.new(multiply.outputs[0],shader.inputs['Base Color'])
    data = read(source/'scene.json')
    objects = {o.name:o for o in models}
    errors = []
    for model in data['bmodels']:
        obj = objects['BModel '+str(model['index'])]
        for vertex,expected in zip(obj.data.vertices,model['vertices']):
            xyz = Vector(tuple(expected[a]/128 for a in 'xyz'))
            assert (obj.matrix_world @ vertex.co-xyz).length==0
            uv = world_to_camera_view(scene,scene.camera,xyz)
            errors.append(max(abs(uv.x-(expected['x']+32768)/65536),abs(uv.y-(expected['y']+32768)/65536))*1024)
    assert max(errors,default=0)<.001
    assert old_coordinates==[tuple(v.co) for v in terrain.data.vertices]
    sun = next(o for o in scene.objects if o.type=='LIGHT' and o.data.type=='SUN')
    background = next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND')
    outputs = {}
    for layer,stem in [('Terrain','terrain'),('Objects','buildings')]:
        prefix = 'terrain' if layer=='Terrain' else 'building'
        elevation = math.radians(settings[prefix+'_sun_elevation'])
        azimuth = math.radians(315)
        direction = Vector((math.sin(azimuth)*math.cos(elevation),math.cos(azimuth)*math.cos(elevation),math.sin(elevation)))
        sun.rotation_euler = (-direction).to_track_quat('-Z','Y').to_euler()
        sun.data.energy = settings[prefix+'_sun_energy']
        sun.data.color = (1,.94,.85)
        sun.data.angle = math.radians(8)
        background.inputs['Color'].default_value = (.4,.55,1,1)
        background.inputs['Strength'].default_value = settings[prefix+'_fill']
        for view_layer in scene.view_layers:
            view_layer.use = view_layer.name==layer
        bpy.context.window.view_layer = scene.view_layers[layer]
        scene.render.filepath = str(out/(stem+'_master.png'))
        bpy.ops.render.render(write_still=True)
        # Each editable scene retains the exact settings of its pass.
        bpy.data.libraries.write(str(out/(stem+'.blend')),{scene},path_remap='RELATIVE_ALL')
        for filename in [stem+'_master.png',stem+'.blend']:
            outputs[filename] = sha(out/filename)
    report = dict(provenance=provenance,outputs=outputs,blender=bpy.app.version_string,
                  model_vertices_checked=len(errors),max_projection_error_x2_pixels=max(errors,default=0),
                  terrain_vertices_unchanged=True,original_art_used_as_pixels=False,
                  method='Blender material masks, normal-only terrain smoothing, per-pass lighting, native building textures')
    (out/'capture.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit',type=int)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    recipe = read(HERE/'recipe.json')
    for row in read(HERE/'scope.json')['records'][:args.limit]:
        render(row,recipe)
        print('STYLE_RENDERED',row['world'],row['stem'],flush=True)


if __name__=='__main__':
    main()
