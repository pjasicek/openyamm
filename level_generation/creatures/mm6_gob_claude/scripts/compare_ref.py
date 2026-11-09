"""Unlit textured renders framed like the reference crops. Args: basecolor tag."""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
args = sys.argv[sys.argv.index('--') + 1:]
base, tag = args[0], args[1]
rig = bpy.data.objects['Peasant_Rig']; rig.animation_data_create(); rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
m = bpy.data.objects['Peasant']
mat = bpy.data.materials.new('T'); mat.use_nodes = True
t = mat.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.abspath(base))
mat.node_tree.links.new(t.outputs[0], next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'])
m.data.materials.clear(); m.data.materials.append(mat)
for o in bpy.data.objects:
    if o.type == 'MESH': o.hide_render = o.name != 'Peasant'
lo, hi = common.world_bounds([m])
scene = bpy.context.scene; common.workbench_clay(scene, textured=True); scene.display.shading.light = 'FLAT'
H = hi.z - lo.z
common.render_views(os.path.join(common.REVIEW, f'{tag}_upper'), hi.z - H * 0.24, H * 0.5, views=('front',), resolution=(800, 800))
common.render_views(os.path.join(common.REVIEW, f'{tag}_full'), (lo.z + hi.z) / 2, H * 1.04, views=('front', 'left', 'back', 'right'), resolution=(520, 780))
