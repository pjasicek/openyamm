"""Sharp-texture UVs (claude_shared/TEXTURE_QUALITY_PASS.md): xatlas charts packed by claude_shared/uv_atlas.py on
the reduced, weighted 'Body', head charts denser, then the neutral static upload GLB for the 4K Meshy retexture.
Mesh, weights and attributes are unchanged. xatlas packs differently per run: never re-run once the upload went to
Meshy (the retexture is only valid on that exact layout).

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
HEAD = ('Xheadpiv', 'Xhead', 'Xjawpiv', 'Xearpiv', 'Xear', 'Xearpiv01', 'Xear01')
HEAD_FACTOR = float(os.environ.get('HEAD_FACTOR', '1.8'))
bpy.ops.wm.open_mainfile(filepath=IN)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
mesh = bpy.data.objects['Body']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
report = uv_atlas.unwrap(mesh, head_groups=HEAD, head_factor=HEAD_FACTOR, **options)
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
