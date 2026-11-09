import os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/check_export60.py'),run_name='__main__')
os.environ.update(GOG_CHECK_CLIP='Hit',INSPECT_BLEND='rig_final.blend',CONTACT_BLEND='rig_final.blend',
    INSPECT_REPORT='deformation_hit_final.json',CONTACT_REPORT='contacts_hit_final.json')
for name in ('inspect_animation.py','contacts.py','export_textured.py'):
    runpy.run_path(str(P/'scripts'/name),run_name='__main__')
