"""Remove the unused combat action from the selected civilian masters."""
from pathlib import Path
import bpy
p = Path(__file__).resolve().parents[1]
for name in ('rig_textured_uv.blend', 'm436_textured_master.blend'):
    path = p / 'work' / name
    bpy.ops.wm.open_mainfile(filepath=str(path))
    attack = bpy.data.actions.get('Attack')
    if attack is not None:
        bpy.data.actions.remove(attack)
    assert {a.name for a in bpy.data.actions} == {'Standing', 'Walking', 'Running', 'Hit', 'Death', 'Dead', 'Fidget'}
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
