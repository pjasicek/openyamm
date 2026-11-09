"""Rest-pose AO for both natm texture layouts (claude_shared/bake_creature_ao.py settings: Cycles, 3 cm reach).
UVMap: the whole body -> work/ao_UVMap.png. HeadUV: the whole body as occluder, non-head faces parked in a 1-texel
corner of the head layout -> work/ao_HeadUV.png. Args: -- <blend> [size]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); size = int(a[1]) if len(a) > 1 else 1024
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
sc = bpy.context.scene
try:
    sc.render.engine = 'CYCLES'
except TypeError:
    pass
sc.cycles.device = 'CPU'; sc.cycles.samples = 64
if sc.world is None: sc.world = bpy.data.worlds.new('w')
sc.world.light_settings.distance = 0.03
me = body.data
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
hl = me.uv_layers['HeadUV'].data
bl = me.uv_layers['UVMap'].data
for p in me.polygons:
    if not hd[p.index]:
        for li in p.loop_indices: hl[li].uv = (0.9995, 0.9995)
    else:   # head faces keep stray UVMap coordinates (the layer was created from HeadUV): park them too, or the
        for li in p.loop_indices: bl[li].uv = (0.9995, 0.9995)   # enclosed eye shells bake black onto body islands
for o in bpy.data.objects: o.select_set(o == body)
bpy.context.view_layer.objects.active = body
sc.render.bake.margin = 8; sc.render.bake.use_selected_to_active = False
for layer in ('UVMap', 'HeadUV'):
    img = bpy.data.images.new('ao_' + layer, size, size, alpha=False)
    mat = bpy.data.materials.new('bake'); mat.use_nodes = True
    n = mat.node_tree.nodes.new('ShaderNodeTexImage'); n.image = img; mat.node_tree.nodes.active = n
    me.materials.clear(); me.materials.append(mat)
    me.uv_layers.active = me.uv_layers[layer]
    for uvl in me.uv_layers: uvl.active_render = (uvl.name == layer)
    bpy.ops.object.bake(type='AO')
    img.filepath_raw = os.path.join(HERE, 'work', f'ao_{layer}.png'); img.file_format = 'PNG'; img.save()
    print('AO', layer, img.filepath_raw)
