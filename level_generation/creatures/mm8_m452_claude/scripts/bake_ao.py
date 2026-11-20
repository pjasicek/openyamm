import bpy,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv.blend'))
sys.argv=[__file__,'--','Rat',str(P/'textures/rat_ao.png'),'.03','2048']
runpy.run_path(str(P.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
