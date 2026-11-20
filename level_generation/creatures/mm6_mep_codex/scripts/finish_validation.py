import runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/repair_review_actions.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/complete_visual_validation.py'),run_name='__main__')
