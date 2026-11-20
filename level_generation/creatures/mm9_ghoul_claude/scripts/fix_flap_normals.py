"""UV blend: every flap face outward (recalc on an open sheet picks either side), then the uploads again; UVs untouched. Args: <blend in/out> <body upload> <head upload>"""
import bpy, bmesh, sys
import numpy as np
BL, UP_B, UP_H = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=BL)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
bm = bmesh.new(); bm.from_mesh(me); lay = bm.verts.layers.int['part']
fl = [f for f in bm.faces if all(v[lay] == 6 for v in f.verts) and f.normal.y > 0] + [f for f in bm.faces if all(v[lay] == 7 for v in f.verts) and f.normal.y < 0]
print('FLIP', len(fl))
bmesh.ops.reverse_faces(bm, faces=fl)
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=BL)
nf = len(me.polygons); nv = len(me.vertices)
pa = np.zeros(nv, np.int32); me.attributes['part'].data.foreach_get('value', pa)
fv = np.array([p.vertices[:] for p in me.polygons])
is_head = (pa[fv] >= 10).all(1)
head_f = np.where(is_head)[0]


def upload(path, faces, uvname):
    dup = body.copy(); dup.data = me.copy(); dup.modifiers.clear(); dup.parent = None; dup.matrix_world = body.matrix_world
    bpy.context.scene.collection.objects.link(dup); dm = dup.data
    for g in list(dup.vertex_groups): dup.vertex_groups.remove(g)
    if uvname == 'HeadUV':
        dm.uv_layers.active = dm.uv_layers['UVMap']
        for i in range(len(dm.loops)): dm.uv_layers['UVMap'].data[i].uv = dm.uv_layers['HeadUV'].data[i].uv
    dm.uv_layers.remove(dm.uv_layers['HeadUV'])
    for a in [a.name for a in dm.attributes if a.name in ('part', 'head')]:
        dm.attributes.remove(dm.attributes[a])
    bm = bmesh.new(); bm.from_mesh(dm); bm.faces.ensure_lookup_table()
    keep = set(faces.tolist())
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(dm); bm.free(); dm.update()
    mat = bpy.data.materials.new('m'); dm.materials.clear(); dm.materials.append(mat)
    for o in bpy.data.objects: o.select_set(o is dup)
    bpy.context.view_layer.objects.active = dup
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_animations=False, export_skins=False, export_yup=True, export_attributes=False, export_materials='EXPORT')
    bpy.data.objects.remove(dup)


upload(UP_B, np.arange(nf), 'UVMap')
upload(UP_H, head_f, 'HeadUV')
print('UPLOADS')
