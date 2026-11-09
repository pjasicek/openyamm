"""Give NB_Plate the carapace atlas (base colour, OpenGL normal, ORM: G roughness) and NB_Glow an orange emission;
saves in place. Args: -- <blend>"""
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
T = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'textures')
m = bpy.data.materials['NB_Plate']; m.use_nodes = True; nt = m.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
b = nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(b.outputs[0], out.inputs[0])
def img(name, colour):
    n = nt.nodes.new('ShaderNodeTexImage')
    n.image = bpy.data.images.load(os.path.join(T, name), check_existing=True); n.image.reload()
    if not colour: n.image.colorspace_settings.name = 'Non-Color'
    return n
nt.links.new(img('nb_carapace_basecolor.png', True).outputs[0], b.inputs['Base Color'])
orm = img('nb_carapace_metal_rough.png', False); sep = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(orm.outputs[0], sep.inputs[0]); nt.links.new(sep.outputs[1], b.inputs['Roughness'])
b.inputs['Metallic'].default_value = 0.0
nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(img('nb_carapace_normal.png', False).outputs[0], nm.inputs['Color'])
nt.links.new(nm.outputs[0], b.inputs['Normal'])
g = bpy.data.materials['NB_Glow']; g.use_nodes = True
gb = next(n for n in g.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
gb.inputs['Base Color'].default_value = (1.0, 0.42, 0.08, 1); gb.inputs['Emission Color'].default_value = (1.0, 0.42, 0.08, 1)
gb.inputs['Emission Strength'].default_value = 3.0
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a[0]))
print('MATERIALS'); sys.stdout.flush(); os._exit(0)
