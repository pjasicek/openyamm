from pathlib import Path
import runpy
P=Path(__file__).resolve().parent
for n in ['build_actions.py','sync_and_texture.py','settle_final.py']:runpy.run_path(str(P/n),run_name='__main__')
