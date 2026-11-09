"""Copy the Dagger bone's rest placement (head, tail, roll; built by dagger.py from the solved grip) from the authoring
chain (work/rig_sim.blend) into the textured master (work/rig_textured_uv.blend), so a re-solved grip carries over
with the clips (sync_actions.py copies actions only). Idempotent."""
import bpy
from pathlib import Path
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/rig_sim.blend'))
b = bpy.data.objects['Rig'].data.bones['Dagger']
head, tail, z = b.head_local.copy(), b.tail_local.copy(), b.matrix_local.to_3x3().col[2].copy()
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/rig_textured_uv.blend'))
rig = bpy.data.objects['Rig']; bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones['Dagger']; moved = (eb.head - head).length
eb.head, eb.tail = head, tail; eb.align_roll(z)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_mainfile()
print('DAGGERBONE moved mm', round(moved * 1000, 2))
