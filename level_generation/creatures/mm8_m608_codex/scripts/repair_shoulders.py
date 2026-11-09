"""Separate the fused stone shoulders so raised arms cannot stretch rib surfaces."""
import bpy,bmesh,json,sys,subprocess,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/shoulder_fix_v2/before/work/rig_uv.blend'))
body=bpy.data.objects['Body'];head=bpy.data.objects['Head']
# Join only for the cut: the two texture surfaces already share a coincident neck boundary.
for o in [body,head]:
 a=o.data.attributes.new('head_surface','INT','FACE')
 for d in a.data:d.value=int(o==head)
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);head.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
bm=bmesh.new();bm.from_mesh(body.data);dlay=bm.verts.layers.deform.verify();uv=bm.loops.layers.uv.active
layer=bm.faces.layers.int['head_surface'];band=bm.faces.layers.int.get('band')
# Welding only coincident texture-boundary vertices leaves UV islands intact.
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
upperfaces=[f for f in bm.faces if min(v.co.z for v in f.verts)>.4 and not (band and f[band])]
upperverts={v for f in upperfaces for v in f.verts};upperedges={e for f in upperfaces for e in f.edges}
# Use the concave stone creases rather than cutting through the broad rib plates.
for i,f in enumerate(upperfaces):f.index=i
adj=[];cost=[]
for e in upperedges:
 if len(e.link_faces)!=2:continue
 a,b=e.link_faces
 if a not in upperfaces or b not in upperfaces:continue
 angle=e.calc_face_angle()
 adj.append([a.index,b.index]);cost.append(max(1,int(e.calc_length()*100000*(2 if e.is_convex else .08+np.exp(-8*angle)))))
path=P/'work/shoulder_motion_v3/cut.npz'
np.savez(path,centres=np.array([f.calc_center_median()[:] for f in upperfaces]),adj=adj,cost=cost)
subprocess.run(['/usr/bin/python3',str(P/'scripts/shoulder_cut.py'),str(path)],check=True)
labels=np.load(str(path)+'.labels.npy');cut_edges=[e for e in upperedges if len(e.link_faces)==2 and all(f in upperfaces for f in e.link_faces) and labels[e.link_faces[0].index]!=labels[e.link_faces[1].index]]
bmesh.ops.split_edges(bm,edges=cut_edges)
newfaces=bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0)['faces']
newfaces=bmesh.ops.triangulate(bm,faces=newfaces)['faces']
# Closed surfaces share a continuous patch of the existing roller stone texture.
# Pixel rectangle is wholly inside the large stone UV island, away from band/padding.
def stone_uv(u,v):return Vector(((328+56*u)/1024,1-(798+76*v)/1024))
remaining=set(newfaces)
while remaining:
 group={remaining.pop()};stack=list(group)
 while stack:
  f=stack.pop()
  for e in f.edges:
   for other in e.link_faces:
    if other in remaining:remaining.remove(other);group.add(other);stack.append(other)
 vertices=list({v for f in group for v in f.verts});points=np.array([v.co[:] for v in vertices]);centre=points.mean(0)
 _,_,axes=np.linalg.svd(points-centre,full_matrices=False);flat=(points-centre)@axes[:2].T;lo=flat.min(0);span=np.maximum(np.ptp(flat,axis=0),1e-6)
 mapping={v:stone_uv(*((xy-lo)/span)) for v,xy in zip(vertices,flat)}
 for f in group:
  f[layer]=0
  if band:f[band]=0
  for l in f.loops:l[uv].uv=mapping[l.vert]
  f.smooth=False
# Assign each connected stone section as a unit, preserving elbow/hand weights.
groups={g.name:g.index for g in body.vertex_groups};seen=set();parts=[]
for start in bm.verts:
 if start in seen:continue
 stack=[start];seen.add(start);component=[]
 while stack:
  v=stack.pop();component.append(v)
  for e in v.link_edges:
   other=e.other_vert(v)
   if other not in seen:seen.add(other);stack.append(other)
 c=sum((v.co for v in component),Vector())/len(component)
 if max(v.co.z for v in component)<.5:continue
 s=1 if c.x>0 else -1
 isarm=abs(c.x)>.205
 for v in component:
  weights=v[dlay]
  if isarm:
   side='L' if s>0 else 'R';names=[f'{p}_{side}' for p in ['UpperArm','Forearm','Hand']]
   w={groups[n]:weights.get(groups[n],0) for n in names}
   total=sum(w.values())
   if total<1e-7:w={groups[names[0]]:1};total=1
   w={i:a/total for i,a in w.items()}
   blend=float(np.clip((v.co.z-.60)/.05,0,1));blend=blend*blend*(3-2*blend)
   w={i:a*(1-blend) for i,a in w.items()};w[groups[names[0]]]=w.get(groups[names[0]],0)+blend;total=1
   weights.clear()
   for i,a in w.items():
    if a>1e-6:weights[i]=a/total
  else:
   # The original face/neck articulation stays; no torso vertex follows an arm.
   w={i:a for i,a in weights.items() if not body.vertex_groups[i].name.endswith(('_L','_R'))}
   total=sum(w.values());weights.clear()
   if total<1e-7:weights[groups['Chest']]=1
   else:
    for i,a in w.items():weights[i]=a/total
 parts.append({'vertices':len(component),'centroid':list(c),'arm':isarm})
# Closed, overlapping stone joints cover the socket as the rigid arms rotate.
for side,sign in [('L',1),('R',-1)]:
 centre=Vector((sign*.215,.075,.755))
 made=bmesh.ops.create_icosphere(bm,subdivisions=2,radius=1,calc_uvs=True)['verts']
 rng=np.random.default_rng(608+(sign+1))
 for v in made:
  p=v.co.copy();p*=float(rng.uniform(.94,1.06));v.co=centre+Vector((p.x*.073,p.y*.082,p.z*.078));v[dlay][groups[f'UpperArm_{side}']]=1
 faces={f for v in made for f in v.link_faces}
 for f in faces:
  f[layer]=0
  if band:f[band]=0
  for l in f.loops:l[uv].uv=stone_uv(*l[uv].uv)
  f.smooth=True
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
# Restore the two original texture owners.
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
for f in body.data.polygons:f.select=bool(body.data.attributes['head_surface'].data[f.index].value)
bpy.context.tool_settings.mesh_select_mode=(False,False,True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.separate(type='SELECTED');bpy.ops.object.mode_set(mode='OBJECT')
head=next(o for o in bpy.context.selected_objects if o!=body);head.name='Head'
for o in [body,head]:
 bm=bmesh.new();bm.from_mesh(o.data);loose=[v for v in bm.verts if not v.link_faces]
 if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
 bm.to_mesh(o.data);bm.free()
assert len([p for p in parts if p['arm'] and p['vertices']>100])==2,parts
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_uv.blend'))
(P/'work/shoulder_motion_v3/repair.json').write_text(json.dumps({'parts':parts,'cap_triangles':len(newfaces),'body_triangles':len(body.data.polygons),'head_triangles':len(head.data.polygons)},indent=2))
print('SHOULDER_REPAIR_COMPLETE',flush=True)
