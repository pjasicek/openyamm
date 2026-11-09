from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parents[1]
for n in ['clean_props','finish_master','equipment_checks']:
 s=P/'scripts'/(n+'.py');sys.argv=[str(s)];runpy.run_path(str(s),run_name='__main__')
