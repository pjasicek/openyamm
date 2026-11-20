"""MCP entry: focused reference exit views, preserving existing scenes and case-study renders."""
from pathlib import Path
import bpy
root=Path('/home/pjasicek/github/OpenYAMM');previous=bpy.context.scene.name
views={
'out02':[
 dict(id='ravenshore_shadowspire',target=(27000,1000,1400),position=(21500,-7500,12500),scale=19000),
 dict(id='ravenshore_alvar',target=(-3000,27000,400),position=(5500,21000,11500),scale=19000),
 dict(id='ravenshore_garrote',target=(-27000,11000,1400),position=(-21000,19000,12500),scale=19000)],
'out03':[
 dict(id='alvar_murmurwoods',target=(-27000,-4800,1400),position=(-20500,-13000,12500),scale=19000),
 dict(id='alvar_ironsand',target=(27000,-20500,1400),position=(21000,-12500,12500),scale=19000),
 dict(id='alvar_ravenshore',target=(-12500,-27000,500),position=(-4500,-21000,11500),scale=19000)]}
try:
    for stem,study in views.items():
        f=root/'level_generation/scripts/blender_reference_view.py'
        exec(compile(f.read_text(),str(f),'exec'),dict(WORLD='mm8',MAP=stem,KIND='outdoor',REPO=str(root),
            STUDY_VIEWS=study,OUTPUT_DIRECTORY=str(root/'level_generation/evidence/transition_calibration')))
finally:
    if bpy.data.scenes.get(previous):bpy.context.window.scene=bpy.data.scenes[previous]
print('Six native reference exit views saved')
