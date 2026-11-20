import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['calibrate_props.py','contact_audit.py','material_review.py','audit_rig_stage.py']:
 runpy.run_path(str(P/'scripts'/name),run_name='__main__')
