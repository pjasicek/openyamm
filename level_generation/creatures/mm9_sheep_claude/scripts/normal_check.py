"""Orientation check of 'Body': faces on the top of the back (|x| < 0.1, z above the spine) should face up.
Args: <blend>"""
import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
ob = bpy.data.objects['Body']
me = ob.data
up = dn = 0
for p in me.polygons:
    c = p.center
    if abs(c.x) < 0.1 and c.z > 1.55 and -0.6 < c.y < 1.0:
        if p.normal.z > 0:
            up += 1
        else:
            dn += 1
print('NORMALS back-top faces up', up, 'down', dn)
