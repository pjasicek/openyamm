"""Step 1 for a batch-B Smart Topology return (work/st_v1_parts.blend, loose parts P00.., 1.7 m, faces -Y):
join every part into 'Body' with the 'piece' point attribute (part index), 'garment' (label below) and 'orig_co';
give it a neutral textured material (Meshy's rigging wants a textured humanoid) and export the PERSON only (no
crescent, back frame, banners or beads: the two banners read as extra limbs to an auto-rig) to work/body_for_rig.glb.
Garments: creature.json (numbering in cfg.py).
Args: none"""
import bpy, os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import cfg
G, LAB, BACK = cfg.GARMENTS, cfg.LAB, cfg.NOT_IN_RIG
# m422: the cleaned parts (clean_parts.py: sticks removed, stray triangle deleted, per-vertex piece override 'piece_ov'
# on the coat shell for the cape 27, collar 28 and skirt 29)
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'st_v1_clean.blend'))
parts = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
_ids = {int(n[1:]) for n in parts}
for o in parts.values():
    if 'piece_ov' in o.data.attributes:
        _ids |= {a.value for a in o.data.attributes['piece_ov'].data if a.value}
assert _ids == set(LAB), ('unlabelled pieces', sorted(_ids - set(LAB)), 'labels without piece', sorted(set(LAB) - _ids))
for o in bpy.data.objects:
    o.select_set(False)
for n, o in parts.items():
    i = int(n[1:])
    pcs = [i] * len(o.data.vertices)
    if 'piece_ov' in o.data.attributes:
        pcs = [a.value or i for a in o.data.attributes['piece_ov'].data]
        o.data.attributes.remove(o.data.attributes['piece_ov'])
    o.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', pcs)
    o.data.attributes.new('garment', 'INT', 'POINT').data.foreach_set('value', [LAB[k] for k in pcs])
    o.data.materials.clear(); o.select_set(True)
bpy.context.view_layer.objects.active = parts['P00']
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = body.data.name = 'Body'
me = body.data
co = np.array([tuple(v.co) for v in me.vertices])
me.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
mat = bpy.data.materials.new('RigNeutral'); mat.use_nodes = True
img = bpy.data.images.new('RigNeutral', width=4, height=4); img.pixels = [.55, .5, .45, 1] * 16; img.pack()
node = mat.node_tree.nodes.new('ShaderNodeTexImage'); node.image = img
mat.node_tree.links.new(node.outputs['Color'], mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
me.materials.append(mat)
if not me.uv_layers:
    me.uv_layers.new(name='UVMap')
for uv in me.uv_layers.active.data:
    uv.uv = (.5, .5)
gv = np.zeros(len(co), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
print('PREP verts', len(co), 'tris', sum(len(p.vertices) - 2 for p in me.polygons), 'height', round(float(co[:, 2].max() - co[:, 2].min()), 3),
      'garments', {g: int((gv == g).sum()) for g in G})
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'step1.blend'))
# person-only copy for the auto-rig
cp = body.copy(); cp.data = body.data.copy(); bpy.context.scene.collection.objects.link(cp)
import bmesh
bm = bmesh.new(); bm.from_mesh(cp.data); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[v for v in bm.verts if gv[v.index] in BACK], context='VERTS')
bm.to_mesh(cp.data); bm.free()
for o in bpy.data.objects:
    o.select_set(o == cp)
bpy.context.view_layer.objects.active = cp
bpy.ops.export_scene.gltf(filepath=os.path.join(common.WORK, 'body_for_rig.glb'), use_selection=True, export_format='GLB',
                          export_animations=False, export_skins=False, export_attributes=False, export_yup=True)
print('PREP rig upload verts', len(cp.data.vertices))
