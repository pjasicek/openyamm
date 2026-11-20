"""All LODs: shared body gates once when exact arrays match; each distinct prop mesh checked independently."""
import bpy,runpy,sys,json,shutil,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
code=(P/'scripts/gate_equipment.py').read_text();equipment_only=code[:code.index('acts=[a.name')]
def mesh_signature():
 b=bpy.data.objects['Body'];return (np.array([v.co[:]for v in b.data.vertices]),[tuple(f.vertices)for f in b.data.polygons],[[tuple((g.group,g.weight))for g in v.groups]for v in b.data.vertices])
reference=None
for level in range(4):
 shutil.copy2(P/f'work/round2/lod{level}.blend',P/'work/rig_equipped.blend');bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));sig=mesh_signature()
 if level==0:
  reference=sig
  for name in ['round2_gates.py','round2_contact_gates.py','gate_equipment.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
 else:
  assert np.array_equal(sig[0],reference[0])and sig[1:]==reference[1:],'Bodies differ; run full body gates'
  runpy.run_path(str(P/'scripts/round2_contact_gates.py'),run_name='__main__')
  exec(compile(equipment_only,str(P/'scripts/gate_equipment.py'),'exec'),{'__file__':str(P/'scripts/gate_equipment.py'),'__name__':'__main__'})
 eq=json.loads((P/'work/equipment_gate.json').read_text());g4=json.loads((P/'work/g4_equipped.json').read_text());g5=json.loads((P/'work/g5_final.json').read_text());g6=json.loads((P/'work/g6_contacts.json').read_text());fail=[]
 for clip,row in eq.items():
  if row['equipment_contact_cm']>.2 or row['floor_min_cm']<-.001:fail.append((clip,'equipment',row))
  if any(v[0]>.2 for v in g6[clip].values()):fail.append((clip,'G6',g6[clip]))
  if max(v['max_edge_stretch']for v in g5[clip].values())>2.2:fail.append((clip,'G5',g5[clip]))
 if max(v['stretch_p99']for row in g4.values()for v in row.values())>2:fail.append('G4')
 out=P/f'review/round2/lod_gates/lod{level}';out.mkdir(parents=True,exist_ok=True)
 for src in ['work/equipment_gate.json','work/g4_equipped.json','work/g5_final.json','work/g6_contacts.json','review/round2/anatomy_and_feet.json','review/round2/contact_gates.json']:shutil.copy2(P/src,out/Path(src).name)
 (out/'status.json').write_text(json.dumps({'pass':not fail,'failures':fail,'body_gate_reuse':'Exact vertices, topology and skin weights identical to LOD0'if level else None,'prop_gates':'independent every clip'},indent=2));print('SELECTED_LOD_GATES',level,fail,flush=True);assert not fail,fail
shutil.copy2(P/'work/round2/lod0.blend',P/'work/rig_equipped.blend')
for name in ['equipment_gate.json','g4_equipped.json','g5_final.json','g6_contacts.json']:shutil.copy2(P/'review/round2/lod_gates/lod0'/name,P/'work'/name)
for name in ['anatomy_and_feet.json','contact_gates.json']:shutil.copy2(P/'review/round2/lod_gates/lod0'/name,P/'review/round2'/name)
