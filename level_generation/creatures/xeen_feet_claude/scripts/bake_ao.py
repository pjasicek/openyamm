"""Rest AO of the single foot (work/foot_v2.blend, reach 2 cm, 2K) -> textures/feet_ao_2k.png."""
import bpy, os, sys, runpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'foot_v2.blend'))
sys.argv = ['blender', '--', 'Foot', os.path.join(HERE, 'textures', 'feet_ao_2k.png'), '0.02', '2048']
runpy.run_path(os.path.join(os.path.dirname(HERE), 'claude_shared', 'bake_creature_ao.py'), run_name='__main__')
