from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1];s=p/'scripts/fit_joints.py'
sys.argv=[str(s),'--',str(p/'work/step1.blend'),'Body'];runpy.run_path(str(s),run_name='__main__')
