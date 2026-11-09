"""Measured bird skeleton; connected skin blends and rigid feather/claw ownership."""
import bpy, bmesh, json
import numpy as np
from pathlib import Path
from mathutils import Vector, kdtree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/static_v1.blend'))
body=bpy.data.objects['Body']; bm=bmesh.new(); bm.from_mesh(body.data)
part=bm.verts.layers.int['part']; jaw=bm.verts.layers.int.new('lower_jaw'); oral=bm.faces.layers.int.new('oral')
# Split the lower bill along the measured closed seam, retaining the upper hook on the skull.
origin=Vector((0,-.185,.157));normal=Vector((0,-.10,1))
faces=[f for f in bm.faces if all(v[part]==0 and v.co.y<-.169 for v in f.verts)]
geom=set(faces)
for f in faces:geom.update(f.edges);geom.update(f.verts)
cut=bmesh.ops.bisect_plane(bm,geom=list(geom),dist=1e-7,plane_co=origin,plane_no=normal)
edges=[e for e in cut['geom_cut'] if isinstance(e,bmesh.types.BMEdge)]
bmesh.ops.split_edges(bm,edges=edges)
for f in bm.faces:
 c=f.calc_center_median()
 if all(v[part]==0 for v in f.verts) and c.y<-.169 and (c-origin).dot(normal)<-1e-7:
  for v in f.verts:v[jaw]=1
for lower in (False,True):
 border=[e for e in bm.edges if e.is_boundary and all(v.co.y<-.169 and abs((v.co-origin).dot(normal))<2e-6 for v in e.verts) and bool(all(v[jaw] for v in e.verts))==lower]
 if border:
  center=bm.verts.new((0,-.169,.1586));center[jaw]=int(lower);center[part]=0
  for e in border:
   a,b=e.verts;f=bm.faces.new((a,b,center) if lower else (b,a,center));f[oral]=1
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
me=body.data;co=np.array([v.co[:] for v in me.vertices]);pa=np.array([v.value for v in me.attributes['part'].data]);jw=np.array([v.value for v in me.attributes['lower_jaw'].data],bool)
x,y,z=co.T;wing=(abs(x)>.050)&(z>.108)&(y<.170)
tail=(y>.105)&(abs(x)<.093)&(z<.118)
bones={}
def chain(names,points,parent):
 for i,n in enumerate(names):bones[n]={'head':list(points[i]),'tail':list(points[i+1]),'parent':parent if i==0 else names[i-1]}
chain(['Root'],[(0,0,.13),(0,0,.18)],None)
chain(['Chest','Neck','Head'],[(0,.025,.13),(0,-.075,.157),(0,-.137,.172),(0,-.210,.16)],'Root')
chain(['Jaw'],[(0,-.169,.1586),(0,-.205,.151)],'Head')
chain(['Tail'],[(0,.070,.107),(0,.205,.068)],'Chest')
for sd,sg in [('L',1),('R',-1)]:
 chain([sd+'Wing0',sd+'Wing1',sd+'Wing2'],[(sg*.048,-.046,.154),(sg*.155,-.025,.179),(sg*.290,-.053,.246),(sg*.460,-.055,.335)],'Chest')
 chain([sd+'Thigh',sd+'Tarsus',sd+'Foot'],[(sg*.046,.020,.102),(sg*.064,.069,.069),(sg*.058,.044,.035),(sg*.057,.024,.016)],'Chest')
 for j,(xx,yy) in enumerate([(.030,.026),(.057,.019),(.082,.030),(.059,.070)]):
  chain([sd+'Toe'+str(j)],[(sg*(.045+.012*j if j<3 else .057),.040,.035),(sg*xx,yy,.014 if j<3 else .025)],sd+'Foot')
arm=bpy.data.armatures.new('PhoenixSkeleton');rig=bpy.data.objects.new('Rig',arm);bpy.context.collection.objects.link(rig)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for n,b in bones.items():
 e=arm.edit_bones.new(n);e.head=b['head'];e.tail=b['tail'];e.align_roll(Vector((0,0,1)));e.parent=arm.edit_bones.get(b['parent']) if b['parent'] else None
bpy.ops.object.mode_set(mode='OBJECT')
names=list(bones);ix={n:i for i,n in enumerate(names)};W=np.zeros((len(co),len(names)))
def linear(ids,ns,stations,values):
 W[ids]=0
 for k,n in enumerate(ns):W[ids,ix[n]]=np.interp(values,stations,np.eye(len(ns))[k])
linear(np.arange(len(co)),['Head','Neck','Chest'],[-.142,-.091,-.04],y)
for sd,sg in [('L',1),('R',-1)]:
 ids=np.where(wing&(x*sg>0))[0]
 linear(ids,['Chest',sd+'Wing0',sd+'Wing1',sd+'Wing2'],[.050,.105,.225,.335],abs(x[ids]))
 ids=np.where((x*sg>0)&(~wing)&(~tail)&(y>-.005)&(z<.112))[0]
 linear(ids,[sd+'Foot',sd+'Tarsus',sd+'Thigh','Chest'],[.035,.059,.085,.112],z[ids])
 k=np.clip((abs(x[ids])-.018)/.026,0,1)*np.clip((.108-y[ids])/.035,0,1);k=k*k*(3-2*k)
 W[ids]*=k[:,None];W[ids,ix['Chest']]+=1-k
 ids=np.where(np.isin(pa,[1,2,5,6,7,8,9,10])&(x*sg>0))[0]
 W[ids]=0;W[ids,ix[sd+'Foot']]=1
 # The three disconnected dark claws retain their nearest toe's rigid ownership.
 for part_id in np.unique(pa[ids]):
  small=ids[pa[ids]==part_id]
  if len(small)>300:continue
  c=co[small].mean(0);j=int(np.argmin([np.linalg.norm(c-np.array(bones[sd+'Toe'+str(j)]['tail'])) for j in range(3)]))
  W[small]=0;W[small,ix[sd+'Toe'+str(j)]]=1
 # Skin toes blend only below the palm; the rear toe stays behind the ankle.
 ids=np.where(np.isin(pa,[1,2])&(x*sg>0)&(z<.040))[0]
 for i in ids:
  j=3 if y[i]>.055 else int(np.argmin(abs(abs(x[i])-np.array([.032,.057,.082]))))
  k=float(np.clip((.042-z[i])/.024,0,1));W[i]*=1-k;W[i,ix[sd+'Toe'+str(j)]]+=k
linear(np.where(tail)[0],['Chest','Tail'],[.092,.137],y[tail])
ids=np.where(jw)[0]
W[ids]=0;W[ids,ix['Jaw']]=1
# Covert fragments follow their nearest skin attachment, not a neighbouring foot or tail.
main=np.where(pa==0)[0];tree=kdtree.KDTree(len(main))
for i in main:tree.insert(Vector(co[i]),int(i))
tree.balance()
for part_id in np.unique(pa):
 if part_id==0 or part_id in [1,2,5,6,7,8,9,10]:continue
 ids=np.where(pa==part_id)[0];c=co[ids].mean(0)
 if tail[ids].all():W[ids]=0;W[ids,ix['Tail']]=1
 elif wing[ids].all():
  # Each feather is rigid; use the basal quarter where it overlaps the covert surface.
  sd='L' if c[0]>0 else 'R';base=ids[np.argsort(abs(x[ids]))[:max(3,len(ids)//4)]]
  xx=float(np.mean(abs(x[base])));w=np.array([np.interp(xx,[.05,.105,.225,.315],np.eye(4)[k]) for k in range(4)])
  W[ids]=0
  for n,v in zip(['Chest',sd+'Wing0',sd+'Wing1',sd+'Wing2'],w):W[ids,ix[n]]=v
 else:
  near=min((tree.find(Vector(co[i])) for i in ids),key=lambda a:a[2]);W[ids]=W[near[1]]
# Smooth the continuous shoulder, neck and thigh transitions without mixing separate feathers.
adj=[[] for _ in co]
for e in me.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
for _ in range(3):
 old=W.copy()
 for i in np.where((pa==0)&(~jw))[0]:
  if adj[i]:W[i]=.80*old[i]+.20*old[adj[i]].mean(0)
keep=np.argpartition(W,-4,axis=1)[:,-4:];mask=np.zeros_like(W,bool);np.put_along_axis(mask,keep,True,axis=1);W[~mask]=0;W/=W.sum(1)[:,None]
body.vertex_groups.clear()
for n in names:
 g=body.vertex_groups.new(name=n)
 for i in np.where(W[:,ix[n]]>1e-7)[0]:g.add([int(i)],float(W[i,ix[n]]),'REPLACE')
mod=body.modifiers.new('PhoenixSkin','ARMATURE');mod.object=rig;body.parent=rig;rig.show_in_front=True
for pb in rig.pose.bones:pb.rotation_mode='QUATERNION'
for attr,values in [('wing',wing),('tail',tail)]:
 layer=me.attributes.new(attr,'BOOLEAN','POINT')
 for i,v in enumerate(values):layer.data[i].value=bool(v)
body.data.materials.clear()
for name,col in [('Feathers',(.52,.24,.055,1)),('BeakClaws',(.14,.075,.035,1)),('Mouth',(.035,.008,.005,1))]:
 m=bpy.data.materials.new(name);m.diffuse_color=col;m.use_nodes=True;m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=col;body.data.materials.append(m)
for f in me.polygons:
 c=np.mean(co[list(f.vertices)],0);f.material_index=2 if me.attributes['oral'].data[f.index].value else 1 if (c[1]<-.175 or c[2]<.038) else 0
assert np.isfinite(W).all() and np.allclose(W.sum(1),1) and len(bones)<128
assert sum(jw)>15,('no lower beak',sum(jw))
(P/'work/rig.json').write_text(json.dumps({'bones':bones,'vertices':len(co),'triangles':sum(len(f.vertices)-2 for f in me.polygons),'jaw_vertices':int(sum(jw))},indent=2))
np.savez(P/'work/rig_weights.npz',weights=W,co=co,parts=pa,names=np.array(names),wing=wing)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'));print('PHOENIX RIG',len(bones),'bones',len(co),'vertices',sum(jw),'jaw vertices')
