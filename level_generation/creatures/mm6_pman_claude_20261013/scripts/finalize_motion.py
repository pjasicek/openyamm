from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for name in ['build_motion.py','clip_timing.py','fit_clearance.py','reduce_and_upload.py','export_clay.py']:
 runpy.run_path(str(p/name),run_name='__main__')
