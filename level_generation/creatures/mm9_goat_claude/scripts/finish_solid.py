"""Second half of the body clean (after solid_grid.py): the solid's blocky boundary (OBJ) is voxel-remeshed (one
closed surface, no inner layer, no bubbles), smoothed, and shrunk back onto the Meshy skin (nearest surface point of
the main component, undoing the one-voxel wall dilation); the Meshy pieces (eyes, teats, tail tassel, beard) are
added back as returned. Output: a GLB like clean_meshy.py's (Body = skin + pieces).
Args: <solid obj> <meshy glb> <out glb> <voxel> [smooth iterations] [shrink 0|1]"""
import bpy, bmesh, sys
argv = sys.argv[sys.argv.index('--') + 1:]
OBJ, MESHY, OUT, VOX = argv[0], argv[1], argv[2], float(argv[3])
ITER = int(argv[4]) if len(argv) > 4 else 8
SHRINK = argv[5] != '0' if len(argv) > 5 else True
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=OBJ)
solid = next(o for o in bpy.data.objects if o.type == 'MESH')
solid.name = 'Body'
bpy.ops.import_scene.gltf(filepath=MESHY)
raw = next(o for o in bpy.data.objects if o.type == 'MESH' and o != solid)
bm = bmesh.new(); bm.from_mesh(raw.data); bm.transform(raw.matrix_world)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.verts.ensure_lookup_table()
seen, comps = set(), []
for v in bm.verts:
    if v.index in seen:
        continue
    c, st = [], [v]; seen.add(v.index)
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); st.append(y)
    comps.append(c)
comps.sort(key=len, reverse=True)
main = set(comps[0])


def make(name, keep):
    b2 = bm.copy(); b2.verts.ensure_lookup_table()
    bmesh.ops.delete(b2, geom=[v for v in b2.verts if (v.index in main) != keep], context='VERTS')
    me = bpy.data.meshes.new(name); b2.to_mesh(me)
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob


skin = make('Skin', True)
pieces = make('Pieces', False)
for o in list(bpy.data.objects):
    if o not in (solid, skin, pieces):
        bpy.data.objects.remove(o)
bpy.context.view_layer.objects.active = solid
for o in bpy.data.objects:
    o.select_set(o == solid)
solid.data.remesh_voxel_size = VOX
solid.data.remesh_voxel_adaptivity = 0.0
bpy.ops.object.voxel_remesh()
n_vox = len(solid.data.polygons)
sm = solid.modifiers.new('smooth', 'SMOOTH'); sm.factor = 0.5; sm.iterations = ITER
bpy.ops.object.modifier_apply(modifier='smooth')
if SHRINK:
    sw = solid.modifiers.new('sw', 'SHRINKWRAP'); sw.target = skin; sw.wrap_method = 'NEAREST_SURFACEPOINT'
    bpy.ops.object.modifier_apply(modifier='sw')
    sm = solid.modifiers.new('relax', 'SMOOTH'); sm.factor = 0.3; sm.iterations = 2
    bpy.ops.object.modifier_apply(modifier='relax')
bmc = bmesh.new(); bmc.from_mesh(solid.data)
info = {'voxel_faces': n_vox, 'boundary': sum(1 for e in bmc.edges if e.is_boundary),
        'nonmanifold': sum(1 for e in bmc.edges if not e.is_manifold), 'pieces': len(comps) - 1}
bmc.free()
bpy.data.objects.remove(skin)
for p in solid.data.polygons:
    p.use_smooth = True
for o in bpy.data.objects:
    o.select_set(True)
bpy.context.view_layer.objects.active = solid
bpy.ops.object.join()
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_yup=True, export_materials='NONE')
print('SOLID', info)
