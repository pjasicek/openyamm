"""Bake the MM5 sand/dirt material from unchanged native textures through Blender MCP.

This authors material assets; rebuild terrain separately. All variants use
the same periodic noise field and corner interpolation, so adjacent orientations
share the same boundary shape. Original donor RGB detail is sampled by the shader.
"""
import hashlib
import json
import math
from pathlib import Path

import bpy

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
OUTPUT = Path(globals().get('MATERIAL_OUTPUT',PROJECT/'implementation/art/desert_terrain'))
OUTPUT.mkdir(parents=True, exist_ok=True)
previous = bpy.context.window.scene
name = 'MM5 desert material study'
if previous.name == name:
    previous = bpy.data.scenes['MM5 Castleview architecture']
    bpy.context.window.scene = previous
if name in bpy.data.scenes:
    bpy.data.scenes.remove(bpy.data.scenes[name])
scene = bpy.data.scenes.new(name)
bpy.context.window.scene = scene
donors = {'sand': ROOT/'assets_dev/worlds/mm7/textures/7sand.bmp',
          'dirt': ROOT/'assets_dev/worlds/mm8/textures/DIRTtyl.bmp'}
mat = bpy.data.materials.new('MM5 original sand and dirt transition material')
mat.use_nodes = True
nodes,links = mat.node_tree.nodes,mat.node_tree.links
nodes.clear()


def math_node(operation,a,b=None):
    node = nodes.new('ShaderNodeMath')
    node.operation = operation
    for i,value in enumerate([a,b]):
        if value is None:
            continue
        if isinstance(value,(int,float)):
            node.inputs[i].default_value = value
        else:
            links.new(value,node.inputs[i])
    return node.outputs[0]


uv = nodes.new('ShaderNodeTexCoord')
split = nodes.new('ShaderNodeSeparateXYZ')
links.new(uv.outputs['UV'],split.inputs[0])
def mask_coordinate(value):
    # Raster edge pixels sample half a texel inside the quad. Pin those centers
    # to 0/1 for the mask only; donor artwork retains its original UV sampling.
    mapped = math_node('DIVIDE',math_node('SUBTRACT',value,.5/128),127/128)
    return math_node('MINIMUM',1,math_node('MAXIMUM',0,mapped))


u,v = [mask_coordinate(split.outputs[key]) for key in ['X','Y']]
corners = [nodes.new('ShaderNodeValue') for _ in range(4)]
for node,label in zip(corners,['NW','NE','SW','SE']):
    node.label = label
    node.name = 'Dirt '+label


def interpolate(a,b,t):
    return math_node('ADD',a,math_node('MULTIPLY',math_node('SUBTRACT',b,a),t))


top = interpolate(corners[0].outputs[0],corners[1].outputs[0],u)
bottom = interpolate(corners[2].outputs[0],corners[3].outputs[0],u)
field = interpolate(bottom,top,v)
# A 4D torus gives identical noise at both U and V edges, including diagonal joins.
angle_u = math_node('MULTIPLY',u,2*math.pi)
angle_v = math_node('MULTIPLY',v,2*math.pi)
vector = nodes.new('ShaderNodeCombineXYZ')
for i,value in enumerate([math_node('COSINE',angle_u),math_node('SINE',angle_u),
                           math_node('COSINE',angle_v)]):
    links.new(value,vector.inputs[i])
noise = nodes.new('ShaderNodeTexNoise')
noise.noise_dimensions = '4D'
noise.inputs['Scale'].default_value = 7
noise.inputs['Detail'].default_value = 3
noise.inputs['Roughness'].default_value = .65
links.new(vector.outputs[0],noise.inputs['Vector'])
links.new(math_node('SINE',angle_v),noise.inputs['W'])
envelope = math_node('MULTIPLY',4,math_node('MULTIPLY',field,math_node('SUBTRACT',1,field)))
variation = math_node('MULTIPLY',math_node('SUBTRACT',noise.outputs['Fac'],.5),.75)
perturbed = math_node('ADD',field,math_node('MULTIPLY',envelope,variation))
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.interpolation = 'EASE'
ramp.color_ramp.elements[0].position = .43
ramp.color_ramp.elements[1].position = .57
links.new(perturbed,ramp.inputs[0])
mix = nodes.new('ShaderNodeMixRGB')
links.new(ramp.outputs['Color'],mix.inputs[0])
for i,(key,path) in enumerate(donors.items(),1):
    texture = nodes.new('ShaderNodeTexImage')
    texture.image = bpy.data.images.load(str(path),check_existing=True)
    texture.interpolation = 'Closest'
    links.new(uv.outputs['UV'],texture.inputs['Vector'])
    links.new(texture.outputs['Color'],mix.inputs[i])
emission = nodes.new('ShaderNodeEmission')
links.new(mix.outputs[0],emission.inputs['Color'])
output = nodes.new('ShaderNodeOutputMaterial')
links.new(emission.outputs[0],output.inputs['Surface'])
mesh = bpy.data.meshes.new('MM5 material sample quad')
mesh.from_pydata([(-.5,-.5,0),(.5,-.5,0),(.5,.5,0),(-.5,.5,0)],[],[(0,1,2,3)])
mesh.materials.append(mat)
layer = mesh.uv_layers.new()
for loop,point in zip(mesh.polygons[0].loop_indices,[(0,0),(1,0),(1,1),(0,1)]):
    layer.data[loop].uv = point
quad = bpy.data.objects.new('MM5 material sample quad',mesh)
scene.collection.objects.link(quad)
camera = bpy.data.objects.new('MM5 material bake camera',bpy.data.cameras.new('MM5 material bake camera'))
scene.collection.objects.link(camera)
camera.location = (0,0,2)
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 1
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.samples = 1
scene.cycles.use_denoising = False
scene.cycles.filter_width = .01
scene.render.resolution_x = scene.render.resolution_y = 128
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.view_settings.exposure = 0
variants = {}
for bits in [0,1,2,3,4,5,7,8,10,11,12,13,14,15]:
    for i,node in enumerate(corners):
        node.outputs[0].default_value = int(bool(bits&(1<<i)))
    path = OUTPUT/f'mm5sd{bits:02d}.png'
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    variants[str(bits)] = {'path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT/'desert_material.blend'),copy=True)
bpy.context.window.scene = previous
report = {'status':'shader-baked material assets; native map requires separate terrain build',
          'donors':{key:{'path':str(path.relative_to(ROOT)),
                         'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for key,path in donors.items()},
          'variants':variants,'bits':'NW=1 NE=2 SW=4 SE=8 indicate dark dirt',
          'method':'periodic 4D noise perturbing bilinear corner field, native texture RGB mixed in linear light',
          'render':'128x128, emission, Standard/None, closest donor sampling; no lighting or upscaling',
          'review':'review/desert_materials_v2/native_review.json',
          'reviewPending':['repeat affected artwork and native views if material parameters change']}
(OUTPUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print('Desert transition material assets baked; native terrain unchanged.')
