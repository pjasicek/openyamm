from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
for view in ['front','left']:
 s=p/'scripts/clip_sheet.py';sys.argv=[str(s),'--',str(p/'work/rig_animated.blend'),str(p/'review/motion_v2'/view),view,'7','Walking','Running','Death'];runpy.run_path(str(s),run_name='__main__')
s=p/'scripts/edge_diagnostic.py';sys.argv=[str(s)];runpy.run_path(str(s),run_name='__main__')
