"""Rest AO of the Doom Bug (work/bug_rig.blend, reach 2 cm, 2K) -> textures/bug_ao_2k.png."""
import bpy, os, sys, runpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'bug_rig.blend'))
sys.argv = ['blender', '--', 'Bug', os.path.join(HERE, 'textures', 'bug_ao_2k.png'), '0.04', '2048']
runpy.run_path(os.path.join(os.path.dirname(HERE), 'claude_shared', 'bake_creature_ao.py'), run_name='__main__')
