import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for n in ['settle_cloth_motion.py','ground_textured.py','finish_contacts.py','export_model.py','verify_export.py']:runpy.run_path(str(p/n),run_name='__main__')
