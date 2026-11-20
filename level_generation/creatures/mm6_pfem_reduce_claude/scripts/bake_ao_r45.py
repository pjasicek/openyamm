"""AO of the rest-pose 45 % peasant, one image per texture set (their UVs overlap): work/ao.png (body, 2048) and
work/ao_head.png (head, 1024)."""
import os, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'r45_master.blend'))
rig = bpy.data.objects['Peasant_Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
m = bpy.data.objects['Peasant']; m.hide_render = False; m.hide_viewport = False; m.hide_set(False)
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o != m:
        bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 64
sc.world = sc.world or bpy.data.worlds.new('W'); sc.world.light_settings.distance = 0.06
head = [a.value for a in m.data.attributes['head'].data]
m.data.materials.clear(); images = []
for label, size in (('body', 2048), ('head', 1024)):
    mat = bpy.data.materials.new('AO_' + label); mat.use_nodes = True; m.data.materials.append(mat)
    img = bpy.data.images.new('ao_' + label, size, size, alpha=False); img.colorspace_settings.name = 'Non-Color'
    t = mat.node_tree.nodes.new('ShaderNodeTexImage'); t.image = img; mat.node_tree.nodes.active = t; images.append((label, img))
m.data.polygons.foreach_set('material_index', head)
for o in bpy.data.objects:
    o.select_set(o == m)
bpy.context.view_layer.objects.active = m
bpy.ops.object.bake(type='AO', margin=8)
for label, img in images:
    img.filepath_raw = os.path.join(HERE, 'work', 'ao.png' if label == 'body' else 'ao_head.png'); img.file_format = 'PNG'; img.save()
print('AO baked')
