"""Rest-pose AO for both Medusa texture sets (claude_shared/bake_creature_ao.py settings: Cycles, 3 cm reach, 64
samples): the body faces bake into work/ao_BODY.png (2K), the head faces (face attribute head) into work/ao_HEAD.png
(1K) - one material slot per set, so the overlapping 0..1 layouts do not overwrite each other. Props are not baked.
Args: <blend>"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
rig.animation_data_create(); rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not body:
        o.hide_render = True
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 64
if sc.world is None:
    sc.world = bpy.data.worlds.new('w')
sc.world.light_settings.distance = 0.03
me = body.data
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
imgs = {}
me.materials.clear()
for k, (name, size) in enumerate((('BODY', 2048), ('HEAD', 1024))):
    img = bpy.data.images.new('ao_' + name, size, size, alpha=False); imgs[name] = img
    mat = bpy.data.materials.new('bake_' + name); mat.use_nodes = True
    n = mat.node_tree.nodes.new('ShaderNodeTexImage'); n.image = img; mat.node_tree.nodes.active = n
    me.materials.append(mat)
me.polygons.foreach_set('material_index', hd.astype(np.int32))
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
sc.render.bake.margin = 8; sc.render.bake.use_selected_to_active = False
bpy.ops.object.bake(type='AO')
for name, img in imgs.items():
    img.filepath_raw = os.path.join(HERE, 'work', f'ao_{name}.png'); img.file_format = 'PNG'; img.save()
    print('AO', img.filepath_raw)
