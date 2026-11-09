from pathlib import Path
import bpy,sys,runpy
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/uv_master.blend'))
(P/'textures').mkdir(exist_ok=True)
sys.argv=['bake_creature_ao.py','--','Wyvern',str(P/'textures/wyvern_ao.png'),'.012','2048']
runpy.run_path(str(P.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
