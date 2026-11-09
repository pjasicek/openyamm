"""Bake the outdoor automap from the written ODM, with north up and native full-grid UV coverage.

Run through Blender MCP after build_brackenford.py. This is generated presentation art, never terrain geometry.
"""
from pathlib import Path
import json
import bpy
from mathutils import Vector

PROJECT = Path('/home/pjasicek/github/OpenYAMM/level_generation/projects/brackenford_greywatch')
LEVELGEN_REVIEW_VIEWS = []
exec(compile((PROJECT / 'review_brackenford_blender.py').read_text(), 'review_brackenford_blender.py', 'exec'))
del LEVELGEN_REVIEW_VIEWS
for obj in billboards:
    obj.hide_render = True
scene.name = 'Brackenford native automap bake'
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.resolution_percentage = 100
camera.location = Vector((0, 0, 80000)) / 128
camera.rotation_euler = (0, 0, 0)
camera.data.ortho_scale = 65536 / 128
scene.render.image_settings.file_format = 'BMP'
scene.render.image_settings.color_mode = 'RGB'
destination = PROJECT / 'runtime/worlds/mm8/icons/lg01.bmp'
destination.parent.mkdir(parents=True, exist_ok=True)
scene.render.filepath = str(destination)
bpy.ops.render.render(write_still=True)
print(json.dumps(dict(automap=str(destination), bounds=[-32768, -32768, 32768, 32768],
                     pixels=[512, 512], north='up', source='written native ODM terrain and BModels')))
