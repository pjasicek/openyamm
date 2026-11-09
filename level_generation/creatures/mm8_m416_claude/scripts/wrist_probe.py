from pathlib import Path
import bpy,sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/fingered.blend'));r=bpy.data.objects['Rig']
for n in ['Standing','AimSource','Fidget']:
 a=bpy.data.actions[n];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
 print(n,{s:armik.wrist_cost(r,s,armik.W(r,f'B_{s}_Hand').to_3x3().normalized()) for s in 'RL'})
