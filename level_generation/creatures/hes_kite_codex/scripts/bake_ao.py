import bpy,sys,os,runpy,traceback
from pathlib import Path
p=Path(__file__).resolve().parents[1]
try:
 bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v3.blend'))
 (p/'textures').mkdir(exist_ok=True)
 sys.argv=['bake_creature_ao.py','--','Ashkite',str(p/'textures/ashkite_ao_1k.png'),'.06','1024']
 runpy.run_path(str(p.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
except BaseException:traceback.print_exc();sys.stderr.flush();os._exit(1)
sys.stdout.flush();os._exit(0)
