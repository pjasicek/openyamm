import bpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/lancer_polished.blend'));body=bpy.data.objects['Body'];names=[g.name for g in body.vertex_groups]
positions=[v.co.copy() for v in body.data.vertices];weights=[[(names[e.group],e.weight) for e in v.groups] for v in body.data.vertices]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/forge_stroke_checkpoint.blend'));body=bpy.data.objects['Body']
assert len(positions)==len(body.data.vertices)
assert max((a-v.co).length for a,v in zip(positions,body.data.vertices))<1e-6
# Retain the checkpoint's useful left-shoulder fit; undo the later right-shoulder weight drift.
checkpoint_names=[g.name for g in body.vertex_groups]
checkpoint=[[(checkpoint_names[e.group],e.weight) for e in v.groups] for v in body.data.vertices]
for i,v in enumerate(body.data.vertices):
 k=min(1,max(0,(v.co.x-.02)/.10))
 if k:
  combined={}
  for n,w in weights[i]:combined[n]=combined.get(n,0)+(1-k)*w
  for n,w in checkpoint[i]:combined[n]=combined.get(n,0)+k*w
  weights[i]=[(n,w) for n,w in combined.items() if w>1e-7]
 assert abs(sum(w for _,w in weights[i])-1)<1e-5
body.vertex_groups.clear()
for name in names:body.vertex_groups.new(name=name)
for i,row in enumerate(weights):
 for name,w in row:body.vertex_groups[name].add([i],w,'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/forge_motion.blend'))
