import bpy,runpy,sys,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
for level in [3]:
 shutil.copy2(P/f'work/round2/lod{level}.blend',P/'work/rig_equipped.blend');errors=[]
 for name in ['round2_gates.py','round2_contact_gates.py','gate_equipment.py']:
  try:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
  except Exception as e:errors.append([name,type(e).__name__,str(e)]);print('DISTANCE_GATE_ERROR',level,errors[-1],flush=True)
 eq=json.loads((P/'work/equipment_gate.json').read_text());g4=json.loads((P/'work/g4_equipped.json').read_text());g5=json.loads((P/'work/g5_final.json').read_text());g6=json.loads((P/'work/g6_contacts.json').read_text())
 for clip,row in eq.items():
  if row['equipment_contact_cm']>0 or row['floor_min_cm']<0:errors.append([clip,'equipment/floor',row])
  if any(v[0]>0 for v in g6[clip].values()):errors.append([clip,'G6',g6[clip]])
  if max(v['max_edge_stretch']for v in g5[clip].values())>2.2:errors.append([clip,'G5'])
 if max(v['stretch_p99']for row in g4.values()for v in row.values())>2:errors.append(['G4'])
 out=P/f'review/round2/lod_gates/lod{level}'
 for src in ['work/equipment_gate.json','work/g4_equipped.json','work/g5_final.json','work/g6_contacts.json','review/round2/anatomy_and_feet.json','review/round2/contact_gates.json']:shutil.copy2(P/src,out/Path(src).name)
 (out/'status.json').write_text(json.dumps({'pass':not errors,'failures':errors,'revision':'strict descending installed-count caps; physical surface fitting'},indent=2));print('FINAL_DISTANCE_GATES',level,errors,flush=True)
shutil.copy2(P/'work/round2/lod0.blend',P/'work/rig_equipped.blend')
for name in ['equipment_gate.json','g4_equipped.json','g5_final.json','g6_contacts.json']:shutil.copy2(P/'review/round2/lod_gates/lod0'/name,P/'work'/name)
for name in ['anatomy_and_feet.json','contact_gates.json']:shutil.copy2(P/'review/round2/lod_gates/lod0'/name,P/'review/round2'/name)
runpy.run_path(str(P/'scripts/round2_assembled_metrics.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round2_head_probe.py'),run_name='__main__')

runpy.run_path(str(P/'scripts/round2_distance_export.py'),run_name='__main__')
