from pathlib import Path
import os,runpy
p=Path(__file__).resolve().parents[1]
os.environ['MAGE_BLEND']=str(p/'work/rig_reduced.blend');os.environ['MAGE_CHECK_STAGE']='reduced'
runpy.run_path(str(p/'scripts/check_full_actions.py'),run_name='__main__')
