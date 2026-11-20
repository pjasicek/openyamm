import bpy,sys,json,runpy,os
from pathlib import Path
P=Path(__file__).resolve().parents[1]
exec((P/'scripts/reduction_balanced.py').read_text().split('config=json.loads')[0])
from gates_summary import summarize
selection=json.loads((ROOT/'selection.json').read_text());curve=[];accepted=None
for step,ratio in enumerate([.10,.115,.13,.15],1):
 bpy.ops.wm.open_mainfile(filepath=str(P/selection['0']['blend']));cleanup();reset()
 for name,kind in [('Body','body'),('KnifeAsset','knife')]:
  ob=bpy.data.objects[name];old=ob.vertex_groups.get('_reduction_protect')
  if old:ob.vertex_groups.remove(old)
  protect(ob,kind);g=ob.vertex_groups['_reduction_protect']
  for v in ob.data.vertices:
   weight=next((x.weight for x in v.groups if x.group==g.index),0)
   if weight>0:g.add([v.index],.4 if weight>.5 else .95,'REPLACE')
  reduce(ob,ratio,planar=True,factor=2)
 path=W/f'lod3_direct{step}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));os.environ.update(GATE_BLEND=str(path),GATE_REPORT=str(ROOT/f'lod3_direct{step}_clothfit.json'),GATE_RENDER='0',FIT_CLOTH='1',FIT_MAX_M='.03');runpy.run_path(str(P/'scripts/initial_checks.py'),run_name='__main__');os.environ.pop('FIT_CLOTH');reset();folder=W/f'lod3_direct{step}';textures(folder,3);bpy.ops.wm.save_as_mainfile(filepath=str(path));render(ROOT/f'lod3/direct{step}',3,folder);scores=metrics(ROOT/'lod3/reference',ROOT/f'lod3/direct{step}');counts={n:triangles(bpy.data.objects[n])for n in ['Body','KnifeAsset']};gate=None;passed=scores['pooled_iou']>=.97
 if passed:
  report=ROOT/f'lod3_direct{step}_gates.json';os.environ.update(GATE_BLEND=str(path),GATE_REPORT=str(report),GATE_RENDER='0');runpy.run_path(str(P/'scripts/initial_checks.py'),run_name='__main__');gate=summarize(json.loads(report.read_text()));passed=gate['pass']
 row={'step':step,'ratio':ratio,'triangles':sum(counts.values()),'counts':counts,'visual':scores,'rig_gate':gate,'pass':passed,'blend':str(path.relative_to(P)),'textures':str(folder)};curve.append(row);(ROOT/'lod3_direct_curve.json').write_text(json.dumps(curve,indent=2));print('DIRECT_LOD3',ratio,counts,scores['pooled_iou'],gate,flush=True)
 if passed:accepted=row;break
assert accepted is not None
selection['3']=accepted;(ROOT/'selection.json').write_text(json.dumps(selection,indent=2));print('SELECTED3',accepted['triangles'],flush=True)
