"""Run claude_shared/bake_creature_ao.py on the body (UVMap) of work/rig_v1t.blend. Args: -- <out.png> <reach> <size>"""
import sys, os, runpy, bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
out, reach, size = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=C.path('work/rig_v1t.blend'))
me = bpy.data.objects[C.MESH].data
me.uv_layers.active = me.uv_layers['UVMap']
for l in me.uv_layers:
    l.active_render = l.name == 'UVMap'
sys.argv = ['x', '--', C.MESH, C.path(out), reach, size]
runpy.run_path(os.path.join(os.path.dirname(C.HERE), 'claude_shared', 'bake_creature_ao.py'))
