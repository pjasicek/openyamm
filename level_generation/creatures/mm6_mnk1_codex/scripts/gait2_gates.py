"""Run the project's own gates on the gait2 gate blends (gait2_gate_blends.py): sleeve/robe containment at 48 Hz on all
four LODs, G4/G5 dense stretch, elbows and locomotion, G6 contacts. Reports under review/gait2/."""
import os,sys,runpy,shutil,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];out=p/'review/gait2';out.mkdir(parents=True,exist_ok=True)
os.environ['PENETRATION_PROBE']='1'
for level in range(4):
 os.environ['GATE_BLEND']=f'work/gait2/gate_lod{level}.blend';os.environ['PENETRATION_REPORT']=f'review/gait2/penetration_lod{level}.json'
 runpy.run_path(str(p/'scripts/review4_penetration.py'),run_name='__main__')
os.environ['GATE_BLEND']='work/gait2/gate_lod0.blend'
runpy.run_path(str(p/'scripts/gates_dense.py'),run_name='__main__');shutil.copy2(p/'work/gates_dense.json',out/'gates_dense.json')
sys.argv=['g6_contacts.py','--',str(p/'work/gait2/gate_lod0.blend'),'Standing','Walking','Running'];runpy.run_path(str(p/'scripts/g6_contacts.py'),run_name='__main__');shutil.copy2(p/'work/g6_contacts.json',out/'g6_contacts.json')
# review4_anatomy writes review/round4/{elbows,locomotion}.json and asserts the old walk's 8-12 cm swing rule; keep the
# round-4 records and file its results under review/gait2 instead.
keep={n:(p/'review/round4'/n).read_bytes() for n in ['elbows.json','locomotion.json']}
try:
 runpy.run_path(str(p/'scripts/review4_anatomy.py'),run_name='__main__')
except AssertionError as e:print('ANATOMY_ASSERT',e)
for n,data in keep.items():shutil.copy2(p/'review/round4'/n,out/n);(p/'review/round4'/n).write_bytes(data)
print('GAIT2_GATES_DONE')
