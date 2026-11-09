"""Rename / copy actions. Args: -- <in> <out> old:new [...] (new = '-' deletes)"""
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
for it in a[2:]:
    o, n = it.split(':')
    if n == '-': bpy.data.actions.remove(bpy.data.actions[o]); continue
    if n in bpy.data.actions: bpy.data.actions.remove(bpy.data.actions[n])
    bpy.data.actions[o].name = n
    print('RENAMED', o, n)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a[1]))
