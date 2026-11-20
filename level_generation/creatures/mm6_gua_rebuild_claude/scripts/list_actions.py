import bpy, sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
print('ACTIONS', [(a.name, tuple(int(x) for x in a.frame_range)) for a in bpy.data.actions])
