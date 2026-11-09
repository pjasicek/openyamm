import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['apply_final_grip','final_visual_attack','final_sheets']:runpy.run_path(str(P/'scripts'/f'{name}.py'),run_name='__main__')
