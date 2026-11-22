"""Run claude_shared/bake_creature_ao.py on a project blend (the wrapper passes no blend file).
Args: -- <blend> <mesh object> <out png> [reach_m] [size]"""
import bpy, sys, os, runpy
import os as _os; _os.chdir(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))  # project-relative paths
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
for o in [o for o in bpy.data.objects if o.name == 'Wings']:
    o.hide_render = True                                   # translucent cards: no occlusion on the body
sys.argv = [sys.argv[0], '--'] + [a[1], os.path.abspath(a[2])] + a[3:]
runpy.run_path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'claude_shared', 'bake_creature_ao.py'))
print('AOBAKED', a[2])
