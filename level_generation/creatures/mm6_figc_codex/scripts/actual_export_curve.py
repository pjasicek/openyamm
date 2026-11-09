"""Select the last passing steps using actual GLB exports, then retain those exact files for validation."""
import bpy,json,os,runpy,sys,subprocess,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round3';A=R/'actual_curve';A.mkdir(exist_ok=True);sys.path.insert(0,str(P/'scripts'));import compare_exported_lods as C
C.O=A/'renders';C.O.mkdir(exist_ok=True);records=[];selected={};os.environ.pop('FIGC_POLICY',None)
def ctag(part,level,step):return f'{part.lower()}_l{level}_s{step:05.2f}'.replace('.','p')
def test(level,steps):
 parts={p:ctag(p,level,steps[p]) for p in steps};tag='actual_l'+str(level)+'_'+'_'.join(f'{steps[p]:05.2f}'.replace('.','p') for p in ['Body','Axe','Shield']);path=A/f'{tag}.blend'
 for p,n in parts.items():
  if not (R/'candidates'/f'{n}.json').exists():
   os.environ['FIGC_REDUCE']=f'{p},{level},{steps[p]}';os.environ['FIGC_SKIP_RENDER']='1'
   try:runpy.run_path(str(P/'scripts/reduction_candidate.py'),run_name='__main__')
   except SystemExit as e:assert e.code==0
 bpy.ops.wm.open_mainfile(filepath=str(R/'before/work/final_motion.blend'))
 for p,n in parts.items():
  with bpy.data.libraries.load(str(R/'candidates'/f'{n}.blend'),link=False) as (src,dst):dst.meshes=[p+'_reduction_mesh']
  o=bpy.data.objects[p];o.data=dst.meshes[0]
  for x in bpy.data.objects:x.select_set(x==o)
  bpy.context.view_layer.objects.active=o;bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
 bpy.ops.wm.save_as_mainfile(filepath=str(path));E=A/tag;E.mkdir(exist_ok=True);os.environ['FIGC_EXPORT_SOURCE']=str(path);os.environ['FIGC_EXPORT_DIR']=str(E);runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
 out=C.render(E/'mm6_figc_lod0.glb',level,tag);metrics=A/f'{tag}.json';subprocess.run(['/usr/bin/python3',str(P/'scripts/measure_reduction.py'),str(R/'export_comparison'/f'reference_lod{level}'),str(out),str(metrics)],check=True);m=json.loads(metrics.read_text());counts={p:json.loads((R/'candidates'/f'{n}.json').read_text())['triangles'] for p,n in parts.items()}
 row={'tag':tag,'algorithm':'actual_export_connected_uv_and_rig_protection','level':level,'steps':dict(steps),'parts':parts,'part_triangles':counts,'triangles':sum(counts.values()),'minimum_iou':m['minimum_iou'],'minimum_ssim':m['minimum_ssim'],'visual_pass':m['pass'],'blend':str(path.relative_to(P)),'export_dir':str(E.relative_to(P)),'renders':str(out.relative_to(P))};records.append(row);(R/'actual_curve.json').write_text(json.dumps({'curve':records,'selected':selected},indent=2)+'\n');print('ACTUAL_CURVE',json.dumps(row),flush=True);return row
for level in range(4):
 steps={p:0.0 for p in ['Body','Axe','Shield']};selected[str(level)]=test(level,steps)
 for part in steps:
  lower=0.;upper=None
  for step in range(1,21):
   steps[part]=step;row=test(level,steps)
   if row['visual_pass']:
    previous=selected[str(level)];lower=step;selected[str(level)]=row
    if row['triangles']==previous['triangles']:row['stop_reason']='protected topology floor';upper=step;break
   else:upper=step;break
  assert upper is not None
  for _ in range(2):
   mid=(lower+upper)/2;steps[part]=mid;row=test(level,steps)
   if row['visual_pass']:lower=mid;selected[str(level)]=row
   else:upper=mid
  steps[part]=lower
 (R/'actual_curve.json').write_text(json.dumps({'curve':records,'selected':selected},indent=2)+'\n')
d=json.loads((R/'curve.json').read_text());d['curve'].extend(records);d['selected']=selected;(R/'curve.json').write_text(json.dumps(d,indent=2)+'\n')
for level,row in selected.items():
 E=P/row['export_dir'];dest=P/'export' if level=='0' else R/f'export_lod{level}';dest.mkdir(exist_ok=True)
 for name in ['mm6_figc_lod0.glb','mm6_figc_authoring.blend','export_info.json']:shutil.copy2(E/name,dest/name)
 shutil.copy2(P/row['blend'],R/f'lod{level}.blend')
 if level=='0':shutil.copy2(P/row['blend'],P/'work/final_motion.blend')
print('ACTUAL_CURVE_COMPLETE',json.dumps({k:v['triangles'] for k,v in selected.items()}),flush=True)
