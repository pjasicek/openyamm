"""Isolated canopy/rope study; never writes active map geometry or native scene inputs."""
import importlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(PROJECT))
import author_skyrope
importlib.reload(author_skyrope)

VERSION = globals().get('REVIEW_VERSION', 'skyrope_study_v1')
OUTPUT = PROJECT/'review'/VERSION
OUTPUT.mkdir(parents=True, exist_ok=True)
NAME = 'MM5 Skyroad rope study'
previous_scene = bpy.context.window.scene
old = bpy.data.scenes.get(NAME)
if old:
    if previous_scene == old:
        previous_scene = bpy.data.scenes['MM5 Castleview architecture']
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new(NAME)
bpy.context.window.scene = scene


def object_from_mesh(name, vertices, faces):
    mesh = bpy.data.meshes.new(NAME+' '+name)
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new(NAME+' '+name, mesh)
    scene.collection.objects.link(obj)
    return obj


materials = {}
spec = json.loads((PROJECT/'implementation/architecture.json').read_text())
for key in author_skyrope.PALETTE.values():
    mat = bpy.data.materials.new(NAME+' '+key)
    mat.use_nodes = True
    tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(ROOT/spec['materials'][key]['path']), check_existing=True)
    tex.interpolation = 'Closest'
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value = 1
    mat.node_tree.links.new(tex.outputs['Color'], shader.inputs['Base Color'])
    materials[key] = (mat, tuple(tex.image.size))


class StudyAuthor:
    def panel(self, panels, points, key):
        first = Vector(points[0])
        u = (Vector(points[1])-first).normalized()
        normal = (Vector(points[1])-first).cross(Vector(points[-1])-first).normalized()
        v = normal.cross(u)
        width, height = materials[key][1]
        uv = [((Vector(p)-first).dot(u)/width, (Vector(p)-first).dot(v)/height) for p in points]
        panels.append((points, key, uv))


for name, generate in [('branch', author_skyrope.branch), ('rope', author_skyrope.rope)]:
    panels = []
    generate(StudyAuthor(), panels, author_skyrope.PALETTE)
    vertices, faces, keys, uvs = [], [], [], []
    for points, key, uv in panels:
        faces.append(tuple(range(len(vertices), len(vertices)+len(points))))
        vertices.extend([[v/128 for v in p] for p in points])
        keys.append(key)
        uvs.extend(uv)
    obj = object_from_mesh(name, vertices, faces)
    for key in materials:
        obj.data.materials.append(materials[key][0])
    for poly, key in zip(obj.data.polygons, keys):
        poly.material_index = list(materials).index(key)
    layer = obj.data.uv_layers.new()
    for datum, uv in zip(layer.data, uvs):
        datum.uv = uv

tree = object_from_mesh('native tree12', [(-4, 0, 0), (4, 0, 0), (4, 0, 8), (-4, 0, 8)], [(0, 1, 2, 3)])
tree.location = (0, 288/128, 0)
layer = tree.data.uv_layers.new()
for datum, uv in zip(layer.data, [(0, 0), (1, 0), (1, 1), (0, 1)]):
    datum.uv = uv
mat = bpy.data.materials.new(NAME+' keyed native tree12')
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
tex = nodes.new('ShaderNodeTexImage')
tex.image = bpy.data.images.load(str(ROOT/'level_generation/catalogues/outdoor_decorations/sprites/mm8_463.png'),
                                 check_existing=True)
tex.interpolation = 'Closest'
shader = nodes.get('Principled BSDF')
shader.inputs['Roughness'].default_value = 1
links.new(tex.outputs['Color'], shader.inputs['Base Color'])
mix = nodes.new('ShaderNodeMixShader')
links.new(tex.outputs['Alpha'], mix.inputs[0])
links.new(nodes.new('ShaderNodeBsdfTransparent').outputs[0], mix.inputs[1])
links.new(shader.outputs[0], mix.inputs[2])
links.new(mix.outputs[0], nodes.get('Material Output').inputs[0])
tree.data.materials.append(mat)

ground = object_from_mesh('neutral ground', [(-100, -100, 0), (100, -100, 0),
                                             (100, 100, 0), (-100, 100, 0)], [(0, 1, 2, 3)])
mat = bpy.data.materials.new(NAME+' neutral ground')
mat.diffuse_color = (.18, .23, .12, 1)
ground.data.materials.append(mat)
scene.world = bpy.data.worlds.new(NAME+' world')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.5, .6, .7, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .7
light = bpy.data.objects.new(NAME+' sun', bpy.data.lights.new(NAME+' sun', 'SUN'))
scene.collection.objects.link(light)
light.rotation_euler = (.35, -.6, -.5)
light.data.energy = 2
camera = bpy.data.objects.new(NAME+' camera', bpy.data.cameras.new(NAME+' camera'))
scene.collection.objects.link(camera)
scene.camera = camera
camera.data.lens = 35
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = 1000, 800
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'Standard'
report = []
for name, position, target in [
        ('approach', (320, -1400, 176), (32, 288, 420)),
        ('side', (1400, 0, 176), (32, 288, 420)),
        ('upper_anchor', (420, -240, 800), (80, 288, 728))]:
    camera.location = Vector(position)/128
    camera.rotation_euler = (Vector(target)/128-camera.location).to_track_quat('-Z', 'Y').to_euler()
    direction = camera.location-tree.location
    tree.rotation_euler[2] = math.atan2(direction.y, direction.x)+math.pi/2
    scene.render.filepath = str(OUTPUT/(name+'.png'))
    bpy.ops.render.render(write_still=True)
    report.append({'image': name+'.png', 'position': position, 'target': target})
(OUTPUT/'cameras.json').write_text(json.dumps(report, indent=2)+'\n')
bpy.context.window.scene = previous_scene
print({'studyScene': scene.name, 'images': len(report), 'nativeExport': False})
