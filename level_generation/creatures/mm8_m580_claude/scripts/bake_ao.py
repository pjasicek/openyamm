from pathlib import Path
import bpy,sys,runpy
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv.blend'))
(P/'textures').mkdir(exist_ok=True)
sys.argv=['bake_creature_ao.py','--','Turtle',str(P/'textures/m580_ao.png'),'.04','1024']
runpy.run_path(str(P.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
