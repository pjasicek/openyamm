"""Resolve the earlier authoring-only warning against actual exported geometry before selecting the minimum."""
import json,os,runpy,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round3';d=json.loads((R/'curve.json').read_text());other=json.loads((R/'soft_arms_curve.json').read_text())
for level in [0,1]:
 rows=[r for r in other['curve'] if r['level']==level and r['visual_pass']];row=min(rows,key=lambda r:r['triangles']);path=R/'soft_arms_joint'/f"{row['tag']}.blend"
 os.environ['FIGC_EXPORT_SOURCE']=str(path);E=R/f'soft_export_lod{level}';W=R/f'soft_validation_lod{level}';os.environ['FIGC_EXPORT_DIR']=str(E);os.environ['FIGC_VALIDATION_DIR']=str(W)
 runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__');runpy.run_path(str(P/'scripts/gates_exported.py'),run_name='__main__');report=json.loads((W/'export_full_gates.json').read_text());faults=[]
 for clip,v in report.items():
  for key,limit in [('arm_p99',1.5),('finger_max',4.5),('head_mm',10),('L_contact_mm',2),('R_contact_mm',2),('Axe_mm',2),('Shield_mm',2)]:
   if v[key]>limit:faults.append([clip,key,v[key],limit])
  if v['minimum_z']<0:faults.append([clip,'floor',v['minimum_z']])
  if clip not in ['Death','Dead'] and (v['pelvis_min']<=.9 or v['trunk_lean_max']>=20):faults.append([clip,'posture'])
 row['rig_pass']=not faults;row['rig_faults']=faults;row['blend']=str(path.relative_to(P));row['algorithm']='weighted_arm_protection';row.pop('rig_faults_authoring',None)
 (R/'gates'/f'soft_lod{level}_export.json').write_text(json.dumps({'pass':not faults,'faults':faults,'clips':report},indent=2)+'\n');d['curve'].append(row)
 if not faults and row['triangles']<d['selected'][str(level)]['triangles']:
  d['selected'][str(level)]=row;destE=P/'export' if level==0 else R/f'export_lod{level}';destW=P/'work' if level==0 else R/f'validation_lod{level}'
  for name in ['mm6_figc_lod0.glb','mm6_figc_authoring.blend','export_info.json']:shutil.copy2(E/name,destE/name)
  for name in ['export_validation.blend','export_full_gates.json','scale_calibration.json']:shutil.copy2(W/name,destW/name)
  shutil.copy2(path,R/f'lod{level}.blend');shutil.copy2(R/'gates'/f'soft_lod{level}_export.json',R/'gates'/f'lod{level}_export.json')
  if level==0:shutil.copy2(path,P/'work/final_motion.blend')
 (R/'curve.json').write_text(json.dumps(d,indent=2)+'\n');print('SOFT_EXPORT_CHECK',level,not faults,faults,'selected',d['selected'][str(level)]['triangles'],flush=True)
for key in ['FIGC_EXPORT_SOURCE','FIGC_EXPORT_DIR','FIGC_VALIDATION_DIR']:os.environ.pop(key,None)
runpy.run_path(str(P/'scripts/preservation_gate.py'),run_name='__main__')
