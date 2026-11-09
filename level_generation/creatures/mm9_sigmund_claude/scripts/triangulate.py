"""Triangulate the non-triangle faces of 'Body' (cuff_trim.py's bisect leaves n-gons; uv_atlas.py needs triangles).
Face attributes, UVs and weights carry over. Args: <in blend> <out blend>"""
import bpy, bmesh, sys
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me)
ng = [f for f in bm.faces if len(f.verts) > 3]
bmesh.ops.triangulate(bm, faces=ng, quad_method='BEAUTY', ngon_method='BEAUTY')
bm.to_mesh(me); bm.free(); me.update()
print('TRI', len(ng), 'faces triangulated; tris', len(me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
