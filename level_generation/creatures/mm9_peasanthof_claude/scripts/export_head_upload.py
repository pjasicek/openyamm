"""Head-only upload for a fresh Meshy head retexture on the CURRENT master (positions after every geometry fix; the
paid UV layout HeadUV unchanged): faces with head = 1 and hand = 0, HeadUV as the only UV layer, no rig, no materials.
Args: <in blend> <out glb>"""
import bpy, bmesh, sys
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; rig = ob.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = ob.data.copy(); new = bpy.data.objects.new('HeadUpload', me); bpy.context.scene.collection.objects.link(new)
new.matrix_world = ob.matrix_world.copy()
bm = bmesh.new(); bm.from_mesh(me)
lh, lk = bm.faces.layers.int['hand'], bm.faces.layers.int['head']
bmesh.ops.delete(bm, geom=[f for f in bm.faces if not (f[lk] == 1 and f[lh] == 0)], context='FACES')
bm.to_mesh(me); me.update()
for name in [u.name for u in me.uv_layers if u.name != 'HeadUV']:
    me.uv_layers.remove(me.uv_layers[name])
me.uv_layers['HeadUV'].name = 'UVMap'
me.materials.clear(); new.vertex_groups.clear()
for o in bpy.data.objects: o.select_set(o is new)
bpy.context.view_layer.objects.active = new
bpy.ops.export_scene.gltf(filepath=a[1], use_selection=True, export_skins=False, export_animations=False, export_materials='NONE')
print('HEAD_UPLOAD faces', len(me.polygons))
