"""Bake the rest-pose AO (claude_shared/bake_creature_ao.py, reach 4 cm, 2K) of work/anim_v1.blend into
textures/hcr_ao_2k.png. The blend is not saved."""
import bpy, os, sys, runpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
sys.argv = ['blender', '--', 'Crawler', os.path.join(HERE, 'textures', 'hcr_ao_2k.png'), '0.04', '2048']
runpy.run_path(os.path.join(os.path.dirname(HERE), 'claude_shared', 'bake_creature_ao.py'), run_name='__main__')
print('AO baked')
