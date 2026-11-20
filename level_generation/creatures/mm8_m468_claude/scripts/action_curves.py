"""Blender interpolates quaternion components; keep adjacent keys in the same hemisphere."""
def curves(action):
 return [fc for layer in action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
def continuous(action):
 groups={}
 for fc in curves(action):
  if fc.data_path.endswith('rotation_quaternion'):groups.setdefault(fc.data_path,{})[fc.array_index]=fc
 for group in groups.values():
  if len(group)!=4:continue
  keys=[group[i].keyframe_points for i in range(4)];prev=None
  for j in range(min(map(len,keys))):
   q=[k[j].co.y for k in keys]
   if prev is not None and sum(a*b for a,b in zip(q,prev))<0:
    for k in keys:k[j].co.y*=-1;k[j].handle_left.y*=-1;k[j].handle_right.y*=-1
    q=[-v for v in q]
   prev=q
  for fc in group.values():fc.update()
def remove_rotations(action,names):
 paths={f'pose.bones["{n}"].rotation_quaternion' for n in names}
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in list(bag.fcurves):
     if fc.data_path in paths:bag.fcurves.remove(fc)
