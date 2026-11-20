from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parents[1]
for n in ['final_equipment_motion','measure_runtime','export_runtime']:
 s=P/'scripts'/(n+'.py');sys.argv=[str(s)];runpy.run_path(str(s),run_name='__main__')
s=P/'scripts/equipment_checks.py';sys.argv=[str(s),'--','Walking'];runpy.run_path(str(s),run_name='__main__')
