from pathlib import Path
import os,sys,runpy
p=Path(__file__).resolve().parents[1]
os.environ['MAGE_BLEND']=str(p/'work/rig_uv.blend');os.environ['MAGE_CHECK_STAGE']='runtime'
runpy.run_path(str(p/'scripts/check_full_actions.py'),run_name='__main__')
sys.argv=['stride.py','--',str(p/'work/rig_uv.blend'),'Walking','Running'];runpy.run_path(str(p/'scripts/stride.py'),run_name='__main__')
