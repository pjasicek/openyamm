"""Export and test every selected LOD, serially, using the production GLB reimport gates."""
import bpy,json,os,runpy,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round3';d=json.loads((R/'curve.json').read_text())
for level in range(4):
 row=d['selected'][str(level)];path=R/f'lod{level}.blend';shutil.copy2(P/row['blend'],path)
 if level==0:shutil.copy2(path,P/'work/final_motion.blend')
 os.environ['FIGC_EXPORT_SOURCE']=str(path);os.environ['FIGC_EXPORT_DIR']=str(P/'export' if level==0 else R/f'export_lod{level}');os.environ['FIGC_VALIDATION_DIR']=str(P/'work' if level==0 else R/f'validation_lod{level}')
 runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__');runpy.run_path(str(P/'scripts/gates_exported.py'),run_name='__main__')
 r=json.loads((Path(os.environ['FIGC_VALIDATION_DIR'])/'export_full_gates.json').read_text());faults=[]
 for clip,v in r.items():
  for key,limit in [('arm_p99',1.5),('finger_max',4.5),('head_mm',10),('L_contact_mm',2),('R_contact_mm',2),('Axe_mm',2),('Shield_mm',2)]:
   if v[key]>limit:faults.append([clip,key,v[key],limit])
  if v['minimum_z']<0:faults.append([clip,'floor',v['minimum_z']])
  if clip not in ['Death','Dead'] and (v['pelvis_min']<=.9 or v['trunk_lean_max']>=20):faults.append([clip,'posture'])
 report={'pass':not faults,'faults':faults,'clips':r};(R/'gates'/f'lod{level}_export.json').write_text(json.dumps(report,indent=2)+'\n');row['rig_pass']=not faults;row['rig_faults']=faults
 (R/'curve.json').write_text(json.dumps(d,indent=2)+'\n');print('EXPORTED_LOD_GATE',level,report['pass'],faults,flush=True)
