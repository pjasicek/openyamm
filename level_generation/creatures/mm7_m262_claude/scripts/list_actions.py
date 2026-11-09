"""List the actions of the opened blend (name, frame range, fake user). Args: -- <blend>"""
import sys, os
import bpy as _b
_b.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index("--") + 1]))
import bpy
for a in bpy.data.actions:
    print('ACT', a.name, tuple(a.frame_range), a.use_fake_user, len(a.fcurves) if hasattr(a,'fcurves') else '')
