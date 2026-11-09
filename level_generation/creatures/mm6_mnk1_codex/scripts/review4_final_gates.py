import os,runpy,shutil
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for script in ['check_master.py','review4_anatomy.py','review1_occlusion.py','review4_cloth_metrics.py','final_checks.py']:
 os.environ['GATE_BLEND']='export/mm6_mnk1.blend'
 runpy.run_path(str(p/'scripts'/script),run_name='__main__')
for level in range(4):
 os.environ['GATE_BLEND']='export/mm6_mnk1.blend' if level==0 else f'work/review4_lod{level}.blend'
 os.environ['PENETRATION_REPORT']=f'review/round4/penetration_lod{level}.json'
 runpy.run_path(str(p/'scripts/review4_penetration.py'),run_name='__main__')
for name in ['gates_dense.json','g6_contacts.json','review1_occlusion.json']:
 shutil.copy2(p/'work'/name,p/'review/round4'/name)
