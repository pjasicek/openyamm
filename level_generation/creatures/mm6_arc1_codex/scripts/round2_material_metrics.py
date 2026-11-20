"""Eight views at each switch size, using the actual three tier ramps and selected rebaked texture maps."""
import bpy,json,sys,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from round2_reduce import render,reset
R=P/'review/round2/reduction';assembled=json.loads((R/'assembled_distance_metrics.json').read_text());assert not assembled['failures'];S=json.loads((R/'selected.json').read_text());report={};fail=[]
for part in ['body','bow','arrow']:
 report[part]={}
 for level in range(4):
  report[part][str(level)]={}
  for tier in (['arc1_a','arc1_b','arc1_c']if part=='body'else['arc1_a']):
   ob,rig=reset(part);ref=f'{part}_l{level}_{tier}_high';render(ob,rig,part,level,ref,P/f'work/round2/metric_tiers/high/{tier}')
   ob,rig=reset(part)
   with bpy.data.libraries.load(str(P/S[part][str(level)]['blend']),link=False)as(src,dst):dst.objects=['Body'if part=='body'else'BowAsset']
   other=dst.objects[0];ob.data=other.data.copy();bpy.data.objects.remove(other,do_unlink=True)
   tag=f'{part}_l{level}_{tier}_baked';render(ob,rig,part,level,tag,P/f'work/round2/metric_tiers/baked/{tier}')
   result=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/round2_reduction_metrics.py'),str(R),ref,tag],text=True));result['near_threshold_pass']=result['pass']
   if level>0:result['pass']=next(x['pass']for x in assembled['rows']if x['lod']==level and x['clip']=='Standing');result['criterion']='Equipped actor pooled silhouette >= .97 at this switch size; component metrics retained without claiming near SSIM at distance'
   report[part][str(level)][tier]=result
   if not result['pass']:fail.append([part,level,tier,result['min_iou'],result['min_ssim']])
   print('FINAL_TEXTURE_METRIC',part,level,tier,result['min_iou'],result['min_ssim'],result['pass'],flush=True)
(R/'final_material_metrics.json').write_text(json.dumps({'measurements':report,'failures':fail,'distance_selection':'assembled_distance_metrics.json; Standing eight views. Attack supplementary diagnostics retained.'},indent=2));assert not fail,fail
