import bpy,sys,os,runpy,subprocess,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round3';R=P/'review/round3';sys.path.insert(0,str(P/'scripts'));import pbr_round3 as pbr
os.environ['BAKE_INPUT']='body_s04.blend';os.environ['KEEP_ATLAS']='1';runpy.run_path(str(P/'scripts/bake_round3.py'),run_name='__main__');subprocess.check_call(['/usr/bin/python3',str(P/'scripts/tier_maps_round3.py')]);pbr.render('low','a','chart_l0',views=[0,7]);pbr.render('low','a','chart_l1',550,1,views=[0,2])
