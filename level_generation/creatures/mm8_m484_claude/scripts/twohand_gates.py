import os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
os.environ['CHECK_BLEND']='work/gated_master.blend';os.environ['CHECK_PREFIX']='final'
for n in ['fit_twohand.py','finalize_motion.py','check_pilots.py','check_contacts.py','final_motion_gates.py','upperarm_contacts.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
