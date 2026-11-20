"""AO bake into one UV layer of 'Body' (2026-10-30 rework; after ../claude_shared/bake_creature_ao.py, Cycles CPU, rest
pose, whole mesh as occluder). Faces outside the chosen set bake into a throwaway image, so the head atlas (HeadUV) is
not touched by body faces and vice versa.
Args: <blend> <uv layer> <face set: body|head> <out.png> [reach_m] [size]"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
layer, which, out = a[1], a[2], a[3]
reach = float(a[4]) if len(a) > 4 else 0.05
size = int(a[5]) if len(a) > 5 else 2048
mesh = bpy.data.objects['Body']
for rig in (o for o in bpy.data.objects if o.type == 'ARMATURE'):
    if rig.animation_data:
        rig.animation_data.action = None
    for b in rig.pose.bones:
        b.matrix_basis.identity()
bpy.context.view_layer.update()
me = mesh.data
for uv in me.uv_layers:
    uv.active_render = uv.name == layer
me.uv_layers.active = me.uv_layers[layer]
head = np.zeros(len(me.polygons), np.int32)
me.attributes['head'].data.foreach_get('value', head)
keep = (head > 0) if which == 'head' else (head == 0)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 96
if sc.world is None:
    sc.world = bpy.data.worlds.new('w')
sc.world.light_settings.distance = reach
me.materials.clear()
for nm, sz in (('bake', size), ('dummy', 16)):
    img = bpy.data.images.new(nm, sz, sz, alpha=False, float_buffer=False)
    mat = bpy.data.materials.new(nm); mat.use_nodes = True
    node = mat.node_tree.nodes.new('ShaderNodeTexImage'); node.image = img; mat.node_tree.nodes.active = node
    me.materials.append(mat)
me.polygons.foreach_set('material_index', np.where(keep, 0, 1).tolist())
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.context.view_layer.objects.active = mesh
sc.render.bake.margin = 8
sc.render.bake.use_selected_to_active = False
bpy.ops.object.bake(type='AO')
img = bpy.data.images['bake']
img.filepath_raw = out; img.file_format = 'PNG'; img.save()
print('BAKED', out, layer, which, int(keep.sum()))
