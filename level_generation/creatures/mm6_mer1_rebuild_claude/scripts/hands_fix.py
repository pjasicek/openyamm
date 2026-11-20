"""After graft_hands.py: the old Meshy hand faces left inside the sleeve (part 4, not a new hand face) go; new hand faces get part 4.
Args: <in blend> <out blend>"""
import bpy, bmesh, sys
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me)
pl = bm.faces.layers.int['part']; hl = bm.faces.layers.int['hand']
old = [f for f in bm.faces if f[pl] == 4 and f[hl] != 1]
for f in bm.faces:
    if f[hl] == 1: f[pl] = 4
bmesh.ops.delete(bm, geom=old, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('HANDSFIX removed', len(old), 'tris', len(me.polygons))
