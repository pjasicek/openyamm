"""Framed clay and part-labelled views for anatomy review."""
from pathlib import Path
import bpy, sys
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
scene=bpy.context.scene;common.workbench_clay(scene)
common.render_views(str(p/'review/anatomy_full'),.85,2.12,views=('front','left','back','three_quarter'),resolution=(900,1000))
for side,x in [('L',.55),('R',-.55)]:
    common.render_views(str(p/('review/hand_'+side)),.67,.42,views=('front','back','three_quarter'),resolution=(700,700),target=(x,0))
for ob in bpy.data.objects:
    if ob.type=='MESH':
        for mat in ob.data.materials:mat.diffuse_color=(.62,.62,.62,1)
common.render_views(str(p/'review/clay_head'),1.49,.48,views=('front','left','three_quarter'),resolution=(700,700),target=(0,0))
