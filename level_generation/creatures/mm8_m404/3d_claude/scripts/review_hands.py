import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for side in ('L','R'):
 sys.argv=['hand_xray.py','--',str(p/'work/rig_v1.blend'),side,str(p/('review/g3_hand_'+side))]
 runpy.run_path(str(p/'scripts/hand_xray.py'),run_name='__main__')
