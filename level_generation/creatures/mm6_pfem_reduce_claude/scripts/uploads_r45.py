"""Meshy uploads of the 45 % master (rest pose, neutral material): texturing/pfem_r45_body_upload.glb (body set
without the knife, which compose paints) and texturing/pfem_r45_head_upload.glb (head set)."""
import os, json, bmesh, bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'r45_master.blend'))
rig = bpy.data.objects['Peasant_Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
src = bpy.data.objects['Peasant']; PARTS = json.loads(bpy.context.scene['pfem_parts'])
head = np.array([a.value for a in src.data.attributes['head'].data]); part = np.array([a.value for a in src.data.attributes['part'].data])
for label, keep in (('body', (head == 0) & (part != PARTS.index('Knife'))), ('head', head == 1)):
    obj = src.copy(); obj.data = src.data.copy(); obj.parent = None; obj.modifiers.clear(); obj.vertex_groups.clear()
    bpy.context.scene.collection.objects.link(obj)
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not keep[f.index]], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(obj.data); bm.free()
    for name in [a.name for a in obj.data.attributes if a.name in ('part', 'head', 'uv_seam')]:
        obj.data.attributes.remove(obj.data.attributes[name])
    mat = bpy.data.materials.new('Neutral'); mat.use_nodes = True; obj.data.materials.clear(); obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.material_index = 0
    for o in bpy.data.objects:
        o.select_set(o == obj)
    bpy.context.view_layer.objects.active = obj
    out = os.path.join(HERE, 'texturing', f'pfem_r45_{label}_upload.glb')
    bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_animations=False,
                              export_skins=False, export_morph=False, export_yup=True, export_attributes=False)
    print('UPLOAD', label, len(obj.data.polygons), out)
    bpy.data.objects.remove(obj, do_unlink=True)
