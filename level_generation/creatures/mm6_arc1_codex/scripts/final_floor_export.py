import runpy,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.dont_write_bytecode=True
runpy.run_path(str(P/'scripts/final_floor.py'),run_name='__main__')
sys.argv=['transfer_uv.py','--','work/rig_equipped.blend','meshy/body_retexture_v1','work/rig_textured.blend'];runpy.run_path(str(P/'scripts/transfer_uv.py'),run_name='__main__')
for n in ['export_runtime.py','build_lods.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
