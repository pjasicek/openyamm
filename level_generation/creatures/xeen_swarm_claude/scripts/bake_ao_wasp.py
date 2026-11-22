"""Rest AO of the single Stinger (work/wasp_uv.blend, reach 2 cm, 2K) -> textures/wasp_ao_2k.png."""
import bpy, os, sys, runpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'wasp_uv.blend'))
sys.argv = ['blender', '--', 'Wasp', os.path.join(HERE, 'textures', 'wasp_ao_2k.png'), '0.02', '2048']
runpy.run_path(os.path.join(os.path.dirname(HERE), 'claude_shared', 'bake_creature_ao.py'), run_name='__main__')
