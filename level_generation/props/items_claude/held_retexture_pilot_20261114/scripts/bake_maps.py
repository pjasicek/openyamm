"""Blender steps of the held-sword retexture pilot (README.md) on the locked layout (work/<icon>/layout.blend).

  blender -b --python bake_maps.py -- ao <icon>              work/<icon>/maps/ao.png (2048, Cycles AO, for the grade)
  blender -b --python bake_maps.py -- oldmetal <icon>        work/<icon>/maps/old_metal.png: the installed model's
                                                             metallic (its binary metal mask) carried onto the new UVs
  blender -b --python bake_maps.py -- assemble <icon> <out.glb>
        the export: the layout mesh with maps/basecolor.png, maps/mr.png (glTF: G roughness, B metallic) and
        maps/normal.png (tangent space, glTF +y up), normalTexture scale 1.
"""
import bpy, sys, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..', '..'))
argv = sys.argv[sys.argv.index('--') + 1:]
MODE, ICON = argv[0], argv[1]
WORK = os.path.join(PROJECT, 'work', ICON)
MAPS = os.path.join(WORK, 'maps')
os.makedirs(MAPS, exist_ok=True)
SIZE = 2048

bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'layout.blend'))
obj = next(o for o in bpy.data.objects if o.type == 'MESH')
scene = bpy.context.scene


def bake_target(name):
    img = bpy.data.images.new(name, SIZE, SIZE, alpha=False, float_buffer=False)
    img.colorspace_settings.name = 'Non-Color'
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    node = mat.node_tree.nodes.new('ShaderNodeTexImage'); node.image = img
    mat.node_tree.nodes.active = node
    obj.data.materials.clear(); obj.data.materials.append(mat)
    return img, mat


def setup_cycles(samples):
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.render.bake.margin = 8


if MODE == 'ao':
    setup_cycles(128)
    img, mat = bake_target('ao')
    for o in bpy.data.objects:
        o.select_set(o == obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.bake(type='AO')
    img.filepath_raw = os.path.join(MAPS, 'ao.png'); img.file_format = 'PNG'; img.save()
    print('BAKE ao done')

elif MODE == 'oldmetal':
    setup_cycles(1)
    bpy.ops.import_scene.gltf(filepath=os.path.join(PROJECT, 'before', f'item_{ICON}.glb'))
    src = next(o for o in bpy.data.objects if o.type == 'MESH' and o is not obj)
    smat = src.data.materials[0]
    nodes, links = smat.node_tree.nodes, smat.node_tree.links
    mr = next(n for n in nodes if n.type == 'TEX_IMAGE' and n.image and n.image.name.endswith('_mr'))
    sep = nodes.new('ShaderNodeSeparateColor'); emit = nodes.new('ShaderNodeEmission')
    out = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
    links.new(mr.outputs['Color'], sep.inputs['Color'])
    links.new(sep.outputs['Blue'], emit.inputs['Color'])
    links.new(emit.outputs['Emission'], out.inputs['Surface'])
    img, mat = bake_target('old_metal')
    for o in bpy.data.objects:
        o.select_set(o in (obj, src))
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.bake(type='EMIT', use_selected_to_active=True, cage_extrusion=0.002, max_ray_distance=0.01)
    img.filepath_raw = os.path.join(MAPS, 'old_metal.png'); img.file_format = 'PNG'; img.save()
    print('BAKE oldmetal done')

elif MODE == 'assemble':
    out_glb = argv[2]
    mat = bpy.data.materials.new(f'{ICON} held retexture'); mat.use_nodes = True
    nt = mat.node_tree; bsdf = nt.nodes['Principled BSDF']

    def tex(path, colour):
        n = nt.nodes.new('ShaderNodeTexImage')
        named = os.path.join(MAPS, 'export', f'{ICON}_' + os.path.basename(path))   # glTF image names: <icon>_<map>
        os.makedirs(os.path.dirname(named), exist_ok=True)
        with open(path, 'rb') as a, open(named, 'wb') as b:
            b.write(a.read())
        n.image = bpy.data.images.load(named)
        n.image.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'
        n.image.name = f'{ICON}_' + os.path.splitext(os.path.basename(path))[0]
        return n

    base = tex(os.path.join(MAPS, 'basecolor.png'), True)
    nt.links.new(base.outputs['Color'], bsdf.inputs['Base Color'])
    mr = tex(os.path.join(MAPS, 'mr.png'), False)
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(mr.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    nm = tex(os.path.join(MAPS, 'normal.png'), False)
    nmap = nt.nodes.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = 1.0
    nt.links.new(nm.outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    obj.data.materials.clear(); obj.data.materials.append(mat)
    for o in bpy.data.objects:
        o.select_set(o == obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=out_glb, use_selection=True, export_format='GLB', export_yup=True,
                              export_animations=False, export_image_format='AUTO')
    print('ASSEMBLE done', out_glb)
