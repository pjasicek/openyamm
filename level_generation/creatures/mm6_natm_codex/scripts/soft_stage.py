import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for name in ['smooth_local','audit_soft_fast','search_lod0_fine']:runpy.run_path(str(p/(name+'.py')),run_name='__main__')
