"""Carry the refined actions into the frozen paint geometry and UVs."""
import bpy,json,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_uvprep.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
keep=['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']
with bpy.data.libraries.load(str(p/'work/motion_final.blend'),link=False) as (src,dst):dst.actions=keep.copy()
for a in dst.actions:a.use_fake_user=True
for b in rig.pose.bones:b.matrix_basis.identity()
assert {a.name for a in bpy.data.actions}==set(keep),[a.name for a in bpy.data.actions]
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_uvprep.blend'))
