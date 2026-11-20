import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent/'work'
def run(n,*a):
    sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(P/n),run_name='__main__')
run('weights_fix.py',W/'master_uv_upload.blend',W/'master_weights_clean.blend')
run('contact_fix.py',W/'master_weights_clean.blend',W/'master_contacts.blend')
run('equip_full.py')
run('jerk_probe.py',W/'master_contacts.blend','Death','Hit','Running')
