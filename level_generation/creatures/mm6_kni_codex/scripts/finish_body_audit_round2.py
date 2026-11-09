import bpy,sys,runpy,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round2';R=P/'review/round2';roles=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
for tag in ['baseline_l1','selected_l0','selected_l1','selected_l2','selected_l3']:
 src=W/(f'audit_{tag}.blend' if tag.startswith('baseline') else f'selected_body_l{tag[-1]}.blend')
 sys.argv=['g6_cloth_round2.py','--',str(src),*roles];runpy.run_path(str(P/'scripts/g6_cloth_round2.py'),run_name='__main__');shutil.copyfile(P/'work/g6_fauld.json',R/f'g6_cloth_{tag}.json')
runpy.run_path(str(P/'scripts/anatomy_round2.py'),run_name='__main__')
