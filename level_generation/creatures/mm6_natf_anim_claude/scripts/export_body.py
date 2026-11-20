"""Skinned body of a skirt_skin.py blend -> GLB for swap_lod0.py (node Natf, no clips, up to 8 influences, custom normals).
Usage: blender -b -P export_body.py -- <blend> <out.glb>"""
import os, sys, bpy
blend, out = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
body.name = 'Natf'
for o in bpy.data.objects:
    o.select_set(o in (rig, body))
bpy.ops.export_scene.gltf(filepath=os.path.abspath(out), use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=False, export_skins=True, export_all_influences=True, export_normals=True,
                          export_attributes=False, export_morph=False, export_image_format='NONE')
print('EXPORTED', sum(len(p.vertices) - 2 for p in body.data.polygons))
