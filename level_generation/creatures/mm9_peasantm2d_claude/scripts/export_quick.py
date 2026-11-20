"""Rigged body without textures, UVs unused, for gates. Args: <blend> <out glb>"""
import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data: rig.animation_data.action = None
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
for pb in rig.pose.bones: pb.matrix_basis.identity()
for a in [a.name for a in body.data.attributes if a.name in ('part',)]:
    pass
body.name = 'PeasantM2'
lift = -min((body.matrix_world @ v.co).z for v in body.data.vertices)
print('LIFT', lift)
rig.location.z += lift
bpy.context.view_layer.update()
for o in bpy.data.objects: o.select_set(o in (body, rig))
bpy.ops.export_scene.gltf(filepath=argv[1], export_format='GLB', use_selection=True, export_animations=False, export_skins=True, export_all_influences=False, export_yup=True, export_attributes=False)
print('EXPORTED', argv[1])
