from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for script in ['polish_motion.py','standing_idle.py','export.py','build_runtime.py','verify_delivery.py','probe_final_export.py']:
    runpy.run_path(str(p/script),run_name='__main__')
