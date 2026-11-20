import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for name in ['smooth_death','final_cloth','audit_final_fast']:runpy.run_path(str(p/(name+'.py')),run_name='__main__')
