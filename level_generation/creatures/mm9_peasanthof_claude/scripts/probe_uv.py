"""Ray-cast from the front at MM9-frame (x, z) points; print the hit face's HeadUV and UVMap (barycentric) and attributes."""
import bpy, bmesh, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; bm = bmesh.new(); bm.from_mesh(ob.data); bm.transform(ob.matrix_world)
bmesh.ops.triangulate(bm, faces=bm.faces[:])
bm.faces.ensure_lookup_table()
bvh = BVHTree.FromBMesh(bm); uvh = bm.loops.layers.uv['HeadUV']; lh = bm.faces.layers.int.get('head')
for q in a[1].split(';'):
    x, z = [float(t) for t in q.split(',')]
    hit = bvh.ray_cast(Vector((x, -0.5, z)), Vector((0, 1, 0)), 2)
    if hit[0] is None: print('UVPROBE miss', x, z); continue
    f = bm.faces[hit[2]]; vs = [l.vert.co for l in f.loops]; uvs = [Vector((l[uvh].uv.x, l[uvh].uv.y, 0)) for l in f.loops]
    uv = barycentric_transform(hit[0], vs[0], vs[1], vs[2], uvs[0], uvs[1], uvs[2])
    print('UVPROBE', x, z, 'hit', [round(c, 4) for c in hit[0]], 'head', f[lh] if lh else None, 'uv', round(uv.x, 4), round(uv.y, 4),
          'px2048', int(uv.x * 2048), int((1 - uv.y) * 2048))
