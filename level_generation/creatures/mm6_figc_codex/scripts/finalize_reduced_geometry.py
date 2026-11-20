"""Remove all-pose hidden faces where that changes no render, then gate the exact selected GLBs."""
import json,os,runpy,shutil,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round3';sys.path.insert(0,str(P/'scripts'));import compare_exported_lods as C
C.O=R/'hidden_review';C.O.mkdir(exist_ok=True);d=json.loads((R/'curve.json').read_text())
for level in range(4):
 row=d['selected'][str(level)];os.environ['FIGC_HIDDEN_SOURCE']=str(R/f'lod{level}.blend');os.environ['FIGC_HIDDEN_PREFIX']=f'hidden_lod{level}';runpy.run_path(str(P/'scripts/remove_hidden_faces.py'),run_name='__main__');hidden=json.loads((R/f'hidden_lod{level}_faces.json').read_text());E=R/f'hidden_export_lod{level}';source=R/f'hidden_lod{level}_clean.blend';os.environ['FIGC_EXPORT_SOURCE']=str(source);os.environ['FIGC_EXPORT_DIR']=str(E);runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__');folder=C.render(E/'mm6_figc_lod0.glb',level,'hidden');mfile=R/f'hidden_lod{level}_metrics.json';deltafile=R/f'hidden_lod{level}_delta.json'
 for ref,out in [(R/'export_comparison'/f'reference_lod{level}',mfile),(P/row['renders'],deltafile)]:subprocess.run(['/usr/bin/python3',str(P/'scripts/measure_reduction.py'),str(ref),str(folder),str(out)],check=True)
 m=json.loads(mfile.read_text());delta=json.loads(deltafile.read_text());removed=sum(x['removed'] for x in hidden.values());dest=P/'export' if level==0 else R/f'export_lod{level}'
 if removed and m['pass'] and delta['minimum_iou']>=.999 and delta['minimum_ssim']>=.999:
  old=row;row=dict(old,tag=f'final_lod{level}',parent_trial=old['tag'],blend=str(source.relative_to(P)),export_dir=str(E.relative_to(P)),renders=str(folder.relative_to(P)),triangles=sum(x['after'] for x in hidden.values()),part_triangles={k:v['after'] for k,v in hidden.items()},minimum_iou=m['minimum_iou'],minimum_ssim=m['minimum_ssim'],hidden_removed=removed,hidden_delta_iou=delta['minimum_iou'],hidden_delta_ssim=delta['minimum_ssim'])
  for name in ['mm6_figc_lod0.glb','mm6_figc_authoring.blend','export_info.json']:shutil.copy2(E/name,dest/name)
  shutil.copy2(source,R/f'lod{level}.blend')
  if level==0:shutil.copy2(source,P/'work/final_motion.blend')
  d['selected'][str(level)]=row;d['curve'].append(row)
 W=P/'work' if level==0 else R/f'validation_lod{level}';os.environ['FIGC_EXPORT_DIR']=str(dest);os.environ['FIGC_VALIDATION_DIR']=str(W);runpy.run_path(str(P/'scripts/gates_exported.py'),run_name='__main__');g=json.loads((W/'export_full_gates.json').read_text());faults=[]
 for clip,v in g.items():
  for key,limit in [('arm_p99',1.5),('finger_max',4.5),('head_mm',10),('L_contact_mm',2),('R_contact_mm',2),('Axe_mm',2),('Shield_mm',2)]:
   if v[key]>limit:faults.append([clip,key,v[key],limit])
  if v['minimum_z']<0:faults.append([clip,'floor',v['minimum_z']])
  if clip not in ['Death','Dead'] and (v['pelvis_min']<=.9 or v['trunk_lean_max']>=20):faults.append([clip,'posture'])
 row.update(rig_pass=not faults,rig_faults=faults);(R/'gates'/f'lod{level}_export.json').write_text(json.dumps({'pass':not faults,'faults':faults,'clips':g},indent=2)+'\n');(R/'curve.json').write_text(json.dumps(d,indent=2)+'\n');print('FINAL_GEOMETRY',level,row['triangles'],row['minimum_iou'],row['minimum_ssim'],faults,flush=True)
 assert not faults
