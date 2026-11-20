"""Textured static export of the rigged master for clips_mm9.py.

Args: <uv blend> <out glb> <mesh name> <texture prefix>
The body takes the composed maps (graded base colour, Meshy normal, ORM with AO in red), smooth normals (Meshy's
faceted custom normals cleared), and is renamed to <mesh name> (the LOD builder's --mesh-node).
"""
import bpy, sys, os
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, NAME, PREFIX = argv
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
bpy.ops.wm.open_mainfile(filepath=IN)
rig = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
if rig.animation_data:
    rig.animation_data.action = None
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)
for b in rig.pose.bones:
    b.matrix_basis.identity()
mat = bpy.data.materials.new(NAME)
mat.use_nodes = True
mat.use_backface_culling = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')


def tex(fname, cs):
    img = bpy.data.images.load(os.path.join(T, fname))
    img.colorspace_settings.name = cs
    n = nt.nodes.new('ShaderNodeTexImage')
    n.image = img
    return n


bc = tex(f'{PREFIX}_basecolor_graded.png', 'sRGB')
nt.links.new(bc.outputs['Color'], bsdf.inputs['Base Color'])
nm = tex(f'{PREFIX}_normal_1k.png', 'Non-Color')
nmap = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(nm.outputs['Color'], nmap.inputs['Color'])
nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
mr = tex(f'{PREFIX}_metal_rough_1k.png', 'Non-Color')
sep = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(mr.outputs['Color'], sep.inputs['Color'])
nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
body.data.materials.clear()
body.data.materials.append(mat)
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects:
    o.select_set(o == body)
try:
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
except RuntimeError:
    pass
bpy.ops.object.shade_smooth()
# model-space y = 0 is the actor's floor: the MM9 bind is centred on the pelvis, so the armature node is lifted
# (joints, bind and clips keep their MM9 values below it)
import numpy as np
lift = -min((body.matrix_world @ v.co).z for v in body.data.vertices)
rig.location.z += lift
bpy.context.view_layer.update()
print('LIFT', round(lift, 4))
body.name = NAME
body.data.name = NAME
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_animations=False,
                          export_skins=True, export_yup=True, export_image_format='AUTO')
print('EXPORTED', OUT, len(body.data.polygons))
