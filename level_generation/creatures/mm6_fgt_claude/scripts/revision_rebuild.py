from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for script in ["revision_body.py","revision_mace.py","revision_head_clearance.py","revision_gates.py"]:runpy.run_path(str(p/script),run_name="__main__")
