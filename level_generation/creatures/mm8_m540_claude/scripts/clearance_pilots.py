from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parent
for name in ['fit_body_weights.py','join_head.py','retarget_pilots.py','assemble_wand.py','author_pilots.py','finish_pilots.py','fit_pilot_cloth.py','pilot_contacts.py','export_pilot.py']:
 sys.argv=[str(p/name)]
 runpy.run_path(str(p/name),run_name='__main__')
