"""One Blender process for the current fitted animation revision and raw exports."""
import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['review3_motion','review3_smooth_fit','review2_reload']:
 runpy.run_path(str(P/f'scripts/{name}.py'),run_name='__main__')
