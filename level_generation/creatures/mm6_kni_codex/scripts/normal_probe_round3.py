import bpy,sys,os,runpy,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import pbr_round3 as pbr
os.environ['BAKE_INPUT']='body_s04.blend';os.environ['KEEP_ATLAS']='1';runpy.run_path(str(P/'scripts/bake_round3.py'),run_name='__main__');subprocess.check_call(['/usr/bin/python3',str(P/'scripts/tier_maps_round3.py')]);runpy.run_path(str(P/'scripts/restore_lods_round3.py'),run_name='__main__');runpy.run_path(str(P/'scripts/bake_lod_normals_round3.py'),run_name='__main__');pbr.render('low','a','normal_l1',550,1,views=[0,2])
