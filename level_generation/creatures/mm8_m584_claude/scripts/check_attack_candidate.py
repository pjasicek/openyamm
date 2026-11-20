from pathlib import Path
import os,runpy,json
P=Path(__file__).resolve().parents[1]
os.environ.update(INSPECT_BLEND='attack_revision_1/candidate.blend',INSPECT_REPORT='attack_revision_1/deformation.json',RAVEN_CHECK_CLIP='Attack',RAVEN_CONTACT_BLEND='attack_revision_1/candidate.blend',RAVEN_CONTACT_REPORT=str(P/'work/attack_revision_1/contacts.json'))
runpy.run_path(str(P/'scripts/inspect_animation.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/contacts.py'),run_name='__main__')

contact=json.loads((P/'work/attack_revision_1/contacts.json').read_text())['Attack']
deform=json.loads((P/'work/attack_revision_1/deformation.json').read_text())['Attack']
assert not contact['contacts'],contact
assert min(contact['floor_min'].values())>0,contact
assert deform['arm']['p99']<2.05 and deform['hand']['worst']['max']<2.35,deform
