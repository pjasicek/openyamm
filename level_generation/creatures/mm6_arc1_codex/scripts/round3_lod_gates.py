import bpy,runpy,sys,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
for level in [0,1,2,3]:
 shutil.copy2(P/f'work/round2/lod{level}.blend',P/'work/rig_equipped.blend')
 failures=[]
 for name in ['round2_gates.py','round2_contact_gates.py','gate_equipment.py']:
  code=(P/'scripts'/name).read_text().replace('review/round2/','review/round3/')
  try:exec(compile(code,str(P/'scripts'/name),'exec'),{'__file__':str(P/'scripts'/name),'__name__':'__main__'})
  except AssertionError as e:failures.append((name,str(e)))
 eq=json.loads((P/'work/equipment_gate.json').read_text());g4=json.loads((P/'work/g4_equipped.json').read_text());g5=json.loads((P/'work/g5_final.json').read_text());g6=json.loads((P/'work/g6_contacts.json').read_text())
 for clip,row in eq.items():
  if row['equipment_contact_cm']>0 or row['floor_min_cm']<0:failures.append((clip,'equipment',row))
  if any(v[0]>0 for v in g6[clip].values()):failures.append((clip,'G6',g6[clip]))
  if max(v['max_edge_stretch']for v in g5[clip].values())>2.2:failures.append((clip,'G5',g5[clip]))
 if max(v['stretch_p99']for row in g4.values()for v in row.values())>2:failures.append('G4')
 out=P/f'review/round3/lod_gates/lod{level}';out.mkdir(parents=True,exist_ok=True)
 for src in ['work/equipment_gate.json','work/g4_equipped.json','work/g5_final.json','work/g6_contacts.json','review/round3/anatomy_and_feet.json','review/round3/contact_gates.json']:shutil.copy2(P/src,out/Path(src).name)
 (out/'status.json').write_text(json.dumps({'pass':not failures,'failures':failures},indent=2));print('LOD_GATES',level,failures,flush=True)
shutil.copy2(P/'work/round2/lod0.blend',P/'work/rig_equipped.blend')
for name in ['equipment_gate.json','g4_equipped.json','g5_final.json','g6_contacts.json']:shutil.copy2(P/'review/round3/lod_gates/lod0'/name,P/'work'/name)
for name in ['anatomy_and_feet.json','contact_gates.json']:shutil.copy2(P/'review/round3/lod_gates/lod0'/name,P/'review/round3'/name)
