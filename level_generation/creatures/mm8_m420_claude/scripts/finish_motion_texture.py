from pathlib import Path
import runpy
P=Path(__file__).resolve().parent
for name in ['build_actions.py','ground_and_review.py','sync_and_texture.py','export_pilot.py']:runpy.run_path(str(P/name),run_name='__main__')
