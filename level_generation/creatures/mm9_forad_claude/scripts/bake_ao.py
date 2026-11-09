"""Project-local entry for ../claude_shared/bake_creature_ao.py: args <blend> <mesh> <out.png> [reach] [size]."""
import bpy, sys, os, runpy
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
sys.argv = ['blender', '--'] + argv[1:]
runpy.run_path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                            'claude_shared', 'bake_creature_ao.py'), run_name='__main__')
