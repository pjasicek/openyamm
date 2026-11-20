import bpy, bmesh, sys
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; bm = bmesh.new(); bm.from_mesh(ob.data)
mw = ob.matrix_world
b = [e for e in bm.edges if e.is_boundary and all(abs((mw @ v.co).x) < 0.004 and (mw @ v.co).z > 0.66 and (mw @ v.co).y < 0.0 for v in e.verts)]
print('MIDBOUNDARY', len(b))
sh = [e for e in bm.edges if (not e.smooth) and all(abs((mw @ v.co).x) < 0.004 and (mw @ v.co).z > 0.66 for v in e.verts)]
print('MIDSHARP', len(sh))
fl = sum(1 for f in bm.faces if not f.smooth)
print('FLATFACES', fl, len(bm.faces))
