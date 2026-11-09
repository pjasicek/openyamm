from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for name in ['verify_export.py','validate_lods.py','scale_review.py']:runpy.run_path(str(p/name),run_name='__main__')
