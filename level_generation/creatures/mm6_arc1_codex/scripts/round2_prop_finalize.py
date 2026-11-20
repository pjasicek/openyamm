import bpy,sys,json,shutil,subprocess,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from round2_reduce import *
R=P/'review/round2';D=R/'reduction';S=json.loads((D/'selected.json').read_text());metrics=json.loads((D/'final_material_metrics.json').read_text());curve=json.loads((D/'curve.json').read_text())
for part,level,ratios in [('bow',1,[.85,.9]),('arrow',3,[.9,1.])]:
 old=S[part][str(level)].copy();old.update(metrics['measurements'][part][str(level)]['arc1_a']);old['strategy']='rejected final pose silhouette';old['rig_gates']='visual_rejection';curve.append(old)
 for ratio in ratios:
  ob,rig=reset(part);count,protection=reduce(ob,rig,part,level,ratio);path=P/f'work/round2/{part}_l{level}_final{int(ratio*100)}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));tag=f'{part}_l{level}_arc1_a_baked'
  render(ob,rig,part,level,tag,P/'work/round2/metric_tiers/baked/arc1_a')
  value=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/round2_reduction_metrics.py'),str(D),f'{part}_l{level}_arc1_a_high',tag],text=True));print('PROP_FINAL',part,level,count,value,flush=True)
  row={'part':part,'lod':level,'ratio':ratio,'triangles':count,'protected':protection,'blend':str(path.relative_to(P)),'strategy':'refined final pose; shared rebake',**value,'rig_gates':'pending'}
  curve.append(row)
  if value['pass']:S[part][str(level)]=row;metrics['measurements'][part][str(level)]['arc1_a']=value;break
 else:raise AssertionError((part,level,'No passing prop candidate'))
metrics['failures']=[(p,l,t)for p,levels in metrics['measurements'].items()for l,tiers in levels.items()for t,m in tiers.items()if not m['pass']];assert not metrics['failures']
(D/'selected.json').write_text(json.dumps(S,indent=2));(D/'curve.json').write_text(json.dumps(curve,indent=2));(D/'final_material_metrics.json').write_text(json.dumps(metrics,indent=2))
runpy.run_path(str(P/'scripts/round2_assemble.py'),run_name='__main__')
for level in [1,3]:
 shutil.copy2(P/f'work/round2/lod{level}.blend',P/'work/rig_equipped.blend')
 for name in ['round2_contact_gates.py','round2_equipment_only.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
 eq=json.loads((P/'work/equipment_gate.json').read_text());assert all(row['equipment_contact_cm']==0 and row['floor_min_cm']>=0 for row in eq.values())
 out=R/f'lod_gates/lod{level}';shutil.copy2(P/'work/equipment_gate.json',out/'equipment_gate.json');shutil.copy2(R/'contact_gates.json',out/'contact_gates.json')
 status=json.loads((out/'status.json').read_text());assert status['pass'];status['prop_recheck']='Final silhouette-refined prop candidate; full clip grip/contact and equipment/floor checks repeated';(out/'status.json').write_text(json.dumps(status,indent=2))
shutil.copy2(P/'work/round2/lod0.blend',P/'work/rig_equipped.blend');shutil.copy2(R/'lod_gates/lod0/equipment_gate.json',P/'work/equipment_gate.json');shutil.copy2(R/'lod_gates/lod0/contact_gates.json',R/'contact_gates.json')
for name in ['round2_pack_lods.py','pack_runtime.py']:subprocess.run(['/usr/bin/python3',str(P/'scripts'/name)],check=True)
runpy.run_path(str(P/'scripts/round2_endchecks.py'),run_name='__main__')
