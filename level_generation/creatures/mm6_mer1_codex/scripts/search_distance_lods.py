"""Select distance LODs by measured projected silhouette; all selected geometry is rebaked and rig-gated."""
import bpy,sys,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
import reduction_common as C,reduction_bake as B,search_reduction as S
W=P/'work/reduction';O=P/'review/reduction'
def pooled(v):
 rows=v['views'].values();inter=sum(r['iou']*(r['reference_pixels']+r['candidate_pixels'])/(1+r['iou'])for r in rows);union=sum(r['reference_pixels']+r['candidate_pixels']for r in rows)-inter;return inter/union
selection={}
for kind in ['body','club']:
 lod0=json.loads((O/f'{kind}_lod0_curve.json').read_text());first=next(s for s in lod0['steps']if s['blend']==lod0['accepted']);selection[kind]=[{k:first[k]for k in ['blend','textures','triangles']}]
 for level in [1,2,3]:
  tag=f'{kind}_lod{level}';seed=selection[kind][-1];cap=int(first['triangles']*[1,.55,.25,.10][level]);cap=min(cap,seed['triangles']-1)
  prior=O/f'{tag}_curve.json'
  if prior.exists():
   data=json.loads(prior.read_text());rows=data['steps'];camera=data['camera'];accepted=None
  else:
   bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction_master.blend'));C.cleanup();camera=S.render(O/tag/'reference',kind,level)
   bpy.ops.wm.open_mainfile(filepath=str(P/seed['blend']));C.cleanup();C.reset();obj=bpy.data.objects['Body'if kind=='body'else'ClubMesh'];C.protect(obj,kind)
   group=obj.vertex_groups['_reduction_protect']
   for v in obj.data.vertices:
    for g in v.groups:
     if g.group==group.index:group.add([v.index],min(g.weight,.85),'REPLACE')
   last=P/seed['blend'];rows=[];accepted=None
   for step in range(1,35):
    if step>1:bpy.ops.wm.open_mainfile(filepath=str(last));C.reset();obj=bpy.data.objects['Body'if kind=='body'else'ClubMesh']
    C.reduce(obj,.9,planar=step==1);count=C.triangles(obj);dest=W/f'{tag}_{step}.blend';tex=W/f'{tag}_{step}_textures'
    if count>cap:
     bpy.ops.wm.save_as_mainfile(filepath=str(dest));last=dest;rows.append({'step':step,'triangles':count,'pass':False,'reason':'above distance triangle cap'});continue
    B.bake(obj,tex)
    if kind=='body':subprocess.run(['/usr/bin/python3',str(P/'scripts/reduction_previews.py'),str(tex)],check=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(dest));S.render(O/tag/f'step_{step:02}',kind,level,tex if kind=='body'else None);v=S.metrics(O/tag/'reference',O/tag/f'step_{step:02}');v['pooled_iou']=pooled(v);v['pass']=v['pooled_iou']>=.97
    row={'step':step,'triangles':count,'blend':str(dest.relative_to(P)),'textures':str(tex.relative_to(P)),'visual':v,'pass':v['pass']};rows.append(row)
    (O/f'{tag}_curve.json').write_text(json.dumps({'kind':kind,'level':level,'camera':camera,'cap':cap,'steps':rows},indent=2));print('FAR LOD',tag,step,count,v['pooled_iou'],v['min_ssim'],v['pass'],flush=True)
    if not v['pass'] or count<24:break
    last=dest
  for row in reversed(rows):
   if not row.get('visual',{}).get('pass'):continue
   row['gates']=S.gates(P/row['blend'],tag+f"_s{row['step']}")
   row['pass']=row['gates']['pass']
   (O/f'{tag}_curve.json').write_text(json.dumps({'kind':kind,'level':level,'camera':camera,'cap':cap,'steps':rows,'accepted':row['blend']if row['pass']else None},indent=2))
   if row['pass']:accepted={k:row[k]for k in ['blend','textures','triangles']};break
  assert accepted,('No passing distance LOD',kind,level)
  selection[kind].append(accepted);(O/'selection_partial.json').write_text(json.dumps(selection,indent=2))
(O/'selection.json').write_text(json.dumps(selection,indent=2));print('SELECTED',json.dumps(selection),flush=True)
