import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for name in ['final_gait','running_cloth','far_inflate','audit_final_lod0']:runpy.run_path(str(p/(name+'.py')),run_name='__main__')
