"""Save a separate editable checkpoint with the selected head repair; preserve geometry and animation."""
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'work/final_v3.blend'), load_ui=False)
mesh = bpy.data.objects['Peasant']
tex = ROOT / 'textures_v3'

def material(name, base, normal, orm):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    def image(filename, space):
        img = bpy.data.images.load(str(tex / filename), check_existing=True)
        img.colorspace_settings.name = space
        node = nodes.new('ShaderNodeTexImage')
        node.image = img
        return node
    color = image(base, 'sRGB')
    links.new(color.outputs['Color'], shader.inputs['Base Color'])
    bump = image(normal, 'Non-Color')
    normal_node = nodes.new('ShaderNodeNormalMap')
    links.new(bump.outputs['Color'], normal_node.inputs['Color'])
    links.new(normal_node.outputs['Normal'], shader.inputs['Normal'])
    roughness = image(orm, 'Non-Color')
    channels = nodes.new('ShaderNodeSeparateColor')
    links.new(roughness.outputs['Color'], channels.inputs['Color'])
    links.new(channels.outputs['Green'], shader.inputs['Roughness'])
    shader.inputs['Metallic'].default_value = 0
    return mat

mesh.data.materials.clear()
mesh.data.materials.append(material('Peasant_A', 'pfem_a_basecolor_1k.png', 'pfem_normal_1k.png', 'pfem_metal_rough_1k.png'))
mesh.data.materials.append(material('PeasantHead_A', 'pfem_head_basecolor_repaired.png', 'pfem_head_normal_1k.png',
                                   'pfem_head_metal_rough_1k.png'))
head = mesh.data.attributes['head'].data
for poly in mesh.data.polygons:
    poly.material_index = head[poly.index].value
bpy.context.scene.frame_set(1)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'work/final_v3_head_repaired.blend'))
print('HEAD_REPAIR_MASTER_SAVED')
