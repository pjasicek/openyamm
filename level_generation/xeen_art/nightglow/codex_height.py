"""One codex exec worker for a height map of a Xeen texture, with mat.py's depth-pass prompt (A6, session 14).

usage: python3 codex_height.py <stem> <version>
Reference: refs/<stem>.png (the x4 master, flattened); return: raw/<stem>_height_v<version>.png and .log.
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(ROOT / 'level_generation/surface_materials'))
import mat  # noqa: E402

stem, version = sys.argv[1], sys.argv[2]
master = ROOT / 'assets_source/worlds/xeen/textures_x4' / f'{stem}.png'
ref = HERE / 'refs' / f'{stem}.png'
Image.open(master).convert('RGB').save(ref)
target = HERE / 'raw' / f'{stem}_height_v{version}.png'
prompt = mat.prompt_for('height', 1, None, None)
with open(target.with_suffix('.log'), 'w') as log:
    process = subprocess.run(
        ['codex', 'exec', '--json', '-s', 'workspace-write', '-C', str(HERE), '--skip-git-repo-check', '-i', str(ref)],
        input=mat.WORKER_PROMPT.format(target=target, prompt=prompt), text=True, stdout=log,
        stderr=subprocess.STDOUT, timeout=900)
print(target, process.returncode, target.exists())
