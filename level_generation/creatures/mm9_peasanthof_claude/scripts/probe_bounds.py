import bpy, sys
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']
zs = [(ob.matrix_world @ v.co).z for v in ob.data.vertices]
print('BOUNDS zmin', round(min(zs), 4), 'zmax', round(max(zs), 4))
