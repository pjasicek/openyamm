from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parent
for n in ['export_physics.py','physical_stride.py']:runpy.run_path(str(P/n),run_name='__main__')
sys.argv=['jerk_probe.py','--',str(P.parent/'work/source_motion.blend'),'AttackSource','HitSource','Death'];runpy.run_path(str(P/'jerk_probe.py'),run_name='__main__')
