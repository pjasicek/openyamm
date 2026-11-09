"""UVs for 'Body' (Smart UV Project, head islands denser) and the neutral static upload for the retexture.

Args: <in blend> <body: lobber|pod> <out blend> <upload glb>
The upload is the body in the bind pose (small pieces included), no rig, no materials; the Dagrell's in its fitted
Stand-like pose (action FitPose), matching its HD views.
"""
import bpy, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                'claude_shared'))
from uv_head_density import scale_head_islands

argv = sys.argv[sys.argv.index('--') + 1:]
IN, BODY, OUT, UPLOAD = argv
HEAD = {'lobber': (('Xheadpiv', 'Xhead', 'Xheadmid', 'Xjawbase', 'Xjawpiv', 'Xjaw', 'Xmouth', 'Xchin'), 2.0),
        'pod': (('XCENTER', 'Xhinge', 'Xheadpiv', 'Xhead', 'Xmouth', 'Xjawpiv', 'Xjaw'), 1.6),
        'nagate': (('Xneck', 'Xhead', 'Xjaw', 'Xjawmid', 'Xjaw01', 'Xjawmid01'), 1.8),
        'dagrell': (('Xheadpiv', 'Xjawbase', 'Xjawpiv', 'Xnose'), 1.8)}[BODY]
bpy.ops.wm.open_mainfile(filepath=IN)
rig = bpy.data.objects['MM9_Rig']
mesh = bpy.data.objects['Body']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
for uv in list(mesh.data.uv_layers):
    mesh.data.uv_layers.remove(uv)
mesh.data.uv_layers.new(name='UVMap')
bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.004, area_weight=0.0, scale_to_bounds=False)
scale_head_islands(mesh, HEAD[0], factor=HEAD[1])
bpy.ops.uv.pack_islands(margin=0.004, rotate=True)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
os.makedirs(os.path.dirname(UPLOAD), exist_ok=True)
if BODY == 'dagrell':
    # the Dagrell's HD views show the MM9 Stand pose, not its crouched bind pose: upload the mesh in the pose fitted
    # to the Meshy return (action FitPose from fit_dagrell.py), same UVs
    fp = bpy.data.actions['FitPose']
    rig.animation_data_create(); rig.animation_data.action = fp
    try:
        rig.animation_data.action_slot = fp.slots[0]
    except Exception:
        pass
    bpy.context.scene.frame_set(0); bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    posed = bpy.data.meshes.new_from_object(mesh.evaluated_get(dg))
    dup = bpy.data.objects.new('DagrellUpload', posed)
    dup.matrix_world = mesh.matrix_world
else:
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
