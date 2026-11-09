"""Run the assigned nine-item bake after the boot-panel repair and focused lining regression."""
import hashlib
import importlib
import json
from pathlib import Path
import runpy
import sys

project = Path(__file__).resolve().parents[1]
scripts = project / 'scripts'
sys.path.insert(0, str(scripts))
receipt = project / 'review/boot_panel_normals_repair.json'
if receipt.exists():
    current = project / 'work/codex_tex/equipment_7item119.blend'
    assert hashlib.sha256(current.read_bytes()).hexdigest() == json.loads(receipt.read_text())['output_sha256']
else:
    runpy.run_path(str(scripts / 'fix_boot_panel_normals.py'))
runpy.run_path(str(scripts / 'check_mask_bake.py'))
import codex_texture
importlib.reload(codex_texture)
icons = json.loads((project / 'remaining_split.json').read_text())['coordinator_texture_worker']['icons']
assert len(icons) == len(set(icons)) == 9
sys.argv = [str(scripts / 'bake_batch.py'), '--', *['equipment_' + icon for icon in icons]]
runpy.run_path(str(scripts / 'bake_batch.py'))
