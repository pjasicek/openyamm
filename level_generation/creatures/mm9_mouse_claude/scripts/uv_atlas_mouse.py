"""MM9 mouse UVs (claude_shared/uv_atlas.py, TEXTURE_QUALITY_PASS.md; from mm9_crow_claude/scripts/uv_atlas_v4.py):
xatlas charts packed into one 2048 atlas, head charts (Bone08 + Bone06) twice as dense, and the neutral static upload
for the 4K Meshy retexture. Runs on the reduced, weighted mesh (the last vertex move); mesh, weights and attributes
are unchanged. xatlas packs differently per run: never re-run once the upload went to Meshy.

Args: <in blend> <out blend> <upload glb> <report json> [key=value uv_atlas.unwrap options]
"""
import bpy, sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                'claude_shared'))
import uv_atlas

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, UPLOAD, REPORT = argv[:4]
options = {k: (float(v) if v.replace('.', '', 1).isdigit() and '.' in v else int(v) if v.isdigit() else v)
           for k, v in (a.split('=', 1) for a in argv[4:])}
HEAD = ('Bone08', 'Bone06')
bpy.ops.wm.open_mainfile(filepath=IN)
rig = bpy.data.objects['MM9_Rig']
mesh = bpy.data.objects['Body']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
report = uv_atlas.unwrap(mesh, head_groups=HEAD, head_factor=2.0, **options)
print('UV_ATLAS', json.dumps(report))
json.dump(report, open(REPORT, 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
os.makedirs(os.path.dirname(UPLOAD), exist_ok=True)
dup = mesh.copy(); dup.data = mesh.data.copy(); dup.modifiers.clear(); dup.parent = None
dup.matrix_world = mesh.matrix_world
bpy.context.scene.collection.objects.link(dup)
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=UPLOAD, use_selection=True, export_format='GLB', export_yup=True,
                          export_skins=False, export_animations=False, export_materials='NONE',
                          export_attributes=False)
print('UV done; upload', UPLOAD, len(mesh.data.polygons))
