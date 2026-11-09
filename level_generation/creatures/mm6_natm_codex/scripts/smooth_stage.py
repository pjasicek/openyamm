import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['settle_motion.py','refine_spear_motion.py','contact_audit.py','material_review.py','motion_pose_audit.py','motion_steps.py']:
 runpy.run_path(str(P/'scripts'/name),run_name='__main__')
