import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for file in ('motion_reduced.blend','master_uv.blend'):
 path=str(P/'work'/file);sys.argv=['clean_reduced.py','--',path,path];runpy.run_path(str(P/'scripts/clean_reduced.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/apply_textures.py'),run_name='__main__')
