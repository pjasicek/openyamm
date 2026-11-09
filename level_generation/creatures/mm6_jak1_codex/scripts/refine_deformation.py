import bpy,numpy as np,json
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated_master.blend'));body=bpy.data.objects['Body'];me=body.data;pv=np.array([a.value for a in me.attributes['piece'].data]);co=np.array([tuple(v.co)for v in me.vertices]);gi={g.name:g.index for g in body.vertex_groups}
# Upper buttock/groin belongs to the pelvis, not both moving femurs.
for v in me.vertices:
 i=v.index;x,y,z=v.co
 if pv[i]==0 and abs(x)<.25 and .85<z<1.10:
  pel=float(np.clip((z-.89)/.14,0,1));pel=max(pel,float(np.clip((.055-abs(x))/.035,0,1)*np.clip((z-.89)/.04,0,1)))
  side='L' if x>0 else 'R';weights={gi['B_Pelvis']:pel,gi[f'B_{side}_Thigh']:1-pel}
  for g in v.groups[:]:body.vertex_groups[g.group].remove([i])
  for g,w in weights.items():body.vertex_groups[g].add([i],w,'REPLACE')
 if pv[i]==3:v.co+=v.normal*.007
 if pv[i]==1:
  r=max((x*x+y*y)**.5,.01);ease=float(np.clip((1.07-z)/.13,0,1));margin=.012*ease
  v.co.x*=1+margin/r;v.co.y*=1+margin/r
co=np.array([tuple(v.co)for v in me.vertices]);skin=np.where((pv==0)&(co[:,2]>.60)&(co[:,2]<1.16))[0];tree=KDTree(len(skin))
for i in skin:tree.insert(me.vertices[i].co,int(i))
tree.balance();W={v.index:{g.group:g.weight for g in v.groups}for v in me.vertices}
for i in np.where(pv==1)[0]:
 near=tree.find_n(me.vertices[i].co,3);weights={};total=sum(1/max(d,.002)**2 for _,_,d in near)
 for _,j,d in near:
  for g,w in W[j].items():weights[g]=weights.get(g,0)+w/max(d,.002)**2/total
 for g in me.vertices[i].groups[:]:body.vertex_groups[g.group].remove([int(i)])
 for g,w in weights.items():body.vertex_groups[g].add([int(i)],w,'REPLACE')
# Keep the planted sole just above ground; root-only correction preserves all limb lengths.
rig=bpy.data.objects['Rig'];feet=np.where(np.isin(pv,[7,8,10,11]))[0];root=rig.pose.bones['B_Pelvis'];inv=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted();floor={}
from mathutils import Vector
for a in []:  # Foot contact is solved with leg IK in animate_staff, preserving the source pelvis.
 if a.name in ('Standing','Fidget','Death','Dead'):continue
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];rows=[]
 for f in range(int(a.frame_range[1])+1):
  bpy.context.scene.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();z=min(em.vertices[int(i)].co.z for i in feet);ev.to_mesh_clear()
  # Running retains its airborne phase; death is floored by its entire surface.
  if a.name in ['Death','Dead']:
   ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();z=min(v.co.z for v in em.vertices);ev.to_mesh_clear()
  target=.0015 if a.name in ('Standing','Fidget') else .003
  dz=max(0,target-z) if a.name=='Running' else target-z
  root.location+=inv@Vector((0,0,dz));root.keyframe_insert('location',frame=f);rows.append(dz)
 floor[a.name]=[min(rows),max(rows)]
from shoulder_weights import repair_shoulders
repair_shoulders(body)
rig.animation_data.action=None
(P/'work/floor_correction.json').write_text(json.dumps(floor,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/animated_master.blend'))
