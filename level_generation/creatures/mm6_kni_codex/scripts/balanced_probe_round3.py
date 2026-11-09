import bpy,sys,os,runpy,subprocess,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round3';R=P/'review/round3';sys.path.insert(0,str(P/'scripts'));import silhouette_hard_round3 as hard;import pbr_round3 as pbr
rows=json.loads((R/'bake_candidate_probe.json').read_text())
for tag in ['seams_s04','body_s04','seams_s03','body_s02']:
 ratio=0;prot={};os.environ['BAKE_INPUT']=f'{tag}.blend'
 runpy.run_path(str(P/'scripts/bake_round3.py'),run_name='__main__');subprocess.check_call(['/usr/bin/python3',str(P/'scripts/tier_maps_round3.py')]);pbr.render('low','a',tag,views=[0,1])
 result=json.loads(subprocess.check_output(['/usr/bin/python3','-c',"import sys,json;sys.path.insert(0,sys.argv[1]);from reduction_metrics_round2 import compare;from pathlib import Path;r=Path(sys.argv[2]);print(json.dumps([compare(r/f'pbr_high_a_{i}.png',r/f'{sys.argv[3]}_{i}.png')for i in [0,1]]))",str(P/'scripts'),str(R),tag],text=True));row={'tag':tag,'triangles':json.loads((R/'bake.json').read_text())['triangles'],'ratio':ratio,'views':result,'protection':prot};rows.append(row);(R/'bake_candidate_probe.json').write_text(json.dumps(rows,indent=2));print('CANDIDATE',json.dumps(row),flush=True)
 dest=W/tag;dest.mkdir(exist_ok=True)
 for f in (P/'textures/round3').glob('*.png'):shutil.copy2(f,dest/f.name)
 for f in ['rebaked_l0.blend','geometry_body_l0.glb']:shutil.copy2(W/f,dest/f)
 if min(v['ssim']for v in result)>=.95:break
