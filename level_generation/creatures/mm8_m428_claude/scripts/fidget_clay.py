"""Clay Fidget sheet with the review dagger (front and left, 6 frames) from work/rig_sim.blend."""
import runpy, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]
for view in ('front', 'left'):
    sys.argv = ['clip_sheet.py', '--', str(P / 'work/rig_sim.blend'), str(P / f'review/fidget_{view}'), view, 6, 'Fidget']
    runpy.run_path(str(P / 'scripts/clip_sheet.py'), run_name='__main__')
