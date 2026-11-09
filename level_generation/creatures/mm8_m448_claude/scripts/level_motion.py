from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
sys.argv=['foot_level','--',str(p/'work/motion_grip.blend'),str(p/'work/motion_level.blend'),'Standing','Walking:const','Running:const','Attack','Hit','Fidget','Death:until=6']
runpy.run_path(str(p/'scripts/foot_level.py'),run_name='__main__')
