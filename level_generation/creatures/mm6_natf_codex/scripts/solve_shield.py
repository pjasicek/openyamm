import sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.dont_write_bytecode=True;os.environ['GRIP_RENDER']=str(P/'review/shield_grip')
sys.argv=['shield_grip.py','--','work/rig_adapted.blend','Standing','0'];runpy.run_path(str(P/'scripts/shield_grip.py'),run_name='__main__')
