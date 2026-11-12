"""Open the UV blend and run claude_shared/bake_creature_ao.py on 'Body' (rest pose). Args: <blend> <out png> [reach] [size]"""
import bpy, sys, os, runpy
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
sys.argv = [sys.argv[0], '--', 'Body', a[1]] + a[2:]
runpy.run_path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'claude_shared', 'bake_creature_ao.py'))
