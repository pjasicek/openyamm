import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'review/round2/baseline/work/rig_equipped.blend'));r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];prop=bpy.data.objects['BowAsset'];sc=bpy.context.scene;g=Matrix(json.loads((P/'work/round2_bow_binding.json').read_text())['hand_local'])
names={g.index:g.name for g in body.vertex_groups};keep=[sum(g.weight for g in v.groups if 'Hand'in names[g.group]or'Finger'in names[g.group])<=.5 for v in body.data.vertices];faces=[tuple(f.vertices)for f in body.data.polygons if all(keep[i]for i in f.vertices)]
inv=r.data.bones['Bow'].matrix_local.inverted();local=[g@inv@v.co for v in prop.data.vertices if any(prop.vertex_groups[g.group].name=='Bow'and g.weight>.9 for g in v.groups)][::2]
cache=[]
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
for clip,lead,tail in [('Attack',12,11),('Hit',5,6),('Death',7,0)]:
 a=bpy.data.actions[clip];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];nf=int(a.frame_range[1])
 for f in np.arange(0,nf+.01,.5):
  if f>lead+1 and (not tail or f<nf-tail-1):continue
  sc.frame_set(int(f),subframe=f-int(f));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=[x.co.copy()for x in me.vertices];ev.to_mesh_clear();tree=BVHTree.FromPolygons(v,faces);h=r.pose.bones['B_L_Hand'];base=h.parent.matrix@h.parent.bone.matrix_local.inverted()@h.bone.matrix_local
  cache.append((clip,float(f),tree,base.to_3x3(),h.head.copy(),h.rotation_quaternion.copy(),smooth(f/lead)*(smooth((nf-f)/tail)if tail else 1)))
a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(0);h=r.pose.bones['B_L_Hand'];restbase=(h.parent.matrix@h.parent.bone.matrix_local.inverted()@h.bone.matrix_local).to_3x3()
results=[]
for angle in range(145,216,5):
 y=Vector((-math.sin(math.radians(angle)),math.cos(math.radians(angle)),0));z=Vector((0,0,1));R=Matrix((y.cross(z),y,z)).transposed()@g.to_3x3().inverted();carry=(restbase.inverted()@R).to_quaternion();worst={c:0 for c in ['Attack','Hit','Death']}
 for clip,f,tree,base,H,q,w in cache:
  rot=base@carry.slerp(q,w).to_matrix()
  for v in local:
   p=rot@v+H;hit,n,index,d=tree.find_nearest(p,.05)
   if hit is not None and (p-hit).dot(n)<-.7*d:worst[clip]=max(worst[clip],d*1000)
 results.append({'angle':angle,'contact_mm':worst});print('TRANSITION_SEARCH',results[-1],flush=True)
(P/'review/round2/transition_search.json').write_text(json.dumps(results,indent=2))
