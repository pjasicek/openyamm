"""Bake the shared short-range AO; keep its source separate from the runtime specular mask."""
from pathlib import Path
import runpy,sys
import bpy
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/uv_master.blend'))
sys.argv=['bake_creature_ao.py','--','Unicorn',str(P/'textures/unicorn_ao.png'),'.025','2048']
runpy.run_path(str(P.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
