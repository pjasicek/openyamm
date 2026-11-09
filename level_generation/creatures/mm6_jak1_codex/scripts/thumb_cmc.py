"""Give the thumb its missing carpometacarpal segment inside the palm, using the measured wrist and thumb branch."""
import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
BASE=json.loads((P/'review/round2/before/work/finger_joints.json').read_text())
def repair_thumbs(body,rig):
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');points={};out=json.loads(json.dumps(BASE))
 for sd in 'LR':
  ns=['B_R_Finger0','B_R_Finger0.001','B_R_Finger0.002']if sd=='R'else['B_L_Finger0','B_L_Finger01','B_L_Finger02'];w=rig.data.edit_bones[f'B_{sd}_Hand'].head.copy();base=Vector(BASE[sd][ns[0]]);mid=Vector(BASE[sd][ns[1]]);tip=Vector(BASE[sd][ns[-1]+'_tip']);pts=[w.lerp(base,.30),base,mid,tip];points[sd]=(ns,pts)
  for n,pt in zip(ns,pts):
   eb=rig.data.edit_bones[n];delta=pt-eb.head;eb.head+=delta;eb.tail+=delta;out[sd][n]=list(pt)
 bpy.ops.object.mode_set(mode='OBJECT')
 names={g.index:g.name for g in body.vertex_groups};labels=[x.value for x in body.data.attributes['finger'].data];weights={v.index:{g.group:g.weight for g in v.groups}for v in body.data.vertices};adj={v.index:[]for v in body.data.vertices}
 for e in body.data.edges:
  a,b=e.vertices;adj[a].append(b);adj[b].append(a)
 original=body.data.get('thumb_weight_original')
 if original:
  for i,row in json.loads(original).items():weights[int(i)]={int(g):w for g,w in row.items()}
 else:
  band={i for i,x in enumerate(labels)if x==1}
  for _ in range(2):band|={j for i in band for j in adj[i]if labels[j]in(0,1)}
  body.data['thumb_weight_original']=json.dumps({i:weights[i]for i in band})
 for sd,(ns,pts) in points.items():
  groups=[body.vertex_groups[n].index for n in ns];hg=body.vertex_groups[f'B_{sd}_Hand'].index;selected=set()
  for v in body.data.vertices:
   if labels[v.index]!=1 or v.co.x*(1 if sd=='L'else-1)<0:continue
   best=None
   for k,(a,b) in enumerate(zip(pts[:-1],pts[1:])):
    u=b-a;t=max(0,min(1,(v.co-a).dot(u)/u.length_squared));d=(v.co-(a+u*t)).length
    if best is None or d<best[0]:best=(d,k,t)
   _,k,t=best;total=sum(x for g,x in weights[v.index].items()if g==hg or names[g].startswith(f'B_{sd}_Finger0'))
   row={g:x for g,x in weights[v.index].items()if g!=hg and not names[g].startswith(f'B_{sd}_Finger0')}
   row[groups[k]]=total
   if k<2 and t>.70:
    blend=(t-.70)/.60;row[groups[k]]=total*(1-blend);row[groups[k+1]]=total*blend
   weights[v.index]=row;selected.add(v.index)
  # The CMC web joins the palm across mesh edges rather than a rigid one-edge seam.
  band=set(selected)
  for _ in range(2):band|={j for i in band for j in adj[i]if labels[j]in(0,1)}
  for _ in range(3):
   old={i:weights[i].copy()for i in band}
   for i in band:
    if not adj[i]:continue
    row={g:.6*w for g,w in old[i].items()}
    for j in adj[i]:
     for g,w in old.get(j,weights[j]).items():row[g]=row.get(g,0)+.4*w/len(adj[i])
    weights[i]=row
  for i in band:
   row={g:w for g,w in weights[i].items()if w>1e-5};row=dict(sorted(row.items(),key=lambda x:-x[1])[:8]);total=sum(row.values());assert total>0
   for g in body.data.vertices[i].groups[:]:body.vertex_groups[g.group].remove([i])
   for g,w in row.items():body.vertex_groups[g].add([i],w/total,'REPLACE')
 (P/'work/finger_joints.json').write_text(json.dumps(out,indent=2))
