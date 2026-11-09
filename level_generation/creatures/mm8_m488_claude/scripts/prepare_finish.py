from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
for n in ('wrap_motion.py','waist_weights.py'):
 path=p/'scripts'/n;sys.argv=[str(path),'--',str(p/'work/animated_fixed.blend'),str(p/'work/animated_fixed.blend')];runpy.run_path(str(path),run_name='__main__')
path=p/'scripts/check_contacts.py';sys.argv=[str(path),'--',str(p/'work/animated_fixed.blend'),'Running'];runpy.run_path(str(path),run_name='__main__')
path=p/'scripts/inspect_contact.py';sys.argv=[str(path),'--'];runpy.run_path(str(path),run_name='__main__')
