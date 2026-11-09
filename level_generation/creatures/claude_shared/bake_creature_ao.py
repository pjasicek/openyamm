"""Bake a short-range ambient-occlusion map for a creature mesh in its rest pose (Blender, Cycles CPU).
Usage: blender --background <authoring.blend> --python bake_creature_ao.py -- <mesh object> <out.png> [reach_m] [size]
The blend is not saved. grade_basecolor.py multiplies the result into the tier base colours, so crevices read like
the sprites' painted shading under flat game lighting."""
import bpy, sys
args = sys.argv[sys.argv.index('--') + 1:]
mesh = bpy.data.objects[args[0]]
out = args[1]
reach = float(args[2]) if len(args) > 2 else 0.04
size = int(args[3]) if len(args) > 3 else 2048
for rig in (o for o in bpy.data.objects if o.type == 'ARMATURE'):
    if rig.animation_data:
        rig.animation_data.action = None
    for b in rig.pose.bones:
        b.matrix_basis.identity()
bpy.context.view_layer.update()
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 96
if sc.world is None:
    sc.world = bpy.data.worlds.new('w')
sc.world.light_settings.distance = reach
img = bpy.data.images.new('ao', size, size, alpha=False, float_buffer=False)
mat = bpy.data.materials.new('bake'); mat.use_nodes = True
node = mat.node_tree.nodes.new('ShaderNodeTexImage'); node.image = img; mat.node_tree.nodes.active = node
mesh.data.materials.clear(); mesh.data.materials.append(mat)
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.context.view_layer.objects.active = mesh
sc.render.bake.margin = 8
sc.render.bake.use_selected_to_active = False  # scenes saved after a high-to-low bake keep this on
bpy.ops.object.bake(type='AO')
img.filepath_raw = out; img.file_format = 'PNG'; img.save()
print('BAKED', out)
