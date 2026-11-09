import os,sys,runpy,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];(p/'review/final').mkdir(exist_ok=True)
for level in range(4):
 os.environ['GATE_BLEND']=f'work/final_lod{level}.blend';os.environ['GATE_REPORT']=f'review/final/lod{level}_dense.json';os.environ['CLOTH_REPORT']=f'review/final/lod{level}_cloth.json';os.environ['G6_REPORT']=f'review/final/lod{level}_contacts.json';os.environ['PHYSICAL_REPORT']=f'review/final/lod{level}_physical.json'
 for script in ['dense_gates.py','cloth_surface_gate.py','physical_gates.py']:
  runpy.run_path(str(p/'scripts'/script),run_name='__main__')
 sys.argv=['g6','--',str(p/os.environ['GATE_BLEND']),'Standing','Fidget','Walking','Running','Attack','Cast','Hit','Death','Dead'];runpy.run_path(str(p/'scripts/g6_contacts.py'),run_name='__main__')
 dense=json.loads((p/os.environ['GATE_REPORT']).read_text());cloth=json.loads((p/os.environ['CLOTH_REPORT']).read_text())['clips'];contacts=json.loads((p/os.environ['G6_REPORT']).read_text())
 assert len(dense)==len(cloth)==len(contacts)==9
 assert all(len(parts)==5 for parts in contacts.values())
 assert all(all(v[k] for k in ['G4_pass','G5_pass','elbow_pass','roll_pass']) for v in dense.values())
 assert all(v['pass'] for v in cloth.values())
 assert all(hit[0]<=.2 for vals in contacts.values() for hit in vals.values())
print('FINAL_ALL_LOD_GATES_PASS',flush=True)
