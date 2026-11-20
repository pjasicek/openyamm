import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
for s in ['finish_clips.py','gate_reduce.py','gates_upload_run.py']:
 runpy.run_path(str(P/'scripts'/s),run_name='__main__')
sys.argv=['g6_contacts.py','--',str(P/'work/rig_reduced.blend'),'Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']
runpy.run_path(str(P/'scripts/g6_contacts.py'),run_name='__main__')

runpy.run_path(str(P/'scripts/remove_neck_ring.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/texture_prepare.py'),run_name='__main__')
