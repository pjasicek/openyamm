"""Promote the visually selected mesh without changing the accepted rig, actions or texture domains."""
import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];step=json.loads((P/'review/reduction/selection.json').read_text())['selected_step']
bpy.ops.wm.open_mainfile(filepath=str(P/'revisions/accepted_v2/work/textured_master.blend'));body=bpy.data.objects['Body']
original_objects=set(bpy.data.objects);original_actions=set(bpy.data.actions)
with bpy.data.libraries.load(str(P/f'review/reduction/step_{step:02d}.blend'),link=False) as (src,dst):dst.objects=['Body']
reduced=dst.objects[0];assert [g.name for g in body.vertex_groups]==[g.name for g in reduced.vertex_groups]
body.data=reduced.data.copy()
# A library object also imports its parent rig/action; only its mesh belongs in this master.
for o in set(bpy.data.objects)-original_objects:bpy.data.objects.remove(o,do_unlink=True)
for a in set(bpy.data.actions)-original_actions:bpy.data.actions.remove(a)
assert len(body.data.materials)==3
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'))
