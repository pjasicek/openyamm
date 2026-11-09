import bpy, sys, json
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
r = bpy.data.objects['MM9_Rig']
json.dump({b.name: list(r.matrix_world @ b.head_local) for b in r.data.bones}, open(a[1], 'w'))
