from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
s=p/'scripts/finger_weights.py';sys.argv=[str(s),'--',str(p/'work/rig_v1.blend'),str(p/'work/rig_fingers.blend')];runpy.run_path(str(s),run_name='__main__')
for name in ['fit_body_weights.py','solve_wand_grip.py','join_head.py','retarget_pilots.py','assemble_wand.py','author_pilots.py','finish_pilots.py','fit_pilot_cloth.py','pilot_contacts.py','export_pilot.py']:
 sys.argv=[str(p/'scripts'/name)];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
