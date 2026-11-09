import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/full_20261006')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/body_raw_inspection.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');adj=[[] for _ in o.data.vertices]
for e in o.data.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
remaining=set(range(len(adj)));parts=[]
while remaining:
 todo=[remaining.pop()];indices=[]
 while todo:
  i=todo.pop();indices.append(i)
  for j in adj[i]:
   if j in remaining:remaining.remove(j);todo.append(j)
 coords=[o.data.vertices[i].co for i in indices];lo=[min(v[a] for v in coords) for a in range(3)];hi=[max(v[a] for v in coords) for a in range(3)]
 parts.append({'id':len(parts),'vertices':indices,'size':len(indices),'min':lo,'max':hi,'center':[(a+b)/2 for a,b in zip(lo,hi)]})
(P/'review/body_raw/components.json').write_text(json.dumps(parts,indent=2)+'\n')
print(json.dumps([{k:v for k,v in p.items() if k!='vertices'} for p in parts],indent=2))
scene=bpy.context.scene; camera=scene.camera
for name,target,scale,offset in [('head_front',(0,-.05,.385),.27,(0,-1,.1)),('head_right',(0,-.01,.38),.32,(-1,0,.1)),('hands_front',(0,-.02,-.015),.85,(0,-1,.05)),('feet_front',(0,-.03,-.43),.45,(0,-1,.3)),('back_armor',(0,.07,.2),.43,(0,1,0))]:
 target=Vector(target);camera.location=target+Vector(offset);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
 scene.render.filepath=str(P/'review/body_raw'/(name+'.png'));bpy.ops.render.render(write_still=True)
