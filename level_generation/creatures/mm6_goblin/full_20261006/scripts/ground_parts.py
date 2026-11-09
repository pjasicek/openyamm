import bpy,json
from pathlib import Path
P=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/full_20261006');bpy.ops.wm.open_mainfile(filepath=str(P/'work/native_full_v1.blend'));a=bpy.data.objects['Goblin_Rig'];b=bpy.data.objects['Goblin_Body']
for clip,frames in [('Death',[14,16,19,25]),('Corpse',[1])]:
 act=bpy.data.actions[clip];a.animation_data.action=act;a.animation_data.action_slot=act.slots[0]
 for f in frames:
  bpy.context.scene.frame_set(f);m=b.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
  bad=sorted(m.vertices,key=lambda v:v.co.z)[:6]
  print(clip,f,[(tuple(round(x,3) for x in v.co),[(b.vertex_groups[g.group].name,round(g.weight,2)) for g in b.data.vertices[v.index].groups if b.vertex_groups[g.group].name in a.data.bones]) for v in bad],flush=True)
