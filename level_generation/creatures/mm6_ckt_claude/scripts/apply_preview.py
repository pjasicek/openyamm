"""Assign the (ungraded or graded) base colour to 'Robot' for textured Workbench previews. Args: basecolor_png"""
import bpy, sys
img = bpy.data.images.load(sys.argv[sys.argv.index('--') + 1])
mat = bpy.data.materials.new('Preview'); mat.use_nodes = True; nt = mat.node_tree
n = nt.nodes.new('ShaderNodeTexImage'); n.image = img
nt.links.new(n.outputs['Color'], next(x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED').inputs['Base Color'])
me = bpy.data.objects['Cockatrice'].data; me.materials.clear(); me.materials.append(mat)
