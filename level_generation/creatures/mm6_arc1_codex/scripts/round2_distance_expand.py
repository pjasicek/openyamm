import bpy,sys,json,subprocess
from pathlib import Path
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from round2_reduce import render
D=P/'review/round2/reduction';rows=[]
for offset in [.002,.004,.006,.008,.010,.012]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/body_l3_factor0.blend'));ob=bpy.data.objects['Body'];rig=bpy.data.objects['Rig']
 for v in ob.data.vertices:
  if v.co.z>.03:v.co+=v.normal*offset
 tag=f'body_l3_expand{round(offset*1000)}';path=P/f'work/round2/{tag}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));render(ob,rig,'body',3,tag,P/'work/round2/metric_tiers/baked/arc1_a')
 result=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/round2_reduction_metrics.py'),str(D),'body_l3_arc1_a_high',tag],text=True));row={'part':'body','lod':3,'triangles':603,'offset_m':offset,'blend':str(path.relative_to(P)),**result};rows.append(row);(D/'distance_expansion.json').write_text(json.dumps(rows,indent=2));print('EXPAND',offset,result['pooled_iou'],flush=True)
