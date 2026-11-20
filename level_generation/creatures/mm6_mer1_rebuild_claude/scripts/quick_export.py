"""Untextured skinned export of a rig blend for motion checks. Args: <blend> <out glb>"""
import bpy, sys
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data: rig.animation_data.action = None
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
for b in rig.pose.bones: b.matrix_basis.identity()
me = body.data
for p in me.polygons: p.use_smooth = True
m = bpy.data.materials.new('Grey'); m.use_nodes = True
next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (0.7, 0.62, 0.42, 1)
me.materials.clear(); me.materials.append(m)
lift = -min((body.matrix_world @ v.co).z for v in me.vertices)
rig.location.z += lift
bpy.context.view_layer.update()
print('LIFT', lift)
for o in bpy.data.objects: o.select_set(o in (body, rig))
body.name = 'Guard'
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_animations=False, export_skins=True, export_yup=True, export_attributes=False)
