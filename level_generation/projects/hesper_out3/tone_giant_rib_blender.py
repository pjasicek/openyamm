"""The causeway's giant ribs toned to a darker, stained bone (the integrator's review of build01: the ivory read as
untextured white at a distance): hes_giant_rib's base colour darkened and stained toward the marsh's olive-brown.
The untoned bake is kept as hes_giant_rib_export_untoned.glb and is the input of every run, so a re-bake is toned again
by running this after it.

    blender --background --factory-startup --python level_generation/projects/hesper_out3/tone_giant_rib_blender.py
"""
import shutil
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'level_generation/props/hesper_decorations/work/codex_tex'
export, untoned = WORK / 'hes_giant_rib_export.glb', WORK / 'hes_giant_rib_export_untoned.glb'
if not untoned.exists() or untoned.stat().st_mtime < export.stat().st_mtime - 60:
    shutil.copy2(export, untoned)                   # a fresh bake: keep it as the untoned source
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(untoned))
STAIN = np.array([0.62, 0.55, 0.42], dtype=np.float32)        # olive-brown marsh stain
for image in bpy.data.images:
    if 'basecolor' not in image.name.lower() and 'base' not in image.name.lower():
        continue
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape(-1, 4)
    pixels[:, :3] = pixels[:, :3] * 0.62 * (0.55 + 0.45 * STAIN)
    image.pixels.foreach_set(pixels.ravel())
    image.pack()
    print('TONED', image.name)
bpy.ops.export_scene.gltf(filepath=str(export), export_format='GLB')
