from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
for side in ['R','L']:
 s=p/'scripts/hand_xray.py';sys.argv=[str(s),'--',str(p/'work/rig_v1.blend'),side,str(p/f'review/hand_fit_{side}')];runpy.run_path(str(s),run_name='__main__')
