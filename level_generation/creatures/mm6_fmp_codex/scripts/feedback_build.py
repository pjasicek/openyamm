import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for n in ['feedback_repair.py','feedback_drape.py','feedback_contacts.py','face_patch.py','feedback_export.py','feedback_face.py']:runpy.run_path(str(p/n),run_name='__main__')
