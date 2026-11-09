"""Inspect the generated crest, skin and unintended torso protrusions before cleanup."""
from pathlib import Path
import sys,json
import bpy,bmesh
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
common.workbench_clay(bpy.context.scene)
for part in ('P00','P01'):
    for obj in bpy.data.objects:
        if obj.type=='MESH':obj.hide_render=obj.name!=part
    common.render_views(str(p/'review'/('detail_'+part)),1.52,.43,views=('front','left','back'),resolution=(600,600))
for obj in bpy.data.objects:
    if obj.type=='MESH':obj.hide_render=obj.name!='P00'
common.render_views(str(p/'review/detail_torso'),1.23,.65,views=('left','back','front'),resolution=(700,700))
mesh=bpy.data.objects['P00'].data
bm=bmesh.new();bm.from_mesh(mesh)
print('SKIN boundary',[[round(x,4) for x in v.co] for v in bm.verts if v.is_boundary])
bm.free()
