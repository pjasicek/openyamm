"""Export the rigged body (no clips) for clips_mm9.py. Args: <blend> <out glb> [object name]"""
import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
name = argv[2] if len(argv) > 2 else 'Body'
arm = bpy.data.objects['MM9_Rig']
if arm.animation_data:
    arm.animation_data.action = None
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
for o in bpy.data.objects:
    o.select_set(o.name in (name, 'MM9_Rig') or (o.parent is not None and o.parent.name == 'MM9_Rig' and o.type == 'EMPTY'))
bpy.ops.export_scene.gltf(filepath=argv[1], export_format='GLB', use_selection=True, export_animations=False,
                          export_skins=True, export_all_influences=False, export_yup=True)
print('EXPORTED', argv[1])
