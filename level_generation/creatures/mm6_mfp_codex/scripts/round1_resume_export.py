import bpy,sys,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
roles=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
for level in range(1,4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/round1/lod{level}.blend'));r=bpy.data.objects['Rig'];r.animation_data.action=None
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 with bpy.data.libraries.load(str(P/'work/round1/lod0.blend'),link=False)as(src,dst):dst.actions=list(roles)
 for a in dst.actions:a.use_fake_user=True
 r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];bpy.context.scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/round1/lod{level}.blend'))

for name in ['round1_export','round1_gate_regions']:runpy.run_path(str(P/'scripts'/(name+'.py')),run_name='__main__')
