import bpy,runpy,sys,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
for level in [1,2,3,0]:
 shutil.copy2(P/f'work/round2/lod{level}.blend',P/'work/rig_equipped.blend')
 for name in ['round2_gates.py','round2_contact_gates.py','gate_equipment.py']:
  runpy.run_path(str(P/'scripts'/name),run_name='__main__')
 eq=json.loads((P/'work/equipment_gate.json').read_text());g4=json.loads((P/'work/g4_equipped.json').read_text());g5=json.loads((P/'work/g5_final.json').read_text());g6=json.loads((P/'work/g6_contacts.json').read_text())
 failures=[]
 for clip,row in eq.items():
  if row['equipment_contact_cm']>0 or row['floor_min_cm']<0:failures.append((clip,'equipment',row))
  if any(v[0]>0 for v in g6[clip].values()):failures.append((clip,'G6',g6[clip]))
  if max(v['max_edge_stretch']for v in g5[clip].values())>2.2:failures.append((clip,'G5',g5[clip]))
 if max(v['stretch_p99']for row in g4.values()for v in row.values())>2:failures.append('G4')
 out=P/f'review/round2/lod_gates/lod{level}';out.mkdir(parents=True,exist_ok=True)
 for src in ['work/equipment_gate.json','work/g4_equipped.json','work/g5_final.json','work/g6_contacts.json','review/round2/anatomy_and_feet.json','review/round2/contact_gates.json']:shutil.copy2(P/src,out/Path(src).name)
 (out/'status.json').write_text(json.dumps({'pass':not failures,'failures':failures},indent=2));print('LOD_GATES',level,failures,flush=True);assert not failures,failures
