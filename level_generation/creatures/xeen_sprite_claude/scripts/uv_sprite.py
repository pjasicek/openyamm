"""Body UVs for the 4K retexture (claude_shared/TEXTURE_QUALITY_PASS.md section 0, uv_atlas.py defaults: PartUV charts,
seam pass, sparrow packing), head islands HEAD_FACTOR denser, then the neutral static upload. The mesh is final
(rigged, weighted, reduced); it is triangulated here (weights are per vertex and survive).
Args: -- <in blend> <out blend> <upload glb> <report json>"""
import bpy, bmesh, sys, os, json
import os as _os; _os.chdir(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))  # project-relative paths
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'claude_shared'))
import uv_atlas
IN, OUT, UPLOAD, REPORT = sys.argv[sys.argv.index('--') + 1:]
HF = float(os.environ.get('HEAD_FACTOR', 2.0))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(IN))
rig = bpy.data.objects['Rig']; mesh = bpy.data.objects['Body']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
bm = bmesh.new(); bm.from_mesh(mesh.data)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.to_mesh(mesh.data); bm.free()
mesh.data.materials.clear()
report = uv_atlas.unwrap(mesh, head_groups=('B_Head', 'B_Neck'), head_factor=HF, vis_objects=(bpy.data.objects['Wings'],))
print('UV_ATLAS', json.dumps({k: v for k, v in report.items() if k not in ('seam_log',)})[:1500])
json.dump(report, open(os.path.abspath(REPORT), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUT))
dup = mesh.copy(); dup.data = mesh.data.copy(); dup.modifiers.clear(); dup.parent = None
dup.matrix_world = mesh.matrix_world
bpy.context.scene.collection.objects.link(dup)
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
os.makedirs(os.path.dirname(os.path.abspath(UPLOAD)), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=os.path.abspath(UPLOAD), use_selection=True, export_format='GLB', export_yup=True,
                          export_skins=False, export_animations=False, export_materials='NONE', export_attributes=False)
print('UVDONE upload', UPLOAD, len(mesh.data.polygons))
