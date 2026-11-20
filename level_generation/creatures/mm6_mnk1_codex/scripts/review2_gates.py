import runpy,os
from pathlib import Path
p=Path(__file__).resolve().parents[1]
os.environ['GATE_BLEND']=str(p/'export/mm6_mnk1.blend')
for name in ['check_master.py','review1_occlusion.py','review2_cloth_metrics.py','build_lods.py']:runpy.run_path(str(p/'scripts'/name),run_name='__main__')
