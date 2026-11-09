"""Rest-pose AO of the robot (claude_shared/bake_creature_ao.py on work/uv_master.blend) -> textures/robot_ao.png."""
import bpy, os, sys, runpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work/uv_master.blend'))
os.makedirs(os.path.join(HERE, 'textures'), exist_ok=True)
sys.argv = ['x', '--', 'Robot', os.path.join(HERE, 'textures/robot_ao.png'), '0.03', '2048']
runpy.run_path(os.path.join(os.path.dirname(HERE), 'claude_shared/bake_creature_ao.py'))
