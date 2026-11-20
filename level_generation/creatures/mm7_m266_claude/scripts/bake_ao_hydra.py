"""Rest-pose ambient occlusion for both texture sets (Cycles AO bake, DIST m reach): the body into a BODY x BODY image
through UVMap on part-0 faces, the heads into a HEADS_W x HEADS_H atlas image on part>0 faces (the two sets share UV
space, so each gets its own material and image). Writes work/ao_body.png and work/ao_heads.png. Args: -- <blend>"""
import bpy, sys, os
import numpy as np
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST, BODY, HEADS_W, HEADS_H = 0.04, 2048, 1536, 1024
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; ob = bpy.data.objects['Body']; me = ob.data
rig.animation_data_create(); rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 64
if sc.world is None:
    sc.world = bpy.data.worlds.new('w')
sc.world.light_settings.distance = DIST
sc.render.bake.margin = 8; sc.render.bake.use_selected_to_active = False
imgs = {}
me.materials.clear()
for name, (w, h) in (('BakeBody', (BODY, BODY)), ('BakeHeads', (HEADS_W, HEADS_H))):
    img = bpy.data.images.new(name, w, h, alpha=False); imgs[name] = img
    m = bpy.data.materials.new(name); m.use_nodes = True
    n = m.node_tree.nodes.new('ShaderNodeTexImage'); n.image = img; m.node_tree.nodes.active = n
    me.materials.append(m)
part = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', part)
me.polygons.foreach_set('material_index', (part > 0).astype(np.int32))
for o in bpy.data.objects:
    o.select_set(o == ob)
bpy.context.view_layer.objects.active = ob
bpy.ops.object.bake(type='AO')
for name, out in (('BakeBody', 'ao_body.png'), ('BakeHeads', 'ao_heads.png')):
    imgs[name].filepath_raw = os.path.join(HERE, 'work', out); imgs[name].file_format = 'PNG'; imgs[name].save()
print('AO baked')
