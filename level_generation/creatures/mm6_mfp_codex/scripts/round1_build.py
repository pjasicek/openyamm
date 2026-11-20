import runpy
from pathlib import Path
p=Path(__file__).parent
for name in ['round1_repair','round1_running','round1_motion_finish','round1_anatomical_ik','round1_contacts','round1_export','round1_gate_regions']:runpy.run_path(str(p/(name+'.py')),run_name='__main__')
