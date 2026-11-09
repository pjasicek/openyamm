"""Untextured rig test export. Args: <blend> <out glb>"""
import bpy, sys
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data: rig.animation_data.action = None
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not body: bpy.data.objects.remove(o)
for an in list(bpy.data.actions): bpy.data.actions.remove(an)
for b in rig.pose.bones: b.matrix_basis.identity()
me = body.data
for x in [x.name for x in me.attributes if x.name in ('fitco', 'pid')]: me.attributes.remove(me.attributes[x])
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects: o.select_set(o == body)
bpy.ops.object.shade_smooth()
lift = -min((body.matrix_world @ v.co).z for v in me.vertices)
rig.location.z += lift
bpy.context.view_layer.update(); print('LIFT', lift)
for o in bpy.data.objects: o.select_set(o in (body, rig))
bpy.ops.export_scene.gltf(filepath=a[1], export_format='GLB', use_selection=True, export_animations=False, export_skins=True, export_yup=True, export_materials='NONE', export_attributes=False)
