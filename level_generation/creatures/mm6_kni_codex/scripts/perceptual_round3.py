import bpy,sys,os,runpy,subprocess,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round3';R=P/'review/round3';sys.path.insert(0,str(P/'scripts'));import pbr_round3 as pbr
os.environ['BAKE_INPUT']='body_s04.blend'
runpy.run_path(str(P/'scripts/bake_round3.py'),run_name='__main__');subprocess.check_call(['/usr/bin/python3',str(P/'scripts/tier_maps_round3.py')])
for tier in 'abc':
 for variant in ['high','low']:
  views=[i for i in range(8)if variant=='low'or not(R/f'pbr_high_{tier}_{i}.png').exists()]
  if views:pbr.render(variant,tier,f'pbr_{variant}_{tier}',views=views)
runpy.run_path(str(P/'scripts/gates_l0_round3.py'),run_name='__main__')
