"""Remove leaked arm weights past the palm, preserving the wrist's existing blend."""
def repair_hand_weights(body, rig):
 names={g.index:g.name for g in body.vertex_groups};changed={}
 for side in 'LR':
  wrist=rig.data.bones[f'B_{side}_Hand'].head_local;axis=(rig.data.bones[f'B_{side}_Finger2'].head_local-wrist).normalized();count=0
  for v in body.data.vertices:
   hand={g.group:g.weight for g in v.groups if names[g.group].startswith((f'B_{side}_Hand',f'B_{side}_Finger'))}
   total=sum(hand.values());depth=(v.co-wrist).dot(axis)
   if total<.05 or depth<.02:continue
   # The wrist transition ends inside the palm; every finger follows its own chain.
   blend=min(1,max(0,(depth-.02)/.025));blend=blend*blend*(3-2*blend)
   other={g.group:g.weight for g in v.groups if g.group not in hand};removed=sum(other.values())*blend
   if removed<1e-6:continue
   for group,weight in other.items():
    if blend==1:body.vertex_groups[group].remove([v.index])
    else:body.vertex_groups[group].add([v.index],weight*(1-blend),'REPLACE')
   for group,weight in hand.items():body.vertex_groups[group].add([v.index],weight*(1+removed/total),'REPLACE')
   count+=1
  changed[side]=count
 return changed
