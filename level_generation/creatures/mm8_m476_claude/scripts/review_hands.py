from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
for side in ['L','R']:
    s=p/'scripts/hand_xray.py';sys.argv=[str(s),'--',str(p/'work/rig_v1.blend'),side,str(p/'review'/('hand_'+side))];runpy.run_path(str(s),run_name='__main__')
