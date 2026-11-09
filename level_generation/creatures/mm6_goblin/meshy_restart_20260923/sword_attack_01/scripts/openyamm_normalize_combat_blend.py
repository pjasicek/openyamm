import bpy,json
from pathlib import Path
s=bpy.data.scenes['Goblin - Sword and Native Attack'];bpy.context.window.scene=s
for other in list(bpy.data.scenes):
 if other!=s:bpy.data.scenes.remove(other)
s.render.resolution_x=800;s.render.resolution_y=900;s.render.resolution_percentage=100
r=s.objects['Goblin_Combat_Rig'];a=bpy.data.actions['MM6_Goblin_Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];s.frame_start=1;s.frame_end=37;s.frame_set(7)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)
print('Standalone combat project:',len(s.objects),'objects,',len(r.data.bones),'bones,',len(r.animation_data.nla_tracks),'stored clips')
