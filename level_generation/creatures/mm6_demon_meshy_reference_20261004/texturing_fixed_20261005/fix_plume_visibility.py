"""Correct portable effect visibility in the selected master; runtime uses batched particles instead."""
import importlib.util
import shutil
from pathlib import Path

import bpy

STAGE = Path(__file__).resolve().parent
BACKUP = STAGE.parents[3] / 'output/performance/demon_cpu_fix_20261006/before'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


source = STAGE / 'mm6_demon_textured.blend'
BACKUP.mkdir(parents=True, exist_ok=True)
backup = BACKUP / source.name
if not backup.exists():
    shutil.copy2(source, backup)
bpy.ops.wm.open_mainfile(filepath=str(source))
author = module('demon_materials', STAGE / 'author_materials.py')
effects = module('demon_effects', STAGE.parent / 'animations_native_v7_20261005/effects.py')
scene = bpy.data.scenes[author.SCENE]
bpy.context.window.scene = scene
plume = scene.objects['Demon_Death_Plume']
assert not plume.animation_data or not plume.animation_data.nla_tracks, 'Visibility tracks already present'
effects.scale_tracks(plume, 'plume')
for clip in effects.CLIPS:
    for frame in (0, effects.CLIPS[clip] * 0.5, effects.CLIPS[clip]):
        author.select(scene, clip, frame)
        assert tuple(plume.scale) == ((1, 1, 1) if clip == 'Death' else (0, 0, 0))
author.select(scene, 'Standing', 0)
bpy.ops.wm.save_as_mainfile(filepath=str(source))
normalizer = module('demon_export', STAGE.parent / 'animations_native_v7_20261005/normalize_export.py')
normalizer.normalize(STAGE / 'mm6_demon_textured.glb')
print('Portable plume visibility corrected; skin, materials and all other animation curves retained.', flush=True)
