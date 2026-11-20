"""Head upload for the Meshy head retexture: the head set's faces alone (face, eyes, hair, braid) with HeadUV as the UV layout,
no materials, bind pose. Args: <uv blend> <out glb>"""
import bpy, bmesh, sys
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
dup = body.copy(); dup.data = body.data.copy(); dup.modifiers.clear(); dup.parent = None; dup.matrix_world = body.matrix_world
bpy.context.scene.collection.objects.link(dup); dm = dup.data
mat = np.zeros(len(dm.polygons), np.int32); dm.attributes['mat'].data.foreach_get('value', mat)
bm = bmesh.new(); bm.from_mesh(dm); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if mat[f.index] != 1], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(dm); bm.free()
hu = dm.uv_layers['HeadUV']
for n in [l.name for l in dm.uv_layers if l.name != 'HeadUV']: dm.uv_layers.remove(dm.uv_layers[n])
hu.name = 'UVMap'
for g in list(dup.vertex_groups): dup.vertex_groups.remove(g)
for a in [a.name for a in dm.attributes if a.name in ('part', 'mat', 'hand', 'graft_s', 'graft_side', 'braid')]:
    dm.attributes.remove(dm.attributes[a])
m = bpy.data.materials.new('m'); dm.materials.clear(); dm.materials.append(m)
for o in bpy.data.objects: o.select_set(o is dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_animations=False, export_skins=False, export_yup=True, export_attributes=False, export_materials='EXPORT')
print('HEADUP', len(dm.polygons))
