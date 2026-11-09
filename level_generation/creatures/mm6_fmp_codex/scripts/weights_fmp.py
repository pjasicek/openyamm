"""Fit sleeve, hand and hidden-leg weights to the corrected skeleton; skirt is rigged separately."""
import bpy,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
# Close the generated sleeve-root openings, which become visible during a run, and two tiny accidental holes.
import bmesh
bm=bmesh.new();bm.from_mesh(me);pl=bm.verts.layers.int['piece'];left={e for e in bm.edges if e.is_boundary}
while left:
 e=left.pop();todo=[e];es={e};vs=set(e.verts)
 while todo:
  e=todo.pop()
  for v in e.verts:
   for x in v.link_edges:
    if x in left:left.remove(x);es.add(x);vs.update(x.verts);todo.append(x)
 parts={v[pl] for v in vs};c=sum((v.co for v in vs),next(iter(vs)).co*0)/len(vs)
 if (parts=={0} and len(es) in (22,23) and 1.22<c.z<1.37) or (parts=={0} and len(es)==3) or (parts=={3} and len(es)==5):
  new=bmesh.ops.holes_fill(bm,edges=list(es),sides=0)['faces'];bmesh.ops.triangulate(bm,faces=new)
  print('CLOSED sleeve/micro hole',parts,len(es))
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
co=np.array([v.co[:] for v in me.vertices]);piece=np.array([v.value for v in me.attributes['piece'].data])
groups={g.name:g for g in body.vertex_groups};J={b.name:np.array(b.head_local) for b in rig.data.bones}
def smooth(t):
 t=float(np.clip(t,0,1));return t*t*(3-2*t)
def mix(a,b,t):
 return {n:a.get(n,0)*(1-t)+b.get(n,0)*t for n in a.keys()|b.keys()}
def trunk(z):
 keys=[(1.075,'B_Pelvis'),(1.14,'B_Spine'),(1.20,'B_Spine1'),(1.285,'B_Spine2'),(1.38,'B_Neck'),(1.445,'B_Head')]
 if z<=keys[0][0]:return {keys[0][1]:1}
 for (a,n),(b,m) in zip(keys,keys[1:]):
  if z<b:return {n:1-smooth((z-a)/(b-a)),m:smooth((z-a)/(b-a))}
 return {'B_Head':1}
def segment(p,a,b):
 d=b-a;return float((p-a)@d/(d@d))
for i,p in enumerate(co):
 part=int(piece[i]);sd='L' if p[0]>-.004 else 'R';pre='B_'+sd+'_'
 if part in (2,3):w={pre+'Hand':1}
 elif part in (1,7):w={'B_Pelvis':1}
 elif part in (5,6):
  if p[2]<.13:w={pre+'Foot':1}
  elif p[2]<.22:w=mix({pre+'Foot':1},{pre+'Calf':1},smooth((p[2]-.13)/.09))
  else:w=mix({pre+'Calf':1},{pre+'Thigh':1},smooth((p[2]-.46)/.10))
 elif part!=0:w={'B_Head':1}
 else:
  w=trunk(p[2])
  sh,el,wr=[J[pre+n] for n in ('UpperArm','Forearm','Hand')]
  t=segment(p,sh,el)
  arm=mix({pre+'UpperArm':1},{pre+'Forearm':1},smooth((t-.82)/.36))
  t2=segment(p,el,wr)
  arm=mix(arm,{pre+'Hand':1},smooth((t2-.88)/.12))
  amount=smooth((abs(p[0]+.004)-.085)/.10)
  if p[2]>1.39:amount=0
  w=mix(w,arm,amount)
 for g in body.vertex_groups:g.remove([i])
 total=sum(w.values());assert total>.999
 for n,v in w.items():
  if v>1e-5:groups[n].add([i],float(v/total),'REPLACE')
assert all(abs(sum(g.weight for g in v.groups)-1)<1e-4 for v in me.vertices)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_weighted.blend'))
print('Fitted all visible surfaces; rigid relaxed hands, head accessories and stable sleeve transitions.')
