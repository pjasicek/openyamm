"""Bake the rest-pose AO (claude_shared/bake_creature_ao.py, reach 4 cm, 2K) of work/rig_uv.blend into
textures/guard_ao_2k.png. The blend is not saved."""
import bpy, os, sys, runpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_uv.blend'))
rig = bpy.data.objects['Guard_Rig']
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
sys.argv = ['blender', '--', 'Guard', os.path.join(HERE, 'textures', 'guard_ao_2k.png'), '0.04', '2048']
runpy.run_path(os.path.join(os.path.dirname(HERE), 'claude_shared', 'bake_creature_ao.py'), run_name='__main__')
print('AO baked')
