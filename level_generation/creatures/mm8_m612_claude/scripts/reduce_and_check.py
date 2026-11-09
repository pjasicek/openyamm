import runpy,os,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
assert not any(json.loads((P/'work/contacts.json').read_text()).values())
runpy.run_path(str(P/'scripts/finish_rig.py'),run_name='__main__')
os.environ.update(INSPECT_BLEND='rig_final.blend',INSPECT_REPORT='deformation_final.json',CONTACT_BLEND='rig_final.blend',CONTACT_REPORT='contacts_final.json')
for name in ('inspect_animation.py','contacts.py'):
 runpy.run_path(str(P/'scripts'/name),run_name='__main__')
assert not any(json.loads((P/'work/contacts_final.json').read_text()).values())
