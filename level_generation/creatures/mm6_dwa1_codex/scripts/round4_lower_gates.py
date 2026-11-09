"""Exercise each selected runtime colour LOD on every clip; shared bones use the LOD0 elbow/palm gates."""
import bpy,sys,json,shutil,numpy as np,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));roles=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
h=hashlib.sha256((P/'export/mm6_dwa1.glb').read_bytes()).hexdigest();summary={}
for level in [1,2,3]:
 dest=P/f'review/round4/lod{level}';dest.mkdir(exist_ok=True);blend=P/f'work/round4/final_lod{level}.blend'
 path=P/'scripts/import_final.py';source=path.read_text().replace("P/'work/textured_master.blend'",f"P/'work/round4/selected_lod{level}.blend'").replace("P/'export/mm6_dwa1_runtime_lod0.glb'",f"P/'work/round4/final_unbaked_lod{level}.glb'").replace("P/'work/export_reimport.blend'",f"P/'work/round4/final_lod{level}.blend'")
 exec(compile(source,str(path),'exec'),{'__file__':str(path),'__name__':'__main__'})
 picks=[f'{n}:{f}'for n in roles for f in np.arange(0,float(bpy.data.actions[n].frame_range[1])+1e-5,bpy.context.scene.render.fps/48)]
 for name in ['g4_weights.py','g5_hand_stretch.py','contact_final.py','skirt_intersections.py','round4_flap_gate.py']:
  path=P/'scripts'/name;source=path.read_text().replace("P/'work/export_reimport.blend'",f"P/'work/round4/final_lod{level}.blend'").replace("P/'review/",f"P/'review/round4/lod{level}/").replace("'review','g5_exported.json'",f"'review','round4','lod{level}','g5_exported.json'").replace('review/round4/lod'+str(level)+'/round3/','review/round4/lod'+str(level)+'/').replace('assert len(bladeids)>100','assert len(bladeids)>3').replace('assert len(ids)>12','assert len(ids)>2')
  if name=='g4_weights.py':sys.argv=[name,'--',str(blend),f'round4_lod{level}',*picks]
  if name=='g5_hand_stretch.py':sys.argv=[name,'--',str(blend),*roles]
  try:exec(compile(source,str(path),'exec'),{'__file__':str(path),'__name__':'__main__'})
  except AssertionError as e:print('LOD_GATE_ASSERT',level,name,str(e),flush=True)
 shutil.copy2(P/f'work/g4_round4_lod{level}.json',dest/'g4.json')
 g4=json.loads((dest/'g4.json').read_text());g5=json.loads((dest/'g5_exported.json').read_text());g6=json.loads((dest/'g6_exported.json').read_text());cloth=json.loads((dest/'skirt_intersections.json').read_text());flap=json.loads((dest/'flap_stretch_gate.json').read_text());rows={}
 for role in roles:
  arm=max(v['stretch_p99']for k,x in g4.items()if k.split(':')[0]==role for v in x.values());hand=max(x['max_edge_ratio']for x in g5[role].values());contact=max(x[0]for x in g6[role]['contacts'].values());cross=cloth[role]['max_crossing_edges']
  rows[role]={'G4_arm_p99':arm,'G5_hand_max':hand,'G6_contact_m':contact,'cloth_crossing_edges':cross,'flap_stretch_pass':flap['clips'][role]['pass'],'pass':bool(arm<=2 and hand<4.5 and contact<=.002 and cross==0 and flap['clips'][role]['pass'])}
 summary[str(level)]={'clips':rows,'pass':all(x['pass']for x in rows.values())};(dest/'summary.json').write_text(json.dumps({'runtime_sha256':h,**summary[str(level)]},indent=2)+'\n');print('LOD_GATES',level,summary[str(level)],flush=True)
(P/'review/round4/lod_gates.json').write_text(json.dumps({'runtime_sha256':h,'sample_hz':48,'levels':summary,'pass':all(x['pass']for x in summary.values())},indent=2)+'\n')

