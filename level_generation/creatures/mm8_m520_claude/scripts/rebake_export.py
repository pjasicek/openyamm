from pathlib import Path
import os,sys,runpy
p=Path(__file__).resolve().parents[1]
os.environ['TWIST_BAKE_ONLY']='1';os.environ['FA']='.65';os.environ['FA_RAMP']='.15,.85'
s=p/'scripts/twist_bones.py';sys.argv=[str(s),'--',str(p/'work/motion_fitted.blend'),str(p/'work/motion_final.blend')];runpy.run_path(str(s),run_name='__main__')
s=p/'scripts/export_review.py';sys.argv=[str(s)];runpy.run_path(str(s),run_name='__main__')
