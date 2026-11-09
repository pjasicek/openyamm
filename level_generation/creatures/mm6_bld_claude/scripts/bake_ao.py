"""Bake a short-range ambient-occlusion map (rest pose, 4 cm reach) into textures/bld_ao_2k.png. The sprites carry
painted crevice shading; compose_bld.py multiplies this into the base colour so features read under flat lighting."""
import bpy, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mesh = bpy.data.objects['Bld']; rig = bpy.data.objects['Bld_Rig']
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 96
if sc.world is None:
    sc.world = bpy.data.worlds.new('w')
sc.world.light_settings.distance = 0.04
img = bpy.data.images.new('ao', 2048, 2048, alpha=False, float_buffer=False)
mat = bpy.data.materials.new('bake'); mat.use_nodes = True
node = mat.node_tree.nodes.new('ShaderNodeTexImage'); node.image = img; mat.node_tree.nodes.active = node
mesh.data.materials.clear(); mesh.data.materials.append(mat)
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.context.view_layer.objects.active = mesh
sc.render.bake.margin = 8
bpy.ops.object.bake(type='AO')
img.filepath_raw = os.path.join(HERE, 'textures', 'bld_ao_2k.png'); img.file_format = 'PNG'; img.save()
print('BAKED', img.filepath_raw)
