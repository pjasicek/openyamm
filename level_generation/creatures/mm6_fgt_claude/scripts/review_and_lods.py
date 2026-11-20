from pathlib import Path
import runpy
s=Path(__file__).resolve().parent
for n in ('textured_review.py','build_lods.py'):runpy.run_path(str(s/n),run_name='__main__')
