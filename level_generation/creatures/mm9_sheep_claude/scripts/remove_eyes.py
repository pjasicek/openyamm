"""Delete the eyeball spheres (piece 1): Meshy painted the eye, with lids, further forward on the head surface than its
own lumpy eye piece, so a separate ball near the ear only doubles it. UVs of everything else stay (the retexture
stays valid). Args: <in blend> <out blend>"""
import bpy, bmesh, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
o = bpy.data.objects['Body']; me = o.data
bm = bmesh.new(); bm.from_mesh(me)
pl = bm.verts.layers.int.get('piece')
vs = [v for v in bm.verts if v[pl] == 1]
bmesh.ops.delete(bm, geom=vs, context='VERTS')
bm.to_mesh(me); bm.free()
print('EYES_REMOVED', len(vs), 'tris', len(me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=argv[1])
