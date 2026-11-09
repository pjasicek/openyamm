"""Rest-pose AO for the griffin's UVMap (claude_shared/bake_creature_ao.py settings: Cycles, 3 cm reach, 64 samples)
-> work/ao_UVMap.png. Args: -- <blend> [size]"""
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); size = int(a[1]) if len(a) > 1 else 2048
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
rig.animation_data_create(); rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 64
if sc.world is None: sc.world = bpy.data.worlds.new('w')
sc.world.light_settings.distance = 0.03
me = body.data
for o in bpy.data.objects: o.select_set(o == body)
bpy.context.view_layer.objects.active = body
sc.render.bake.margin = 8; sc.render.bake.use_selected_to_active = False
img = bpy.data.images.new('ao', size, size, alpha=False)
mat = bpy.data.materials.new('bake'); mat.use_nodes = True
n = mat.node_tree.nodes.new('ShaderNodeTexImage'); n.image = img; mat.node_tree.nodes.active = n
me.materials.clear(); me.materials.append(mat)
bpy.ops.object.bake(type='AO')
img.filepath_raw = os.path.join(HERE, 'work', 'ao_UVMap.png'); img.file_format = 'PNG'; img.save()
print('AO', img.filepath_raw)
