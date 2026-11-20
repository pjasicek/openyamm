"""Replace the first twist-weight experiment with smooth axial bands and a stable bracer section."""
import bpy
from mathutils import Vector
s=bpy.data.scenes['Goblin Arm Rig Revision'];bpy.context.window.scene=s
rig=bpy.data.objects['Goblin Arm Revision Rig'];body=bpy.data.objects['Goblin Arm Revision Body']
source_scene=bpy.data.scenes.get('Meshy Goblin Sword and Native Attack')
if source_scene is None:
 from pathlib import Path
 original=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_sword_attack/goblin_sword.blend')
 with bpy.data.libraries.load(str(original),link=False) as (src,dst):
  dst.scenes=['Meshy Goblin Sword and Native Attack']
 source_scene=dst.scenes[0]
source=next(o for o in source_scene.objects if o.type=='MESH' and o.data.shape_keys)
assert len(source.data.vertices)==len(body.data.vertices)
source_names={g.index:g.name for g in source.vertex_groups}
weights=[{source_names[g.group]:g.weight for g in v.groups} for v in source.data.vertices]
for group in list(body.vertex_groups):body.vertex_groups.remove(group)
all_names=list(source_names.values())+[f'ForearmRoll{tag}.{side}' for side in ['R','L'] for tag in ['Base','Mid']]
groups={name:body.vertex_groups.new(name=name) for name in all_names}
def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
for vertex,old in zip(body.data.vertices,weights):
 new=old.copy();pos=body.matrix_world@vertex.co
 for side,label in [('Right','R'),('Left','L')]:
  name='mixamorig:'+side+'ForeArm';weight=old.get(name,0)
  arm_weight=sum(old.get('mixamorig:'+side+part,0) for part in ['Arm','ForeArm','Hand','HandMiddle4'])
  if arm_weight<.1:continue
  bone=rig.data.bones[name];axis=(bone.tail_local-bone.head_local).normalized();t=(pos-bone.head_local).dot(axis)/bone.length
  b,m,f=0,0,0
  if t<.24:b=1-smooth((t-.06)/.18);m=1-b
  elif t>.85:f=smooth((t-.85)/.15);m=1-f
  else:m=1
  new.pop(name,None)
  for n,w in [(f'ForearmRollBase.{label}',weight*b),(f'ForearmRollMid.{label}',weight*m),(name,weight*f)]:
   if w>1e-7:new[n]=new.get(n,0)+w
  # Blend the bracer toward the full forearm transform, including hand/elbow influence inherited from auto weights.
  rigid=smooth((t+.05)/.10)*(1-smooth((t-.99)/.10))*smooth((arm_weight-.2)/.5)
  if rigid>0:
   new={n:w*(1-rigid) for n,w in new.items()}
   n=name;new[n]=new.get(n,0)+rigid
 ordered=sorted(new.items(),key=lambda x:x[1],reverse=True)[:4];total=sum(w for n,w in ordered)
 for name,w in ordered:
  if w>1e-7:groups[name].add([vertex.index],w/total,'REPLACE')
print('Restored original weights, then applied continuous twist bands and rigid bracer weighting')
