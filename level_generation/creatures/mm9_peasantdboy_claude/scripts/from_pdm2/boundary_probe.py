"""Boundary (open) edges of 'Body' inside a box. Args: <blend> <xmin,ymin,zmin,xmax,ymax,zmax>"""
import bpy, bmesh, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
lo = [float(x) for x in argv[1].split(',')][:3]; hi = [float(x) for x in argv[1].split(',')][3:]
bm = bmesh.new(); bm.from_mesh(bpy.data.objects['Body'].data)
n = 0; pts = []
for e in bm.edges:
    if e.is_boundary:
        c = (e.verts[0].co + e.verts[1].co) / 2
        if all(lo[i] <= c[i] <= hi[i] for i in range(3)):
            n += 1; pts.append(tuple(round(x, 3) for x in c))
print('BOUNDARY', n, sorted(pts))
