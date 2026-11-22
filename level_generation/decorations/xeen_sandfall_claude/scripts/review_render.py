"""Review renders of a fall GLB on a mock rim: land at the lip height, a rim cell's slope (one 512-unit cell down to
the stars water), the water plane; the materials rebuilt as the engine draws them (core blended with texture alpha,
haze additive: colour x alpha x COLOR_0). Views: along the rim, from the land over the lip, from outside, from below.
Usage: blender --background --python review_render.py -- <glb> <out_dir> <drop units> [bright]"""
import math
import os
import sys

import bpy
from mathutils import Vector

glb, out_dir, drop = sys.argv[sys.argv.index('--') + 1:][:3]
bright = 'bright' in sys.argv[sys.argv.index('--') + 1:]
drop = float(drop) / 81.7
os.makedirs(out_dir, exist_ok=True)
M = 1.0 / 81.7

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue
scene.render.resolution_x, scene.render.resolution_y = 960, 720
scene.view_settings.view_transform = 'Standard'

bpy.ops.import_scene.gltf(filepath=glb)
fall = [o for o in bpy.context.scene.objects if o.type == 'MESH']


def node(tree, kind, **inputs):
    n = tree.nodes.new(kind)
    for key, value in inputs.items():
        n.inputs[key].default_value = value
    return n


# Rebuild each material as the engine shades it (flat-lit approximation: the review is about shape and alpha).
for obj in fall:
    for slot in obj.material_slots:
        m = slot.material
        image = next(n.image for n in m.node_tree.nodes if n.type == 'TEX_IMAGE')
        factor = list(m.get('_factor', [1, 1, 1, 1]))
        additive = m.name != 'Core'
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = image
        attr = nt.nodes.new('ShaderNodeVertexColor')
        light = 0.85 if bright else 0.55
        if additive:
            strength = {'Haze1': 0.62, 'Haze2': 0.34, 'Plume': 0.30}.get(m.name, 0.5)
            mul = node(nt, 'ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
            mul.inputs[0].default_value = 1.0
            nt.links.new(tex.outputs['Color'], mul.inputs[6]); nt.links.new(attr.outputs['Color'], mul.inputs[7])
            em = nt.nodes.new('ShaderNodeEmission')
            mul2 = node(nt, 'ShaderNodeMath', Value=strength * light); mul2.operation = 'MULTIPLY'
            nt.links.new(tex.outputs['Alpha'], mul2.inputs[0])
            nt.links.new(mul.outputs[2], em.inputs['Color']); nt.links.new(mul2.outputs[0], em.inputs['Strength'])
            add = nt.nodes.new('ShaderNodeAddShader'); tr = nt.nodes.new('ShaderNodeBsdfTransparent')
            nt.links.new(em.outputs[0], add.inputs[0]); nt.links.new(tr.outputs[0], add.inputs[1])
            nt.links.new(add.outputs[0], out.inputs['Surface'])
        else:
            em = node(nt, 'ShaderNodeEmission', Strength=light)
            nt.links.new(tex.outputs['Color'], em.inputs['Color'])
            tr = nt.nodes.new('ShaderNodeBsdfTransparent')
            mix = nt.nodes.new('ShaderNodeMixShader')
            nt.links.new(tex.outputs['Alpha'], mix.inputs[0])
            nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2])
            nt.links.new(mix.outputs[0], out.inputs['Surface'])
        m.surface_render_method = 'BLENDED'
        m.use_backface_culling = False

# Mock rim (Blender: +Z up; the GLB's out (glTF +Z) imports as Blender -Y).
land_colour = (0.62, 0.50, 0.34, 1) if bright else (0.36, 0.29, 0.20, 1)


def solid(name, verts, faces, colour):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces)
    o = bpy.data.objects.new(name, me); scene.collection.objects.link(o)
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    em = node(nt, 'ShaderNodeEmission', Color=colour, Strength=1.0)
    nt.links.new(em.outputs[0], nt.nodes.new('ShaderNodeOutputMaterial').inputs['Surface'])
    me.materials.append(mat)
    return o


half = 4000 * M
inland = 4000 * M
run = 512 * M
solid('land', [(-half, 0, 0), (half, 0, 0), (half, inland, 0), (-half, inland, 0)], [(0, 1, 2, 3)], land_colour)
solid('slope', [(-half, 0, 0), (half, 0, 0), (half, -run, -drop), (-half, -run, -drop)], [(0, 1, 2, 3)],
      tuple(c * 0.7 for c in land_colour[:3]) + (1,))
water = (0.05, 0.08, 0.14, 1) if bright else (0.02, 0.03, 0.06, 1)
solid('water', [(-half * 3, -run, -drop), (half * 3, -run, -drop), (half * 3, -half * 4, -drop),
                (-half * 3, -half * 4, -drop)], [(0, 1, 2, 3)], water)
world = bpy.data.worlds.new('w'); scene.world = world; world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.45, 0.55, 0.8, 1) if bright else (0.01, 0.012, 0.03, 1)

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); scene.collection.objects.link(cam)
scene.camera = cam
cam.data.lens = 28
views = {
    'rim_edge': ((1800 * M, 60 * M, 180 * M), (0, -400 * M, -700 * M)),
    'promontory': ((3000 * M, -900 * M, 300 * M), (0, -400 * M, -800 * M)),
    'land_close': ((350 * M, 900 * M, 180 * M), (0, -300 * M, -500 * M)),
    'outside': ((600 * M, -3800 * M, -500 * M), (0, -500 * M, -900 * M)),
    'side': ((4200 * M, -500 * M, -800 * M), (0, -500 * M, -900 * M)),
}
for name, (position, target) in views.items():
    cam.location = Vector(position)
    cam.rotation_euler = (Vector(target) - Vector(position)).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(out_dir, f'{name}{"_bright" if bright else ""}.png')
    bpy.ops.render.render(write_still=True)
    print('RENDERED', scene.render.filepath)
