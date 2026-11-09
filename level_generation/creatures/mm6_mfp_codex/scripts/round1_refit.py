import shutil,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for n in range(4):shutil.copy2(p/f'work/round1/pre_ik_lod{n}.blend',p/f'work/round1/lod{n}.blend')
for n in ['round1_anatomical_ik','round1_contacts','round1_export','round1_gate_regions']:runpy.run_path(str(p/'scripts'/(n+'.py')),run_name='__main__')
