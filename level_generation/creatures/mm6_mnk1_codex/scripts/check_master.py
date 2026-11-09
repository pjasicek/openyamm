import os,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];os.environ['GATE_BLEND']='export/mm6_mnk1.blend'
runpy.run_path(str(p/'scripts/gates_dense.py'),run_name='__main__')
sys.argv=['g6_contacts.py','--',str(p/'export/mm6_mnk1.blend'),'Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']
runpy.run_path(str(p/'scripts/g6_contacts.py'),run_name='__main__')

import json
dense=json.loads((p/"work/gates_dense.json").read_text());contact=json.loads((p/"work/g6_contacts.json").read_text())
assert len(dense)==9 and all(v["G4_pass"] and v["G5_pass"] for v in dense.values()),dense
assert all(v[0]<=.2 for c in contact.values() for v in c.values()),contact
