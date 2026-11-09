import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
acts=['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']
for view in ['front','left','three_quarter']:
 sys.argv=['clip_sheet.py','--',str(P/'work/rig_reduced.blend'),str(P/'review'/('reduced_'+view)),view,'6',*acts]
 runpy.run_path(str(P/'scripts/clip_sheet.py'),run_name='__main__')
sys.argv=['g6_contacts.py','--',str(P/'work/rig_reduced.blend'),*acts]
runpy.run_path(str(P/'scripts/g6_contacts.py'),run_name='__main__')
sys.argv=['g5_hand_stretch.py','--',str(P/'work/rig_reduced.blend'),*acts]
runpy.run_path(str(P/'scripts/g5_hand_stretch.py'),run_name='__main__')
