"""Finish the cached geometric LOD search with complete per-piece bakes and native tier materials."""
import bpy,sys,json,subprocess,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C,reduction_bake as B,search_reduction as S
from project_lod import project
W=P/'work/reduction';O=P/'review/reduction'
def pooled(v):
 rows=v['views'].values();inter=sum(r['iou']*(r['reference_pixels']+r['candidate_pixels'])/(1+r['iou'])for r in rows);return inter/(sum(r['reference_pixels']+r['candidate_pixels']for r in rows)-inter)
def candidate(info,kind,level,step,reduce=False,rebake=True):
 bpy.ops.wm.open_mainfile(filepath=str(P/info['blend']));C.reset();obj=bpy.data.objects['Body'if kind=='body'else'ClubMesh']
 if reduce:C.reduce(obj,.9)
 correction=project(obj)
 count=C.triangles(obj);tag=f'{kind}_lod{level}';suffix='final'if rebake else'probe';dest=W/f'{tag}_{step}_{suffix}.blend';tex=W/f'{tag}_{step}_final_textures'
 if rebake:B.bake(obj,tex)
 if kind=='body'and rebake:subprocess.run(['/usr/bin/python3',str(P/'scripts/reduction_previews.py'),str(tex)],check=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(dest));folder=O/tag/f'step_{step:02}_{suffix}';S.render(folder,kind,level,tex if kind=='body'and rebake else None,tiers=None if rebake else ['a']);v=S.metrics(O/tag/'reference_final',folder)if rebake else json.loads(subprocess.run(['/usr/bin/python3',str(P/'scripts/silhouette_metrics.py'),str(O/tag/'reference_final'),str(folder)],check=True,capture_output=True,text=True).stdout);v['pooled_iou']=pooled(v);v['pass']=v['pooled_iou']>=.97
 row={'step':step,'triangles':count,'blend':str(dest.relative_to(P)),'textures':str(tex.relative_to(P)),'renders':str(folder.relative_to(P)),'visual':v,'pass':v['pass'],'bake_revision':3,'projection_correction_max_m':correction};print('FINAL FAR',tag,step,count,v['pooled_iou'],v['min_ssim'],v['pass'],flush=True);return row
selection={}
for kind in ['body','club']:
 near=json.loads((O/f'{kind}_lod0_curve.json').read_text());first=next(r for r in near['steps']if r['blend']==near['accepted']);selection[kind]=[{k:first[k]for k in ['blend','textures','triangles']}]
 for level in [1,2,3]:
  tag=f'{kind}_lod{level}';seed=selection[kind][-1];cap=min(int(first['triangles']*[1,.55,.25,.10][level]),seed['triangles']-1);file=O/f'{tag}_curve.json';backup=O/f'{tag}_curve_first_bake.json'
  if file.exists()and not backup.exists():shutil.copyfile(file,backup)
  old=json.loads(backup.read_text())if backup.exists()else{};oldrows=[];done=bool(oldrows and oldrows[-1].get('visual',{}).get('pooled_iou',1)<.97)
  bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction_master.blend'));C.cleanup();camera=S.render(O/tag/'reference_final',kind,level);rows=[];accepted=None
  def save():
   file.write_text(json.dumps({'kind':kind,'level':level,'cap':cap,'camera':camera,'preliminary_curve':str(backup.relative_to(P))if backup.exists()else None,'steps':rows,'accepted':accepted['blend']if accepted else None,'thresholds':{'pooled_iou':.97}},indent=2))
  if done:
   choices=sorted([r for r in oldrows if r.get('visual',{}).get('pooled_iou',0)>=.97 and r['triangles']<=cap],key=lambda r:r['triangles'])
   for info in choices:
    row=candidate(info,kind,level,info['step']);rows.append(row)
    if row['visual']['pass']:row['gates']=S.gates(P/row['blend'],tag+f"_final{row['step']}");row['pass']=row['gates']['pass']
    if row['pass']:accepted={k:row[k]for k in ['blend','textures','triangles']}
    save()
    if accepted:break
  else:
   choices=[r for r in oldrows if 'blend'in r and r['triangles']<=cap and r['triangles']<seed['triangles']]
   if choices:
    info=max(choices,key=lambda r:r['triangles']);step=info['step'];row=candidate(info,kind,level,step,rebake=False);rows.append(row);save()
   else:
    bpy.ops.wm.open_mainfile(filepath=str(P/seed['blend']));C.reset();obj=bpy.data.objects['Body'if kind=='body'else'ClubMesh'];C.protect(obj,kind);group=obj.vertex_groups['_reduction_protect']
    for v in obj.data.vertices:
     for g in v.groups:
      if g.group==group.index:group.add([v.index],min(g.weight,.85),'REPLACE')
    step=0
    while C.triangles(obj)>cap:step+=1;C.reduce(obj,.9,planar=step==1);project(obj)
    path=W/f'{tag}_seed_final.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));info={'blend':str(path.relative_to(P))};row=candidate(info,kind,level,step);rows.append(row);save()
   while row['visual']['pass']and row['triangles']>24:
    step+=1;row=candidate(row,kind,level,step,True,False);rows.append(row);save()
   for probe in reversed(list(rows)):
    if not probe['visual']['pass']:continue
    row=candidate(probe,kind,level,probe['step']);rows.append(row)
    row['gates']=S.gates(P/row['blend'],tag+f"_final{row['step']}");row['pass']=row['gates']['pass']
    if row['pass']:accepted={k:row[k]for k in ['blend','textures','triangles']}
    save()
    if accepted:break
  assert accepted,('No acceptable distance LOD',kind,level)
  selection[kind].append(accepted);(O/'selection_partial.json').write_text(json.dumps(selection,indent=2))
(O/'selection.json').write_text(json.dumps(selection,indent=2));print('FINAL SELECTION',json.dumps(selection),flush=True)
