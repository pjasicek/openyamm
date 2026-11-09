from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for n in ['build_actions.py','ground_and_review.py']:runpy.run_path(str(p/n),run_name='__main__')
