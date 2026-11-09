import sys,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from rebake_render import render
from rebake_reduce import build
subprocess.run(['/usr/bin/python3',str(P/'scripts/rebake_tiers.py'),'reference','near70final'],check=True)
path=P/'work/rebake/near70final_baked.blend';report={}
for tier in ['lzd_a','lzd_b','lzd_c']:
 ref='reference_'+tier;tag='near70final_'+tier
 render(path,ref,0,True,parts=['body'],palette=('reference',tier));render(path,tag,0,parts=['body'],palette=('near70final',tier))
 r=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/rebake_measure.py'),tag,'0','8','body',ref],text=True));report[tier]=r;print('ACTUAL_TIER',tier,r['body']['min_iou'],r['body']['min_ssim'],flush=True)
(P/'review/rebake/actual_tiers.json').write_text(json.dumps(report,indent=2))
# The bow and head masks have zero red coverage, so their tier colours are identical.
path=build('bow80_boundary',.7,0,.8);render(path,'bow80_boundary',0,parts=['bow'])
r=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/rebake_measure.py'),'bow80_boundary','0','8','bow'],text=True));(P/'review/rebake/bow80_boundary_geometry_metrics.json').write_text(json.dumps(r,indent=2));print('BOW_BOUNDARY',r['bow']['min_iou'],flush=True)
