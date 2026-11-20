"""Blender side of the xatlas UV route (after hes_harvester_claude/scripts/xatlas_uv.py).
export: <blend> <out.npz>               -> positions / triangles of the triangulated 'Body'
apply:  <blend> <uv.npz> <out blend> <upload glb> -> UVs per triangle corner, head islands x2 (uv_head_density),
        islands re-packed (margin 0.003), neutral static upload for the retexture (no rig, no materials)."""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                'claude_shared'))
argv = sys.argv[sys.argv.index('--') + 1:]
mode, src = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=src)
ob = bpy.data.objects['Body']
me = ob.data
assert all(len(p.vertices) == 3 for p in me.polygons)
if mode == 'export':
    np.savez(argv[2], positions=np.array([tuple(v.co) for v in me.vertices], np.float32),
             triangles=np.array([list(p.vertices) for p in me.polygons], np.int32))
    print('EXPORTED', len(me.polygons))
    sys.exit(0)
from uv_head_density import scale_head_islands
uv = np.load(argv[2])['uv']
rig = bpy.data.objects['MM9_Rig']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
for layer in list(me.uv_layers):
    me.uv_layers.remove(layer)
layer = me.uv_layers.new(name='UVMap')
for p in me.polygons:
    for k, li in enumerate(p.loop_indices):
        layer.data[li].uv = tuple(uv[p.index, k])
bpy.context.view_layer.objects.active = ob
for o in bpy.data.objects:
    o.select_set(o == ob)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
scale_head_islands(ob, ('Xheadpiv', 'Xhead', 'Xjawbase', 'Xjawpivot', 'Xjaw', 'Xtongpiv', 'Xtong'), factor=2.0)
bpy.ops.uv.select_all(action='SELECT')
bpy.ops.uv.pack_islands(margin=0.003, rotate=True)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=argv[3])
dup = ob.copy(); dup.data = me.copy(); dup.modifiers.clear(); dup.parent = None
dup.matrix_world = ob.matrix_world
bpy.context.scene.collection.objects.link(dup)
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=argv[4], use_selection=True, export_format='GLB', export_yup=True,
                          export_skins=False, export_animations=False, export_materials='NONE', export_attributes=False)
print('APPLIED', len(me.polygons))
