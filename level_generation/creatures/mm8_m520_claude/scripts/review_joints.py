from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1];s=p/'scripts/joint_xray.py'
sys.argv=[str(s),'--',str(p/'work/step1.blend'),'Body',str(p/'work/joints_final.json'),str(p/'review/joints'),str(p/'work/meshy_joints.json')];runpy.run_path(str(s),run_name='__main__')
