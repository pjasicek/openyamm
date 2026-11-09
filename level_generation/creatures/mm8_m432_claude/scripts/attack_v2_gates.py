"""The project's half-frame probes (gates.py set without the weight sweep) on Attack v2 and the old Attack (v1) of
work/rig_textured_fit_attack_v2.blend; g6 output goes to work/attack_v2/g6_contacts.json (the assembled-revision
work/g6_contacts.json is restored)."""
import os, runpy, shutil, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]; sys.dont_write_bytecode = True
src = P / 'work/rig_textured_fit_attack_v2.blend'; acts = ['Attack', 'Attack_v1']
keep = P / 'work/g6_contacts.json'; backup = P / 'work/attack_v2/g6_contacts_assembled_backup.json'
shutil.copy(keep, backup)
try:
    for script in ('g5_hand_stretch.py', 'sole_probe.py', 'jerk_probe.py', 'g6_contacts.py'):
        print('RUN', script, flush=True); os.environ['STEP'] = '0.5'
        sys.argv = [script, '--', str(src), *acts]; runpy.run_path(str(P / 'scripts' / script), run_name='__main__')
    shutil.copy(keep, P / 'work/attack_v2/g6_contacts.json')
finally:
    shutil.copy(backup, keep); backup.unlink()
