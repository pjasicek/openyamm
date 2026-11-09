"""Map the purpose-painted trim tiles onto exact authored panels and unrolled bands."""
import math
from pathlib import Path

import bpy

PROJECT = Path(__file__).resolve().parents[1]


def trim_material(tile, band=False):
    name = f'jewellery_trim_{tile}' + ('_band' if band else '')
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = True
    shader = mat.node_tree.nodes['Principled BSDF']
    textures = {}
    for suffix in ('base', 'mr', 'normal'):
        texture = mat.node_tree.nodes.new('ShaderNodeTexImage')
        texture.image = bpy.data.images.load(str(PROJECT / f'textures/{name}_{suffix}.png'), check_existing=True)
        if suffix != 'base':
            texture.image.colorspace_settings.name = 'Non-Color'
        textures[suffix] = texture
    mat.node_tree.links.new(textures['base'].outputs['Color'], shader.inputs['Base Color'])
    channels = mat.node_tree.nodes.new('ShaderNodeSeparateColor')
    mat.node_tree.links.new(textures['mr'].outputs['Color'], channels.inputs['Color'])
    mat.node_tree.links.new(channels.outputs['Green'], shader.inputs['Roughness'])
    mat.node_tree.links.new(channels.outputs['Blue'], shader.inputs['Metallic'])
    normal = mat.node_tree.nodes.new('ShaderNodeNormalMap')
    mat.node_tree.links.new(textures['normal'].outputs['Color'], normal.inputs['Color'])
    mat.node_tree.links.new(normal.outputs['Normal'], shader.inputs['Normal'])
    return mat


def engrave(obj, tile, band=False):
    obj.data.materials.append(trim_material(tile, band))
    index = len(obj.data.materials) - 1
    uv = obj.data.uv_layers.active or obj.data.uv_layers.new(name='Painted surface UV')
    lower = [min(v.co[i] for v in obj.data.vertices) for i in range(3)]
    upper = [max(v.co[i] for v in obj.data.vertices) for i in range(3)]
    for face in obj.data.polygons:
        if (band and abs(face.normal.z) > .65) or (not band and face.normal.z < .22):
            continue
        face.material_index = index
        values = []
        for vertex_index in face.vertices:
            co = obj.data.vertices[vertex_index].co
            if band:
                u = (math.atan2(co.y, co.x) / math.tau) % 1
                v = (co.z - lower[2]) / max(upper[2] - lower[2], 1e-5)
            else:
                u = (co.x - lower[0]) / max(upper[0] - lower[0], 1e-5)
                v = (co.y - lower[1]) / max(upper[1] - lower[1], 1e-5)
            values.append((u, v))
        seam = band and max(u for u, v in values) - min(u for u, v in values) > .5
        for loop_index, (u, v) in zip(face.loop_indices, values):
            if seam and u < .5:
                u = 1
            uv.data[loop_index].uv = (.012 + .976 * u, .012 + .976 * v)
    return obj
