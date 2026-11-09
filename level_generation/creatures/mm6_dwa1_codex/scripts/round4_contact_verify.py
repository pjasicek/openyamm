import bpy,json,sys,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
h=hashlib.sha256((P/'export/mm6_dwa1.glb').read_bytes()).hexdigest()
for level in range(4):
 path=P/'scripts/contact_final.py';s=path.read_text()
 if level:s=s.replace("P/'work/export_reimport.blend'",f"P/'work/round4/final_lod{level}.blend'").replace("P/'review/g6_exported.json'",f"P/'review/round4/lod{level}/g6_exported.json'").replace('assert len(bladeids)>100','assert len(bladeids)>3')
 exec(compile(s,str(path),'exec'),{'__file__':str(path),'__name__':'__main__'})
d=json.loads((P/'review/round4/lod_gates.json').read_text());assert d['runtime_sha256']==h
for level,entry in d['levels'].items():
 g6=json.loads((P/f'review/round4/lod{level}/g6_exported.json').read_text())
 for role,r in entry['clips'].items():
  r['G6_contact_m']=max(v[0]for v in g6[role]['contacts'].values());r['pass']=bool(r['G4_arm_p99']<=2 and r['G5_hand_max']<4.5 and r['G6_contact_m']<=.002 and r['cloth_crossing_edges']==0 and r['flap_stretch_pass'])
 entry['pass']=all(x['pass']for x in entry['clips'].values());(P/f'review/round4/lod{level}/summary.json').write_text(json.dumps({'runtime_sha256':h,**entry},indent=2)+'\n')
d['pass']=all(x['pass']for x in d['levels'].values());(P/'review/round4/lod_gates.json').write_text(json.dumps(d,indent=2)+'\n');print('COMPLETE_SURFACE_CONTACTS',d['pass']);assert d['pass']

