"""Assign a material from texture files to the rat mesh. Args: basecolor normal metal_rough|- roughness|- metallic|-"""
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
mesh = bpy.data.objects['Rat']
mat = bpy.data.materials.new('Rat_A'); mat.use_nodes = True
nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
def tex(p, cs):
    img = bpy.data.images.load(os.path.abspath(p)); img.colorspace_settings.name = cs
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n
bc = tex(a[0], 'sRGB'); nt.links.new(bc.outputs['Color'], bsdf.inputs['Base Color'])
nm = tex(a[1], 'Non-Color'); nmap = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(nm.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
if a[2] != '-':
    mr = tex(a[2], 'Non-Color'); sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(mr.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
else:
    r = tex(a[3], 'Non-Color'); nt.links.new(r.outputs['Color'], bsdf.inputs['Roughness'])
    m = tex(a[4], 'Non-Color'); nt.links.new(m.outputs['Color'], bsdf.inputs['Metallic'])
nt.nodes.active = bc
mesh.data.materials.clear(); mesh.data.materials.append(mat)
bpy.ops.wm.save_mainfile()
print('MATERIAL applied')
