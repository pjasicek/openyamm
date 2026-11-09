import sys,json,bpy,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));from round2_reduce import *
curve=json.loads((R/'curve.json').read_text());selected=json.loads((R/'selected.json').read_text())
for part in ['body','bow']:
 for level in range(4):
  for step in range(1,20):
   ob,rig=reset(part);ratio=.9**step;count,protection=reduce(ob,rig,part,level,ratio);tag=f'{part}_l{level}_outline{step:02d}';bpy.ops.wm.save_as_mainfile(filepath=str(W/f'{tag}.blend'));render(ob,rig,part,level,tag)
   result=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/round2_reduction_metrics.py'),str(R),f'{part}_l{level}_s00',tag],text=True));row={'part':part,'lod':level,'step':step,'strategy':'prioritize silhouette over non-joint weight blends','ratio':ratio,'triangles':count,'protected':protection,'projected_diameter_pixels':[800,550,220,88][level],**result,'blend':f'work/round2/{tag}.blend','rig_gates':'pending'if result['pass']else'visual_rejection'};curve.append(row);(R/'curve.json').write_text(json.dumps(curve,indent=2));print('REFINE',part,level,step,count,result['min_iou'],result['min_ssim'],result['pass'],flush=True)
   if not result['pass']:break
   if count<selected[part][str(level)]['triangles']:selected[part][str(level)]=row
  (R/'selected.json').write_text(json.dumps(selected,indent=2))
