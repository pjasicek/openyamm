from pathlib import Path
import sys,runpy,json
p=Path(__file__).resolve().parents[1]
for name in ['fit_fingers','finger_joints','build_rig','hand_frame_check']:
 s=p/f'scripts/{name}.py';sys.argv=[str(s),'--',str(p/'work/rig_v1.blend')];runpy.run_path(str(s),run_name='__main__')
 if name=='fit_fingers':assert set(json.loads((p/'work/fingers_fit.json').read_text()))=={'L','R'}
