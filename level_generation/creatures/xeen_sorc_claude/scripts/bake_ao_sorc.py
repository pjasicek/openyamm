"""Rest AO of the sorceress on the locked shared layout (work/uv_v1.blend, reach 3 cm, 2048 over the whole upload square:
each set's lower-half quadrant is 1024, the size of its ORM and colour) -> textures/sorc_ao_2k.png."""
import bpy, os, sys, runpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'uv_v1.blend'))
sys.argv = ['blender', '--', 'Body', os.path.join(HERE, 'textures', 'sorc_ao_2k.png'), '0.03', '2048']
runpy.run_path(os.path.join(os.path.dirname(HERE), 'claude_shared', 'bake_creature_ao.py'), run_name='__main__')
