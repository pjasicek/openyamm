"""Export the rest-pose Peasant mesh (no rig/anim/knife) with the atlas UVs for Meshy retexturing."""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
out = sys.argv[sys.argv.index('--') + 1]
rig = bpy.data.objects['Peasant_Rig']; rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
src = bpy.data.objects['Peasant']
PARTS = json.loads(bpy.context.scene['pfem_parts'])
obj = src.copy(); obj.data = src.data.copy(); obj.name = 'PeasantNeutral'
bpy.context.scene.collection.objects.link(obj)
obj.parent = None
for m in list(obj.modifiers): obj.modifiers.remove(m)
obj.vertex_groups.clear()
part = np.zeros(len(obj.data.polygons), dtype=np.int32); obj.data.attributes['part'].data.foreach_get('value', part)
bm = bmesh.new(); bm.from_mesh(obj.data); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if part[f.index] == PARTS.index('Knife')], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(obj.data); bm.free()
obj.data.attributes.remove(obj.data.attributes['part'])
mat = bpy.data.materials.new('Neutral'); mat.use_nodes = True
obj.data.materials.clear(); obj.data.materials.append(mat)
for o in bpy.data.objects: o.select_set(o == obj)
bpy.context.view_layer.objects.active = obj
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_animations=False,
                          export_skins=False, export_morph=False, export_yup=True, export_attributes=False)
print('NEUTRAL', out, len(obj.data.polygons))
