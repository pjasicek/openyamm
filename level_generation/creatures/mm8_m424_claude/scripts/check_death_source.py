import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for blend in ['rig_carry_twist.blend','rig_gated_candidate.blend']:
    print('COMPARE_JERK',blend,flush=True)
    sys.argv=['jerk_probe.py','--',str(P/'work'/blend),'Hit','Death']
    runpy.run_path(str(P/'scripts/jerk_probe.py'),run_name='__main__')
