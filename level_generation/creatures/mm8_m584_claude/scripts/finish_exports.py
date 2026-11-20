from pathlib import Path
import runpy
P=Path(__file__).resolve().parents[1]
for name in ['review_heads.py','export_parity.py','review_textured_motion.py','lods.py']:
 runpy.run_path(str(P/'scripts'/name),run_name='__main__')
