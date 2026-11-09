import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.argv=['skirt_sim.py','--',str(p/'work/skirt_rig.blend'),str(p/'work/skirt_animated.blend')]
runpy.run_path(str(p/'scripts/skirt_sim.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/audit_skirt.py'),run_name='__main__')
