"""Triangulate every non-triangle face of 'Body' (the neck bisect and the hole fills leave quads/ngons; uv_atlas.py needs
triangles). Face attributes, UVs and weights carry. Args: <in blend> <out blend>"""
import bpy, bmesh, sys
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me)
nf = [f for f in bm.faces if len(f.verts) > 3]
bmesh.ops.triangulate(bm, faces=nf, quad_method='BEAUTY', ngon_method='BEAUTY')
bm.to_mesh(me); me.update()
print('TRIANGULATED', len(nf), 'tris', len(me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
