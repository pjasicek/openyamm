import runpy, sys
from pathlib import Path
P=Path(__file__).resolve().parent
for side in ('L','R'):
    sys.argv=['hand_xray','--',str(P.parent/'work/rig_v1.blend'),side,str(P.parent/f'review/g5_hand_{side}')]
    runpy.run_path(str(P/'hand_xray.py'),run_name='__main__')
