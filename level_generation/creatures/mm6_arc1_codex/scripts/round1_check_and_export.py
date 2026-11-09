import runpy,json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
for n in ['round1_gates.py','gate_equipment.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
g6=json.loads((P/'work/g6_contacts.json').read_text());eq=json.loads((P/'work/equipment_gate.json').read_text());errors=[]
for name,row in g6.items():
 if any(v[0]>.2 for v in row.values()):errors.append((name,'body',row))
 if eq[name]['equipment_contact_cm']>.2:errors.append((name,'equipment',eq[name]))
assert not errors,errors
for n in ['export_all.py','uv_gate_run.py','release_gate.py','export_trace_run.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
