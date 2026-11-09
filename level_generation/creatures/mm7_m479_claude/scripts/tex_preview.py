"""Assign a base-colour image to 'Body' for Workbench texture previews. Args: -- <in blend> <image> <out blend>"""
import bpy, os, sys
src, img, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Body']
m = bpy.data.materials.new('Preview'); m.use_nodes = True; nt = m.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.abspath(img))
nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
body.data.materials.clear(); body.data.materials.append(m)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
print('PREVIEW', out)
