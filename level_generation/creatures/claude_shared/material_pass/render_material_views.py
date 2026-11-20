"""Blender half of review_sheet.py: render one creature GLB (rest pose, full-detail meshes) with prepared maps.

Usage: blender --background --python render_material_views.py -- <job.json>
job.json: {"glb", "base", "mr", "normal", "metallic", "roughness", "specular", "specular_mask", "out_prefix", "size"}
Every visible mesh gets one Principled material: base colour = the tier-baked image, metallic = MR blue x factor,
roughness = MR green x factor, Specular IOR Level = 0.5 x specular (x MR red with the specular mask), as the engine
scales its specular (game/shaders/fs_model.sc). Two lights: "sun" (sun from above front-left, sky-gradient world for
reflections) and "indoor" (dim warm torch at the side, dark room world). Views: front, three-quarter, head close-up.
Writes <out_prefix>_<light>_<view>.png. Optional job keys: "lights" and "views" (subsets to render) and
"patch_materials" ({material name: {"specular", "specular_mask"}}): keep the importer's own materials (every
material, image and the default variant of the prepared GLB) and only wire Specular IOR Level as above, for models
with several materials (contact_sheet.py)."""
import json
import math
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

job = json.load(open(sys.argv[sys.argv.index('--') + 1:][0]))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=job['glb'])
for arm in (o for o in bpy.data.objects if o.type == 'ARMATURE'):
    if arm.animation_data:
        arm.animation_data.action = None
    for bone in arm.pose.bones:
        bone.matrix_basis.identity()
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and not any(k in o.name or k in o.data.name
                                                                       for k in ('Shadow', 'LOD'))] or \
    [o for o in bpy.data.objects if o.type == 'MESH' and 'Shadow' not in o.name]
for o in bpy.data.objects:
    if o.type == 'MESH' and o not in meshes:
        o.hide_render = True



def patch(material, specular, mask):
    """Specular IOR Level = 0.5 x specular (x the metallic-roughness red channel with the mask) on an imported one."""
    tree = material.node_tree
    principled = next((n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if principled is None:
        return
    level = principled.inputs['Specular IOR Level']
    for link in list(level.links):
        tree.links.remove(link)
    source = None
    if mask:
        for node in tree.nodes:
            if node.type == 'TEX_IMAGE' and any(link.to_node.type == 'SEPARATE_COLOR'
                                                for link in node.outputs['Color'].links):
                source = node
    if source is None:
        level.default_value = 0.5 * specular
        return
    split = tree.nodes.new('ShaderNodeSeparateColor')
    tree.links.new(source.outputs['Color'], split.inputs['Color'])
    multiply = tree.nodes.new('ShaderNodeMath')
    multiply.operation = 'MULTIPLY'
    multiply.inputs[1].default_value = 0.5 * specular
    tree.links.new(split.outputs['Red'], multiply.inputs[0])
    tree.links.new(multiply.outputs[0], level)


if 'patch_materials' in job:
    for material in bpy.data.materials:
        settings = job['patch_materials'].get(material.name) or job['patch_materials'].get(material.name.split('.')[0])
        if material.node_tree is not None:
            settings = settings or {'specular': 1.0, 'specular_mask': False}
            patch(material, settings['specular'], settings['specular_mask'])


def single_material():
    """One review material from the job's prepared maps on every visible mesh."""
    mat = bpy.data.materials.new('review')
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    uv = nt.nodes.new('ShaderNodeUVMap')

    def image_node(path, colour):
        node = nt.nodes.new('ShaderNodeTexImage')
        node.image = bpy.data.images.load(path)
        if not colour:
            node.image.colorspace_settings.name = 'Non-Color'
        nt.links.new(uv.outputs['UV'], node.inputs['Vector'])
        return node

    def scaled(socket, factor):
        node = nt.nodes.new('ShaderNodeMath')
        node.operation = 'MULTIPLY'
        nt.links.new(socket, node.inputs[0])
        node.inputs[1].default_value = factor
        return node.outputs[0]

    base = image_node(job['base'], True)
    nt.links.new(base.outputs['Color'], bsdf.inputs['Base Color'])
    mr = image_node(job['mr'], False)
    split = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(mr.outputs['Color'], split.inputs['Color'])
    nt.links.new(scaled(split.outputs['Blue'], job['metallic']), bsdf.inputs['Metallic'])
    rough = nt.nodes.new('ShaderNodeMath')
    rough.operation = 'MAXIMUM'
    nt.links.new(scaled(split.outputs['Green'], job['roughness']), rough.inputs[0])
    rough.inputs[1].default_value = 0.045
    nt.links.new(rough.outputs[0], bsdf.inputs['Roughness'])
    if job['specular_mask']:
        nt.links.new(scaled(split.outputs['Red'], 0.5 * job['specular']), bsdf.inputs['Specular IOR Level'])
    else:
        bsdf.inputs['Specular IOR Level'].default_value = 0.5 * job['specular']
    normal_image = image_node(job['normal'], False)
    normal_map = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(normal_image.outputs['Color'], normal_map.inputs['Color'])
    nt.links.new(normal_map.outputs['Normal'], bsdf.inputs['Normal'])
    for o in meshes:
        o.data.materials.clear()
        o.data.materials.append(mat)
        for poly in o.data.polygons:
            poly.material_index = 0
        if o.data.uv_layers:
            normal_map.uv_map = uv.uv_map = o.data.uv_layers[0].name


if 'patch_materials' not in job:
    single_material()
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
co = np.concatenate([np.array([tuple(o.matrix_world @ v.co) for v in o.evaluated_get(dg).data.vertices])
                     for o in meshes])
lo, hi = np.percentile(co, 0.2, axis=0), np.percentile(co, 99.8, axis=0)
centre = Vector((lo + hi) / 2)
height = float(hi[2] - lo[2])
extent = float((hi - lo).max())
head = Vector((centre.x, centre.y, hi[2] - 0.11 * height))
front = -1.0 if job.get('front', '-y') == '-y' else 1.0

sc = bpy.context.scene
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = sc.render.resolution_y = job.get('size', 420)
sc.view_settings.view_transform = 'Standard'
world = bpy.data.worlds.new('w')
world.use_nodes = True
sc.world = world
wn = world.node_tree
background = next(n for n in wn.nodes if n.type == 'BACKGROUND')
coord = wn.nodes.new('ShaderNodeTexCoord')
sep = wn.nodes.new('ShaderNodeSeparateXYZ')
ramp = wn.nodes.new('ShaderNodeValToRGB')
wn.links.new(coord.outputs['Generated'], sep.inputs['Vector'])
wn.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
wn.links.new(ramp.outputs['Color'], background.inputs['Color'])
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = 'ORTHO'
light_objects = []


def lights(kind):
    for o in light_objects:
        bpy.data.objects.remove(o)
    light_objects.clear()
    stops = ramp.color_ramp.elements
    if kind == 'sun':
        # ground brown below the horizon, pale horizon, blue zenith (the Generated Z of the world is the direction)
        stops[0].position, stops[0].color = 0.45, (0.16, 0.12, 0.08, 1)
        stops[1].position, stops[1].color = 0.75, (0.35, 0.5, 0.8, 1)
        mid = stops.new(0.52)
        mid.color = (0.75, 0.78, 0.82, 1)
        background.inputs['Strength'].default_value = 0.7
        sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
        sun.data.energy = 3.5
        sun.data.angle = math.radians(1.5)
        sun.rotation_euler = (math.radians(45), 0, math.radians(-35 if front < 0 else 145))  # -Z: towards +Y, down
        sc.collection.objects.link(sun)
        light_objects.append(sun)
    else:
        while len(stops) > 2:
            stops.remove(stops[1])
        stops[0].position, stops[0].color = 0.4, (0.035, 0.03, 0.028, 1)
        stops[1].position, stops[1].color = 0.6, (0.06, 0.055, 0.05, 1)
        background.inputs['Strength'].default_value = 1.0
        torch = bpy.data.objects.new('torch', bpy.data.lights.new('torch', 'POINT'))
        torch.data.energy = 60 * height ** 2
        torch.data.color = (1.0, 0.72, 0.45)
        torch.data.shadow_soft_size = 0.05
        torch.location = centre + Vector((-0.9 * height, front * 0.8 * height, 0.35 * height))
        sc.collection.objects.link(torch)
        light_objects.append(torch)


# camera offsets from the target (the creature faces `front` along Y), slightly above
views = {'front': (Vector((0, front, 0.12)), centre, extent * 1.05),
         'three_quarter': (Vector((0.7, 0.7 * front, 0.12)), centre, extent * 1.05),
         'head': (Vector((-0.55, 0.85 * front, 0.1)), head, height * 0.3)}
for kind in job.get('lights', ('sun', 'indoor')):
    lights(kind)
    for name, (offset, target, scale) in views.items():
        if name not in job.get('views', views):
            continue
        direction = -offset.normalized()
        cam.data.ortho_scale = scale
        cam.location = target - direction * extent * 4
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f"{job['out_prefix']}_{kind}_{name}.png"
        bpy.ops.render.render(write_still=True)
print('RENDERED', job['out_prefix'])
