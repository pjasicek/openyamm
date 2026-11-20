import sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.argv=['grip_final.py','--',str(P/'work/rig_polished.blend'),'Attack','12.5'];os.environ.update(GRIP_RENDER=str(P/'review/grip_closed_trial'),GRIP_SCALE='.24');runpy.run_path(str(P/'scripts/grip_final.py'),run_name='__main__')
