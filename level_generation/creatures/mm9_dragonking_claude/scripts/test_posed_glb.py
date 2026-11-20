"""Test target for fit_dragon.py: the MM9 meshes posed at ACTION@FRAME, joined, exported as a static GLB.
Args: <src blend> <action@frame> <out glb>"""
import bpy, sys, bmesh
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
arm = bpy.data.objects['MM9_Rig']
name, f = argv[1].split('@')
arm.animation_data_create(); arm.animation_data.action = bpy.data.actions[name]
try:
    arm.animation_data.action_slot = bpy.data.actions[name].slots[0]
except Exception:
    pass
bpy.context.scene.frame_set(int(f))
dg = bpy.context.evaluated_depsgraph_get()
bm = bmesh.new()
for o in bpy.data.objects:
    if o.type == 'MESH':
        me = o.evaluated_get(dg).to_mesh()
        me.transform(o.matrix_world)
        bm.from_mesh(me)
        o.evaluated_get(dg).to_mesh_clear()
me = bpy.data.meshes.new('T'); bm.to_mesh(me)
ob = bpy.data.objects.new('T', me); bpy.context.scene.collection.objects.link(ob)
for o in bpy.data.objects:
    o.select_set(o == ob)
bpy.ops.export_scene.gltf(filepath=argv[2], use_selection=True, export_format='GLB', export_animations=False)
