"""Verify authoring textures and render the existing LOD comparison with refreshed colours."""
import bpy
import json
import os
from pathlib import Path
import runpy
import sys

P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/rig_export.blend'))
images = []
for image in bpy.data.images:
    if not image.name.startswith('gloamer_'):
        continue
    path = Path(bpy.path.abspath(image.filepath))
    assert path.is_file() and not image.packed_file, image.name
    image.reload()
    images.append(str(path.relative_to(P)))
assert len(images) >= 9
(P / 'review/colour_fix/authoring.json').write_text(json.dumps({'external_maps': images}, indent=2) + '\n')
sys.argv = ['lod_render.py', '--', str(P / 'review/colour_fix/lods'), 'hes_gloamer']
runpy.run_path(str(P.parent / 'lod_repair_claude/scripts/lod_render.py'), run_name='__main__')
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
