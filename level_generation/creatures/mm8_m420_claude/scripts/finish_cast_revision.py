"""Export the current cast and corrected coat weights through every delivered LOD."""
from pathlib import Path
import runpy, subprocess
P = Path(__file__).resolve().parents[1]
runpy.run_path(str(P / 'scripts/export_final_lods.py'), run_name='__main__')
for script in ['finalize_exports.py', 'viewer_tiers.py', 'audit_exports.py']:
    subprocess.run(['python3', str(P / 'scripts' / script)], check=True)
runpy.run_path(str(P / 'scripts/verify_cast_revision.py'), run_name='__main__')
