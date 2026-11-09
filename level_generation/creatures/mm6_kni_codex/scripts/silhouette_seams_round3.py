import bpy,sys,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round3';R=P/'review/round3';sys.path.insert(0,str(P/'scripts'));import reduce_round2 as old
old.R=R;curve=json.loads((R/'silhouette_curve.json').read_text());h=curve[0]['body_standing_height_m'];pixels=2.1778047/h*700
for step in range(3,17):
 body,rig=old.reset(0);prot=old.protect(body,rig,0);ratio=.9**step;count=old.reduce(body,ratio,0);tag=f'seams_s{step:02d}';rig.animation_data.action=None
 for bone in rig.pose.bones:bone.matrix_basis.identity()
 bpy.ops.wm.save_as_mainfile(filepath=str(W/f'{tag}.blend'));old.render(body,rig,tag,pixels)
 metrics=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/reduction_metrics_round2.py'),str(R),'high_silhouette',tag],text=True));row={'tag':tag,'ratio':ratio,'triangles':count,'min_iou':metrics['min_iou'],'views':[x['iou']for x in metrics['views']],'silhouette_pass':metrics['min_iou']>=.99,'actor_height_px':700,'body_standing_height_m':h,'protection':prot,'blend':f'work/round3/{tag}.blend','method':'retained seam geometry; rebake planned'};curve.append(row);(R/'silhouette_curve.json').write_text(json.dumps(curve,indent=2));print('SILHOUETTE',tag,count,row['min_iou'],flush=True)
 if not row['silhouette_pass']:break
