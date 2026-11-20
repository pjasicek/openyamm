"""Preview glow on a shell material: Emission Color = the glow colour, Emission Strength = the glow mask (the runtime
uses claude_shared/emission.py). Usage (Blender): preview_glow.py <blend> <material> <mask.png> <r,g,b> [strength]"""
import bpy, sys
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=args[0])
m = bpy.data.materials[args[1]]; nt = m.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
for l in list(bsdf.inputs['Emission Color'].links) + list(bsdf.inputs['Emission Strength'].links):
    nt.links.remove(l)
node = next((n for n in nt.nodes if n.type == 'TEX_IMAGE' and n.label == 'glow'), None) or nt.nodes.new('ShaderNodeTexImage')
node.label = 'glow'
img = bpy.data.images.load(args[2], check_existing=False); img.colorspace_settings.name = 'Non-Color'; node.image = img
mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = float(args[4]) if len(args) > 4 else 3.0
nt.links.new(node.outputs['Color'], mul.inputs[0]); nt.links.new(mul.outputs[0], bsdf.inputs['Emission Strength'])
bsdf.inputs['Emission Color'].default_value = (*[float(x) for x in args[3].split(',')], 1)
bpy.ops.wm.save_as_mainfile(filepath=args[0])
