import bpy,sys,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C,search_reduction as S,reduction_bake as B
from project_lod import project
W=P/'work/reduction';O=P/'review/reduction';rows=[];accepted=None
for target in [952,1024]:
 if target==952:
  bpy.ops.wm.open_mainfile(filepath=str(W/'body_lod3_direct_near_soft.blend'));C.reset()
 else:
  bpy.ops.wm.open_mainfile(filepath=str(W/'body_lod0_4_final.blend'));C.reset();o=bpy.data.objects['Body'];C.protect(o,'body');group=o.vertex_groups['_reduction_protect']
  for v in o.data.vertices:
   for g in v.groups:
    if g.group==group.index:group.add([v.index],min(g.weight,.85),'REPLACE')
  C.reduce(o,target/C.triangles(o));project(o,minimum=.02)
 o=bpy.data.objects['Body'];dest=W/f'body_lod3_direct_{target}_final.blend';tex=W/f'body_lod3_direct_{target}_textures';B.bake(o,tex);subprocess.run(['/usr/bin/python3',str(P/'scripts/reduction_previews.py'),str(tex)],check=True);count=C.triangles(o);bpy.ops.wm.save_as_mainfile(filepath=str(dest));folder=O/f'body_lod3/direct_{target}_final';S.render(folder,'body',3,tex);v=S.metrics(O/'body_lod3/reference_final',folder);rs=list(v['views'].values());inter=sum(x['iou']*(x['reference_pixels']+x['candidate_pixels'])/(1+x['iou'])for x in rs);v['pooled_iou']=inter/(sum(x['reference_pixels']+x['candidate_pixels']for x in rs)-inter);v['pass']=v['pooled_iou']>=.97
 row={'step':target,'triangles':count,'blend':str(dest.relative_to(P)),'textures':str(tex.relative_to(P)),'renders':str(folder.relative_to(P)),'visual':v,'pass':False,'bake_revision':3,'method':'direct protected collapse; only projection outliers over 2cm reprojected'}
 if v['pass']:row['gates']=S.gates(dest,f'body_lod3_direct{target}');row['pass']=row['gates']['pass']
 rows.append(row)
 if row['pass']:accepted={k:row[k]for k in ['blend','textures','triangles']}
 (O/'body_lod3_curve.json').write_text(json.dumps({'kind':'body','level':3,'steps':rows,'accepted':accepted['blend']if accepted else None,'cap_guidance':.10,'absolute_ratio_ceiling':.11,'thresholds':{'pooled_iou':.97},'camera':{'switch_pixels':88}},indent=2));print('ACTUAL FAR3',count,v['pooled_iou'],v['min_ssim'],row.get('gates'),flush=True)
 if accepted:break
assert accepted,'Final far material comparison failed'
selection=json.loads((O/'selection_partial.json').read_text());selection['body']=selection['body'][:3]+[accepted];(O/'selection_partial.json').write_text(json.dumps(selection,indent=2))
