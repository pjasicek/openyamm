import bpy,sys,os,runpy,subprocess,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round3';R=P/'review/round3';sys.path.insert(0,str(P/'scripts'));import silhouette_round3 as red;import pbr_round3 as pbr
rows=json.loads((R/'bake_candidate_probe.json').read_text())
for ratio in [.69,.729,.77]:
 body,rig=red.old.reset(0);prot=red.reduce(body,rig,ratio);tag=f'balanced_{int(ratio*1000)}';bpy.ops.wm.save_as_mainfile(filepath=str(W/f'{tag}.blend'));os.environ['BAKE_INPUT']=f'{tag}.blend'
 runpy.run_path(str(P/'scripts/bake_round3.py'),run_name='__main__');subprocess.check_call(['/usr/bin/python3',str(P/'scripts/tier_maps_round3.py')]);pbr.render('low','a',tag)
 result=json.loads(subprocess.check_output(['/usr/bin/python3','-c',"import sys,json;sys.path.insert(0,sys.argv[1]);from reduction_metrics_round2 import compare;from pathlib import Path;r=Path(sys.argv[2]);print(json.dumps([compare(r/f'pbr_high_a_{i}.png',r/f'{sys.argv[3]}_{i}.png')for i in range(8)]))",str(P/'scripts'),str(R),tag],text=True));row={'tag':tag,'triangles':json.loads((R/'bake.json').read_text())['triangles'],'ratio':ratio,'views':result,'min_iou':min(v['iou']for v in result),'min_ssim':min(v['ssim']for v in result),'protection':prot};row['pass']=row['min_iou']>=.99 and row['min_ssim']>=.95;rows.append(row);(R/'bake_candidate_probe.json').write_text(json.dumps(rows,indent=2));print('FULL CANDIDATE',json.dumps(row),flush=True)
 dest=W/tag;dest.mkdir(exist_ok=True)
 for f in (P/'textures/round3').glob('*.png'):shutil.copy2(f,dest/f.name)
 for f in ['rebaked_l0.blend','geometry_body_l0.glb']:shutil.copy2(W/f,dest/f)
 if row['pass']:
  (R/'selected_l0.json').write_text(json.dumps(row,indent=2));break
else:raise RuntimeError('No candidate met all eight-view thresholds')
# Remaining two tier sets; high A and the selected low A are already rendered.
for tier in 'bc':
 for variant in ['high','low']:pbr.render(variant,tier,f'pbr_{variant}_{tier}')
for i in range(8):shutil.copy2(R/f'{tag}_{i}.png',R/f'pbr_low_a_{i}.png')
runpy.run_path(str(P/'scripts/gates_l0_round3.py'),run_name='__main__')
