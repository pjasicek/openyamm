"""Short-range ambient occlusion of the installed body's LOD0 in its rest pose, baked into the shared atlas layout
(2080x1024: body left, head right), for detail_pass.py. Adapted from claude_shared/bake_creature_ao.py, which bakes
square maps from an authoring blend.
Usage: blender -b -P bake_ao.py -- <body.glb> <out.png> [reach_m]"""
import bpy, sys
args = sys.argv[sys.argv.index('--') + 1:]
glb, out = args[0], args[1]
reach = float(args[2]) if len(args) > 2 else 0.05
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
body = max(meshes, key=lambda o: len(o.data.vertices))  # LOD0 (the importer also adds a bone-shape Icosphere)
for o in meshes:
    if o is not body:
        bpy.data.objects.remove(o)
for rig in (o for o in bpy.data.objects if o.type == 'ARMATURE'):
    if rig.animation_data:
        rig.animation_data.action = None
    for b in rig.pose.bones:
        b.matrix_basis.identity()
bpy.context.view_layer.update()
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 128
sc.world = bpy.data.worlds.new('w')
sc.world.light_settings.distance = reach
img = bpy.data.images.new('ao', 2080, 1024, alpha=False, float_buffer=False)
mat = bpy.data.materials.new('bake'); mat.use_nodes = True
node = mat.node_tree.nodes.new('ShaderNodeTexImage'); node.image = img; mat.node_tree.nodes.active = node
body.data.materials.clear(); body.data.materials.append(mat)
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
sc.render.bake.margin = 8
sc.render.bake.use_selected_to_active = False
bpy.ops.object.bake(type='AO')
img.filepath_raw = out; img.file_format = 'PNG'; img.save()
print('BAKED', out, body.name)
