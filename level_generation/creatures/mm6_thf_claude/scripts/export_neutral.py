"""Export the rest-pose Thief mesh (no rig or animation) with its atlas UVs for Meshy retexturing; the daggers are left
out (they take colour swatches at export, not Meshy paint).
Usage: blender --background work/<master>.blend --python export_neutral.py -- <out.glb>"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[sys.argv.index('--') + 1]
rig = bpy.data.objects['Thief_Rig']
rig.animation_data_create()
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
src = bpy.data.objects['Thief']
obj = src.copy()
obj.data = src.data.copy()
obj.name = 'ThiefNeutral'
bpy.context.scene.collection.objects.link(obj)
obj.parent = None
obj.matrix_world = src.matrix_world.copy()
for m in list(obj.modifiers):
    obj.modifiers.remove(m)
obj.vertex_groups.clear()
import bmesh, json
parts = json.loads(bpy.context.scene['thf_parts'])
bm = bmesh.new(); bm.from_mesh(obj.data); pl = bm.faces.layers.int['part']
bmesh.ops.delete(bm, geom=[f for f in bm.faces if parts[f[pl]] == 'Dagger'], context='FACES')
bm.to_mesh(obj.data); bm.free()
for a in [a.name for a in obj.data.attributes if a.name in ('part', 'uv_region', 'hid', 'head')]:
    obj.data.attributes.remove(obj.data.attributes[a])
mat = bpy.data.materials.new('Neutral')
mat.use_nodes = True
obj.data.materials.clear()
obj.data.materials.append(mat)
for o in bpy.data.objects:
    o.select_set(o == obj)
bpy.context.view_layer.objects.active = obj
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_animations=False,
                          export_skins=False, export_morph=False, export_yup=True, export_attributes=False)
print('NEUTRAL', out, len(obj.data.polygons), 'faces')
