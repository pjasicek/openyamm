"""Resume the projected geometric search, rebaking only final candidates and preserving all rejection evidence."""
import bpy,sys,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
import reduction_common as C,reduction_bake as B,search_reduction as S
from project_lod import project
W=P/'work/reduction';O=P/'review/reduction';selection=json.loads((O/'selection_partial.json').read_text())
def pooled(v):
 r=list(v['views'].values());inter=sum(x['iou']*(x['reference_pixels']+x['candidate_pixels'])/(1+x['iou'])for x in r);return inter/(sum(x['reference_pixels']+x['candidate_pixels']for x in r)-inter)
def measure(info,kind,level,step,reduce=False,bake=False):
 bpy.ops.wm.open_mainfile(filepath=str(P/info['blend']));C.reset();obj=bpy.data.objects['Body'if kind=='body'else'ClubMesh']
 if reduce:C.reduce(obj,.9)
 correction=project(obj);tag=f'{kind}_lod{level}';suffix='final'if bake else'probe';dest=W/f'{tag}_{step}_{suffix}.blend';tex=W/f'{tag}_{step}_final_textures'
 if bake:
  B.bake(obj,tex)
  if kind=='body':subprocess.run(['/usr/bin/python3',str(P/'scripts/reduction_previews.py'),str(tex)],check=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(dest));folder=O/tag/f'step_{step:02}_{suffix}';S.render(folder,kind,level,tex if kind=='body'and bake else None,tiers=None if bake else['a'])
 v=S.metrics(O/tag/'reference_final',folder)if bake else json.loads(subprocess.run(['/usr/bin/python3',str(P/'scripts/silhouette_metrics.py'),str(O/tag/'reference_final'),str(folder)],check=True,capture_output=True,text=True).stdout);v['pooled_iou']=pooled(v);v['pass']=v['pooled_iou']>=.97
 row={'step':step,'triangles':C.triangles(obj),'blend':str(dest.relative_to(P)),'textures':str(tex.relative_to(P)),'renders':str(folder.relative_to(P)),'visual':v,'pass':v['pass'],'bake_revision':3,'projection_correction_max_m':correction};print('DISTANCE',tag,step,row['triangles'],v['pooled_iou'],v['min_ssim'],flush=True);return row
for kind in ['club']:
 d=json.loads((O/f'{kind}_lod0_curve.json').read_text());near=next(r for r in d['steps']if r['blend']==d['accepted']);selection[kind]=[{k:near[k]for k in ['blend','textures','triangles']}]
 for level in [1,2,3]:
  tag=f'{kind}_lod{level}';file=O/f'{tag}_curve.json';old=json.loads(file.read_text())if file.exists()else{};rows=[r for r in old.get('steps',[])if r.get('bake_revision')==3];seed=selection[kind][0];cap=min(int(near['triangles']*[1,.55,.25,.1][level]),selection[kind][-1]['triangles']-1);accepted=None
  ref=O/tag/'reference_final'
  if len(list(ref.glob('*.png')))<(96 if kind=='body'else 8):
   bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction_master.blend'));C.cleanup();camera=S.render(ref,kind,level)
  else:camera=old.get('camera',{'switch_pixels':[None,550,220,88][level]})
  def save():
   file.write_text(json.dumps({'kind':kind,'level':level,'cap':cap,'camera':camera,'steps':rows,'accepted':accepted['blend']if accepted else None,'thresholds':{'pooled_iou':.97},'surface_projection':'matching original piece; barycentric skin transfer'},indent=2))
  complete=any(not r['visual']['pass']for r in rows)
  if not complete:
   if rows:row=min(rows,key=lambda r:r['triangles']);step=row['step']
   else:
    bpy.ops.wm.open_mainfile(filepath=str(P/seed['blend']));C.reset();obj=bpy.data.objects['Body'if kind=='body'else'ClubMesh'];C.protect(obj,kind);group=obj.vertex_groups['_reduction_protect']
    for v in obj.data.vertices:
     for g in v.groups:
      if g.group==group.index:group.add([v.index],min(g.weight,.85),'REPLACE')
    step=0
    while C.triangles(obj)>cap:step+=1;C.reduce(obj,max(.9,cap/C.triangles(obj)),planar=step==1);project(obj)
    dest=W/f'{tag}_seed_final.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));row=measure({'blend':str(dest.relative_to(P))},kind,level,step);rows.append(row);save()
   while row['visual']['pass']and row['triangles']>24:
    step+=1;row=measure(row,kind,level,step,True);rows.append(row);save()
  choices={}
  for r in rows:
   if r['visual']['pass']and r['triangles']<=cap and not(level==1 and r['triangles']<(2400 if kind=='body'else 290)):
    if r['triangles']not in choices or r['visual']['min_ssim']is not None:choices[r['triangles']]=r
  for count,info in sorted(choices.items()):
   if info['visual']['min_ssim']is None:row=measure(info,kind,level,info['step'],bake=True);rows.append(row)
   else:row=info
   row['gates']=S.gates(P/row['blend'],f'{tag}_surface_v4_{row["step"]}');row['pass']=row['visual']['pass']and row['gates']['pass']
   if row['pass']:accepted={k:row[k]for k in ['blend','textures','triangles']}
   save();print('SELECT CHECK',tag,count,row['gates'],flush=True)
   if accepted:break
  assert accepted,(tag,'No passing candidate')
  selection[kind].append(accepted);(O/'selection_partial.json').write_text(json.dumps(selection,indent=2))
(O/'selection.json').write_text(json.dumps(selection,indent=2));print('SELECTED',json.dumps(selection),flush=True)
