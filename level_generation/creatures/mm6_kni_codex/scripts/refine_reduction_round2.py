import bpy,sys,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduce_round2 as red
curve=json.loads((red.R/'reduction_curve.json').read_text())
for level,pixels in enumerate([800,550,220,88]):
 rows=[r for r in curve if r['lod']==level];passed=[r for r in rows if r['pass']];hi=min([r['ratio']for r in passed],default=1.);lo=max(r['ratio']for r in rows if not r['pass'])
 for j in range(3):
  ratio=(hi+lo)/2;body,rig=red.reset(level);prot=red.protect(body,rig,level);count=red.reduce(body,ratio,level);tag=f'body_l{level}_refine{j}';bpy.ops.wm.save_as_mainfile(filepath=str(red.W/f'{tag}.blend'));red.render(body,rig,tag,pixels);m=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/reduction_metrics_round2.py'),str(red.R),f'body_l{level}_reference',tag],text=True));row={'part':'body','lod':level,'step':f'bracket_{j}','ratio':ratio,'triangles':count,'projected_diameter_pixels':pixels,'protection':prot,**m,'blend':f'work/round2/{tag}.blend','reference':f'work/round2/baseline_body_l{level}.glb','rig_gate':'pending'if m['pass']else 'not_run_visual_rejection'};curve.append(row);(red.R/'reduction_curve.json').write_text(json.dumps(curve,indent=2));print('REFINE',level,ratio,count,m['min_iou'],m['min_ssim'],m['pass'],flush=True)
  if m['pass']:hi=ratio
  else:lo=ratio
