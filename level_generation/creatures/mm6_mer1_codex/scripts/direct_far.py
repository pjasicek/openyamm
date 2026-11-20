import bpy,sys,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C,search_reduction as S
from project_lod import project
W=P/'work/reduction';O=P/'review/reduction';rows=[]
for name,source,protect,minimum in [('master_soft','work/before_death_surface.blend',.85,.02),('master_plain','work/before_death_surface.blend',0,.02),('master_mid','work/before_death_surface.blend',.5,.02)]:
 bpy.ops.wm.open_mainfile(filepath=str(P/source));C.reset();o=bpy.data.objects['Body'];C.protect(o,'body');group=o.vertex_groups['_reduction_protect']
 for v in o.data.vertices:
  for g in v.groups:
   if g.group==group.index:group.add([v.index],min(g.weight,protect),'REPLACE')
 C.reduce(o,953/C.triangles(o),planar=False);project(o,minimum=minimum);dest=W/f'body_lod3_direct_{name}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));folder=O/f'body_lod3/direct_{name}';S.render(folder,'body',3,tiers=['a']);v=json.loads(subprocess.run(['/usr/bin/python3',str(P/'scripts/silhouette_metrics.py'),str(O/'body_lod3/reference_final'),str(folder)],capture_output=True,text=True,check=True).stdout);rs=list(v['views'].values());inter=sum(x['iou']*(x['reference_pixels']+x['candidate_pixels'])/(1+x['iou'])for x in rs);pooled=inter/(sum(x['reference_pixels']+x['candidate_pixels']for x in rs)-inter);rows.append({'name':name,'blend':str(dest.relative_to(P)),'triangles':C.triangles(o),'pooled_iou':pooled});print('DIRECT FAR',rows[-1],flush=True)
(O/'far_direct_fit.json').write_text(json.dumps(rows,indent=2))
