import bpy, sys, json, bmesh
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
out = {}
for o in bpy.context.scene.objects:
    if o.type == 'MESH' and o.name.startswith('d_wing'):
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
        vs = []
        for v in bm.verts:
            dv = o.data.vertices[v.index] if v.index < len(o.data.vertices) else None
            vs.append([round(x, 4) for x in (o.matrix_world @ v.co)])
        faces = [[v.index for v in f.verts] for f in bm.faces]
        uvl = bm.loops.layers.uv.active
        uvs = {}
        for f in bm.faces:
            for l in f.loops:
                uvs[l.vert.index] = [round(l[uvl].uv.x, 4), round(l[uvl].uv.y, 4)]
        out[o.name] = {'verts': vs, 'faces': faces, 'uv': uvs}
print('WINGS ' + json.dumps(out))
