import os,sys,runpy,json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for level in range(4):
 os.environ['GATE_BLEND']=f'work/final_lod{level}.blend';os.environ['PHYSICAL_REPORT']=f'review/final/lod{level}_physical.json';runpy.run_path(str(p/'scripts/physical_gates.py'),run_name='__main__')
os.environ['G6_REPORT']='review/final/lod3_contacts.json';sys.argv=['g6','--',str(p/'work/final_lod3.blend'),'Standing','Fidget','Walking','Running','Attack','Cast','Hit','Death','Dead'];runpy.run_path(str(p/'scripts/g6_contacts.py'),run_name='__main__')
for level in range(4):
 for v in json.loads((p/f'review/final/lod{level}_dense.json').read_text()).values():assert all(v[k] for k in ['G4_pass','G5_pass','elbow_pass','roll_pass'])
 assert all(v['pass'] for v in json.loads((p/f'review/final/lod{level}_cloth.json').read_text())['clips'].values())
 assert all(v[0]<=.2 for role in json.loads((p/f'review/final/lod{level}_contacts.json').read_text()).values() for v in role.values())
print('FINAL_ALL_LOD_GATES_PASS',flush=True)
runpy.run_path(str(p/'scripts/export_trace_final.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/final_visual_metrics.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/render_final.py'),run_name='__main__')
