"""Prepare owned designs and their real geometry variants in one isolated Blender process."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import codex_texture as texture

only = set(sys.argv[sys.argv.index('--') + 1:]) if '--' in sys.argv else set()
for name, entry in texture.DESIGNS.items():
    if only and name not in only:
        continue
    source = Path(texture.MESHY) / f"{entry['geometry_design']}_st_v1/model_urls_glb.glb"
    target = Path(texture.WORK) / f'{name}.blend'
    if not source.exists() or target.exists():
        continue
    texture.prep(name)
