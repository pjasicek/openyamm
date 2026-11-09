import bpy,sys,json,runpy,os
from pathlib import Path
P=Path(__file__).resolve().parents[1]
exec((P/'scripts/reduction_balanced.py').read_text().split('config=json.loads')[0].replace('.4375','.4166666666667'))
from gates_summary import summarize
selection=json.loads((P/'review/reduction_soft/selection.json').read_text());curve=[];accepted=None
for step,ratio in enumerate([.125,.13],1):
 bpy.ops.wm.open_mainfile(filepath=str(P/selection['0']['blend']));cleanup();reset()
 for name,kind in [('Body','body'),('KnifeAsset','knife')]:
  ob=bpy.data.objects[name];old=ob.vertex_groups.get('_reduction_protect')
  if old:ob.vertex_groups.remove(old)
  protect(ob,kind);g=ob.vertex_groups['_reduction_protect']
  for v in ob.data.vertices:
   weight=next((x.weight for x in v.groups if x.group==g.index),0)
   if weight>0:g.add([v.index],.98 if ob.data.attributes['_silhouette_protect'].data[v.index].value else .35,'REPLACE')
  reduce(ob,ratio,planar=True,factor=2)
 path=W/f'lod3_polished{step}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));os.environ.update(GATE_BLEND=str(path),GATE_REPORT=str(ROOT/f'lod3_polished{step}_clothfit.json'),GATE_RENDER='0',FIT_CLOTH='1',FIT_MAX_M='.03');runpy.run_path(str(P/'scripts/initial_checks.py'),run_name='__main__');os.environ.pop('FIT_CLOTH');reset();folder=W/f'lod3_polished{step}';textures(folder,3);bpy.ops.wm.save_as_mainfile(filepath=str(path));render(ROOT/f'lod3/direct{step}',3,folder);scores=metrics(P/'review/final_comparison/lod3/reference',ROOT/f'lod3/direct{step}');counts={n:triangles(bpy.data.objects[n])for n in ['Body','KnifeAsset']};gate=None;passed=scores['pooled_iou']>=.97
 if passed:
  report=ROOT/f'lod3_polished{step}_gates.json';os.environ.update(GATE_BLEND=str(path),GATE_REPORT=str(report),GATE_RENDER='0');runpy.run_path(str(P/'scripts/initial_checks.py'),run_name='__main__');gate=summarize(json.loads(report.read_text()));passed=gate['pass']
 row={'step':step,'ratio':ratio,'triangles':sum(counts.values()),'counts':counts,'visual':scores,'rig_gate':gate,'pass':passed,'blend':str(path.relative_to(P)),'textures':str(folder)};curve.append(row);(ROOT/'lod3_polished_curve.json').write_text(json.dumps(curve,indent=2));print('POLISHED_LOD3',ratio,counts,scores['pooled_iou'],gate,flush=True)
 if passed:accepted=row;break
assert accepted is not None
selection['3']=accepted;(P/'review/reduction_soft/selection.json').write_text(json.dumps(selection,indent=2));print('SELECTED3',accepted['triangles'],flush=True)

from shutil import copytree
last=P/'review/final_comparison/lod3/selected';copytree(last,last.with_name('selected_rejected_012'),dirs_exist_ok=True);copytree(ROOT/f'lod3/direct{accepted["step"]}',last,dirs_exist_ok=True);scorespath=P/'review/final_comparison/scores.json';all_scores=json.loads(scorespath.read_text());all_scores['3']=dict(accepted['visual'],pass_result=True);all_scores['3']['pass']=True;scorespath.write_text(json.dumps(all_scores,indent=2))
