"""Short-range AO in the rest pose for one material's faces (Bone or Head have overlapping 0..1 layouts, so each is baked
alone while every other piece still occludes it), after claude_shared/bake_creature_ao.py. Also writes the UV layout
(triangles per material) to work/uv_layout.json for the texture compose step.
Args: -- <blend> <material> <out png> [reach_m] [size]"""
import bpy, sys, json, os
a = sys.argv[sys.argv.index('--') + 1:]
blend, which, out = a[:3]
reach = float(a[3]) if len(a) > 3 else 0.03
size = int(a[4]) if len(a) > 4 else 1024
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Skeleton_Rig']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
mesh = bpy.data.objects['Skeleton']; me = mesh.data
uv = me.uv_layers['UVMap'].data
layout = {}
for p in me.polygons:
    name = me.materials[p.material_index].name
    layout.setdefault(name, []).append([list(uv[l].uv) for l in p.loop_indices])
json.dump(layout, open(os.path.join(os.path.dirname(os.path.abspath(blend)), 'uv_layout.json'), 'w'))
target = list(me.materials).index(me.materials[which])
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 96
if sc.world is None:
    sc.world = bpy.data.worlds.new('w')
sc.world.light_settings.distance = reach
img = bpy.data.images.new('ao', size, size, alpha=False, float_buffer=False)
bake = bpy.data.materials.new('bake'); bake.use_nodes = True
node = bake.node_tree.nodes.new('ShaderNodeTexImage'); node.image = img; bake.node_tree.nodes.active = node
dummy = bpy.data.materials.new('dummy'); dummy.use_nodes = True        # other faces: no image node to bake into
dn = dummy.node_tree.nodes.new('ShaderNodeTexImage'); dn.image = bpy.data.images.new('x', 8, 8)
dummy.node_tree.nodes.active = dn
idx = [p.material_index for p in me.polygons]
me.materials.clear(); me.materials.append(dummy); me.materials.append(bake)
me.polygons.foreach_set('material_index', [1 if i == target else 0 for i in idx])
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.context.view_layer.objects.active = mesh
sc.render.bake.margin = 8
sc.render.bake.use_selected_to_active = False
bpy.ops.object.bake(type='AO')
img.filepath_raw = os.path.abspath(out); img.file_format = 'PNG'; img.save()
print('BAKED', which, out)
