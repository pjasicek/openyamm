import bpy,sys,json,math,subprocess
from pathlib import Path
from collections import Counter
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C,search_reduction as S
W=P/'work/reduction';O=P/'review/reduction';path=W/'body_lod3_direct_near_soft.blend'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction_master.blend'));m=bpy.data.objects['Body'].data;pv=[x.value for x in m.attributes['piece'].data];co=[v.co.copy()for v in m.vertices];trees={}
for pid in set(pv):
 faces=[tuple(f.vertices)for f in m.polygons if Counter(pv[i]for i in f.vertices).most_common(1)[0][0]==pid];trees[pid]=BVHTree.FromPolygons(co,faces)
rows=[]
for radius in [.001,.002,.003,.004,.005,.006]:
 bpy.ops.wm.open_mainfile(filepath=str(path));C.reset();o=bpy.data.objects['Body'];pv=[x.value for x in o.data.attributes['piece'].data]
 for v,pid in zip(o.data.vertices,pv):
  if v.co.z<.016:continue
  amount=radius*({0:.4,6:.4,7:.4,3:.15,4:.15}.get(pid,1)if pid in [0,1,2,3,4,6,7,8,9,11]else 0);loc,n,fi,d=trees[pid].find_nearest(v.co);v.co+=n*amount
 o.data.update();dest=W/f'body_lod3_direct_fit_{int(radius*1000)}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));folder=O/f'body_lod3/direct_fit_{int(radius*1000)}';S.render(folder,'body',3,tiers=['a']);v=json.loads(subprocess.run(['/usr/bin/python3',str(P/'scripts/silhouette_metrics.py'),str(O/'body_lod3/reference_final'),str(folder)],capture_output=True,text=True,check=True).stdout);rs=list(v['views'].values());inter=sum(x['iou']*(x['reference_pixels']+x['candidate_pixels'])/(1+x['iou'])for x in rs);pooled=inter/(sum(x['reference_pixels']+x['candidate_pixels']for x in rs)-inter);rows.append({'radius_m':radius,'blend':str(dest.relative_to(P)),'pooled_iou':pooled});print('FAR FIT',radius,pooled,flush=True)
(O/'far_direct_shape_fit.json').write_text(json.dumps(rows,indent=2))
