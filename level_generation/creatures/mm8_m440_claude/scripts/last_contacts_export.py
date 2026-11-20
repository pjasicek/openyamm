from pathlib import Path
import sys,os,runpy
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
runpy.run_path(str(p/'scripts/last_contacts.py'),run_name='__main__')
os.environ['TWIST_POSES_ONLY']='1';os.environ['TWIST_ACTIONS']='Running,Death';os.environ['FA']='.6'
sys.argv=['twist','--',str(p/'work/full_repaired.blend'),str(p/'work/full_repaired.blend')];runpy.run_path(str(p/'scripts/twist_bones.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/export_full.py'),run_name='__main__')
