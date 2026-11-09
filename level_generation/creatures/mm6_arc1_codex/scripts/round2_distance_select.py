import bpy,json,sys,numpy as np,runpy,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));from round2_reduce import reset
D=P/'review/round2/reduction';W=P/'work/round2';S=json.loads((D/'distance_selected.json').read_text())
for row in json.loads((D/'distance_contact_fit.json').read_text()):S['body'][str(row['lod'])]=row
arrow=json.loads((W/'arrow_far_source.json').read_text())
for level in [2,3]:
 ob,rig=reset('arrow');vertices=arrow['vertices'];faces=arrow['faces'];uv=arrow['uv']
 if level==3:
  vertices=np.array(vertices);areas=[np.linalg.norm(np.cross(vertices[f[1]]-vertices[f[0]],vertices[f[2]]-vertices[f[0]]))for f in faces];faces=[f for i,f in enumerate(faces)if i!=int(np.argmin(areas))]
 me=bpy.data.meshes.new('Arrow distance');me.from_pydata(vertices,[],faces);me.update();ob.data=me;layer=me.uv_layers.new(name='UVMap')
 for f in me.polygons:
  for li in f.loop_indices:layer.data[li].uv=uv[me.loops[li].vertex_index]
 for name in ['bow_part','material_class']:me.attributes.new(name,'INT','FACE').data.foreach_set('value',[3 if name=='bow_part'else 9]*len(faces))
 (ob.vertex_groups.get('Arrow') or ob.vertex_groups.new(name='Arrow')).add(list(range(len(vertices))),1,'REPLACE');path=W/f'arrow_l{level}_capped.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));S['arrow'][str(level)]={'part':'arrow','lod':level,'triangles':len(faces),'blend':str(path.relative_to(P)),'strategy':'installed five-triangle distance topology; least-area triangle removed at LOD3'}
(D/'selected.json').write_text(json.dumps(S,indent=2));runpy.run_path(str(P/'scripts/round2_assemble.py'),run_name='__main__')
for level in [1,2,3]:
 shutil.copy2(W/f'lod{level}.blend',P/'work/rig_equipped.blend');errors=[]
 for name in ['round2_gates.py','round2_contact_gates.py','gate_equipment.py']:
  try:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
  except Exception as e:errors.append([name,type(e).__name__,str(e)]);print('DISTANCE_GATE_ERROR',level,errors[-1],flush=True)
 out=D/f'distance_gates/lod{level}';out.mkdir(parents=True,exist_ok=True)
 for src in ['work/equipment_gate.json','work/g4_equipped.json','work/g5_final.json','work/g6_contacts.json','review/round2/anatomy_and_feet.json','review/round2/contact_gates.json']:shutil.copy2(P/src,out/Path(src).name)
 (out/'execution.json').write_text(json.dumps({'errors':errors},indent=2));print('DISTANCE_GATES_DONE',level,errors,flush=True)
shutil.copy2(W/'lod0.blend',P/'work/rig_equipped.blend')
for name in ['equipment_gate.json','g4_equipped.json','g5_final.json','g6_contacts.json']:shutil.copy2(P/'review/round2/lod_gates/lod0'/name,P/'work'/name)
for name in ['anatomy_and_feet.json','contact_gates.json']:shutil.copy2(P/'review/round2/lod_gates/lod0'/name,P/'review/round2'/name)
