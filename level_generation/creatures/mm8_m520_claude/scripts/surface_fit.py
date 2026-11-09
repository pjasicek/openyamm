"""Fit rigid boot soles and neck ornaments once on the selected mesh."""
import numpy as np
def apply(body):
 me=body.data
 if me.get('cyclops_surface_fit'):return
 co=np.array([v.co[:] for v in me.vertices]);pv=np.array([v.value for v in me.attributes['piece'].data])
 ids=np.flatnonzero((pv==1)&(co[:,2]<.065));z=co[ids,2];t=np.clip((.065-z)/.030,0,1);co[ids,2]+=(.008-z)*t
 for piece in [6,7,8]:co[pv==piece,1]-=.035
 for piece in [3,4,5]:
  ids=np.flatnonzero(pv==piece);zz=co[ids,2];t=np.clip((zz.max()-zz)/max(zz.max()-zz.min(),1e-6),0,1);co[ids,1]-=.035*t
 for v,c in zip(me.vertices,co):v.co=c
 for side in 'LR':
  toe=body.vertex_groups[f'B_{side}_Toe0'];foot=body.vertex_groups[f'B_{side}_Foot']
  for v in me.vertices:
   w=sum(g.weight for g in v.groups if g.group==toe.index)
   if w:foot.add([v.index],w,'ADD');toe.remove([v.index])
 for side,sign in [('L',1),('R',-1)]:
  foot=body.vertex_groups[f'B_{side}_Foot']
  for v in me.vertices:
   if pv[v.index]==1 and co[v.index,2]<.04 and sign*co[v.index,0]>0:
    for g in body.vertex_groups:g.remove([v.index])
    foot.add([v.index],1,'REPLACE')
 me['cyclops_surface_fit']=True
