from pathlib import Path
import sys,runpy,json
p=Path(__file__).resolve().parents[1]
poses=json.loads((p/'work/rom.json').read_text())['stress_poses']
frames=[f"{r['role']}:{round(r['frame']*30/24)}" for r in poses]
sys.argv=['g4_weights','--',str(p/'work/motion_grip.blend'),'first',*frames]
runpy.run_path(str(p/'scripts/g4_weights.py'),run_name='__main__')
sys.argv=['g5_hand_stretch','--',str(p/'work/motion_grip.blend'),'Standing','Walking','Running','Attack','Hit','Death','Fidget']
runpy.run_path(str(p/'scripts/g5_hand_stretch.py'),run_name='__main__')
