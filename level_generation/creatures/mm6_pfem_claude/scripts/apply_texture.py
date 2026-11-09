"""Assign a base-colour (and optional normal/roughness/metallic) texture set to Peasant as one material.
Args: basecolor [normal] [roughness] [metallic] [out_blend]."""
import bpy, sys, os
args = sys.argv[sys.argv.index('--') + 1:]
paths = (args + [''] * 4)[:4]
mesh = bpy.data.objects['Peasant']
mat = bpy.data.materials.get('Peasant_Material') or bpy.data.materials.new('Peasant_Material')
mat.use_nodes = True; mat.use_backface_culling = False
nt = mat.node_tree
for n in list(nt.nodes): nt.nodes.remove(n)
out = nt.nodes.new('ShaderNodeOutputMaterial'); bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
nt.links.new(bsdf.outputs[0], out.inputs[0])
def tex(path, colour):
    img = bpy.data.images.load(os.path.abspath(path), check_existing=True); img.colorspace_settings.name = colour
    node = nt.nodes.new('ShaderNodeTexImage'); node.image = img; return node
bc = tex(paths[0], 'sRGB'); nt.links.new(bc.outputs['Color'], bsdf.inputs['Base Color'])
if paths[1]:
    n = tex(paths[1], 'Non-Color'); nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(n.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
if paths[2]:
    r = tex(paths[2], 'Non-Color'); nt.links.new(r.outputs['Color'], bsdf.inputs['Roughness'])
if paths[3]:
    m = tex(paths[3], 'Non-Color'); nt.links.new(m.outputs['Color'], bsdf.inputs['Metallic'])
else:
    bsdf.inputs['Metallic'].default_value = 0.0
mesh.data.materials.clear(); mesh.data.materials.append(mat)
if len(args) > 4 and args[4]:
    bpy.ops.wm.save_as_mainfile(filepath=args[4])
else:
    bpy.ops.wm.save_mainfile()
