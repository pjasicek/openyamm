import bpy,sys,json,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));clips=['Standing','Fidget','Walking','Running','Attack','Cast','Hit','Death','Dead']
for level in range(4):
 path=P/'work/export_reimport.blend'if level==0 else P/f'work/rebake/runtime_lod{level}.blend'
 sys.argv=['head','--',str(path),*clips];runpy.run_path(str(P/'scripts/g6_head_clearance.py'),run_name='__main__');text=(P/'review/head_clearance.json').read_text();report=json.loads(text)
 if level==0:near=text
 else:
  (P/f'review/rebake/runtime_lod{level}_head_clearance.json').write_text(text);file=P/f'review/rebake/runtime_lod{level}_gates.json';g=json.loads(file.read_text());g['head_contact_m']=max(v['depth_m']for v in report.values());g['passed']=g['arm_p99']<=2 and g['hand_max']<=4.5 and g['body_contact_m']<=.002 and g['head_contact_m']<=.01 and g['equipment_contact_m']<=.002 and g['motion']['passed'];file.write_text(json.dumps(g,indent=2));assert g['passed'],level
(P/'review/head_clearance.json').write_text(near)
runpy.run_path(str(P/'scripts/runtime_lod_gates.py'),run_name='__main__',init_globals={'LOD_LEVELS':[3]})
