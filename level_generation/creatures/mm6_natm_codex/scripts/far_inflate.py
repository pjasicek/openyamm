import bpy,sys,json,subprocess,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
from reduction_render import render
rows=[]
for amount in [.001,.0025,.004,.006]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/lod3_feet.blend'));C.reset();o=bpy.data.objects['Body'];me=o.data;pv=np.array([x.value for x in me.attributes['piece'].data]);gn={g.index:g.name for g in o.vertex_groups}
 for v in me.vertices:
  if pv[v.index]in [1,10]or v.co.z<.14 or any(('Hand'in gn[g.group]or'Finger'in gn[g.group])and g.weight>.2 for g in v.groups):continue
  v.co+=v.normal*amount
 me.update();tag=f'inflate{round(amount*10000)}';dest=P/f'work/lod3_{tag}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));out=P/f'review/reduction/lod3_{tag}';render(dest,out,P/'work/reduction/lod3_continuous',88)
 v=json.loads(subprocess.check_output(['/usr/bin/python3','-B',str(P/'scripts/reduction_metrics.py'),str(P/'review/reduction/lod3_reference'),str(out)],text=True));rr=list(v['views'].values());uu=[(x['reference_pixels']+x['candidate_pixels'])/(1+x['iou'])for x in rr];pooled=sum(x['iou']*u for x,u in zip(rr,uu))/sum(uu);rows.append({'amount_m':amount,'pooled_iou':pooled,'visual':v});(P/'review/reduction/inflate_curve.json').write_text(json.dumps(rows,indent=2));print('INFLATE',amount,pooled,flush=True)
 if pooled>=.971:break
