import bpy,bmesh,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/master.blend'));C.reset();C.cleanup();o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];s=bpy.context.scene;pv=np.array([a.value for a in o.data.attributes['piece'].data]);co=np.array([v.co[:] for v in o.data.vertices])
# Eyeballs sit within the eyelid opening instead of crossing its rim.
for pid in [14,15]:
 ids=np.where(pv==pid)[0];center=co[ids].mean(0)
 for i in ids:o.data.vertices[int(i)].co=Vector(center+(co[i]-center)*.93+np.array([0,.001,0]))
# Solve a garment-only harmonic skin field between torso, sleeve and cuff anchors.
names=['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck']+[f'B_{sd}_{n}' for sd in 'LR' for n in ['Clavicle','UpperArm','Forearm','Hand']];W=np.zeros((len(co),len(names)));seed=np.zeros(len(co),bool);adj=[[]for _ in co]
def putrow(i,w):
 for n,v in w.items():W[i,names.index(n)]=v
 seed[i]=True
for i in np.where(pv==1)[0]:
 x,y,z=co[i];sd='L'if x>0 else'R';ax=abs(x)
 if ax<.17 or (ax<.31 and z<1.20):
  zs=[.98,1.12,1.245,1.34];j=int(np.clip(np.searchsorted(zs,z)-1,0,2));t=float(np.clip((z-zs[j])/(zs[j+1]-zs[j]),0,1));t=t*t*(3-2*t);putrow(i,{names[j]:1-t,names[j+1]:t})
 elif z>1.35 and ax<.19:putrow(i,{'B_Spine2':1})
 else:
  a=np.array(r.data.bones[f'B_{sd}_UpperArm'].head_local);b=np.array(r.data.bones[f'B_{sd}_Forearm'].head_local);c=np.array(r.data.bones[f'B_{sd}_Hand'].head_local);d=b-a;t=np.dot(co[i]-a,d)/np.dot(d,d)
  if ax>.325 and t>.40:
   d=c-b;u=np.dot(co[i]-b,d)/np.dot(d,d);blend=float(np.clip((t-.67)/.65,0,1));hand=float(np.clip((u-.70)/.25,0,1));putrow(i,{f'B_{sd}_UpperArm':(1-blend)*(1-hand),f'B_{sd}_Forearm':blend*(1-hand),f'B_{sd}_Hand':hand})
for e in o.data.edges:
 a,b=e.vertices
 if pv[a]==pv[b]==1:adj[a].append(b);adj[b].append(a)
free=[i for i in np.where(pv==1)[0]if not seed[i]]
# Harmonic coordinates are bounded and cannot give the opposite arm any belly influence.
for i in free:W[i,names.index('B_Spine2')]=1
for iteration in range(400):
 old=W.copy()
 for i in free:
  nb=adj[i]
  if nb:W[i]=old[nb].mean(0)
 if np.max(abs(W-old))<1e-7:break
for i in np.where(pv==1)[0]:
 v=o.data.vertices[int(i)]
 for g in list(v.groups):o.vertex_groups[g.group].remove([int(i)])
 ids=np.argsort(W[i])[-4:];total=W[i,ids].sum()
 for j in ids:
  if W[i,j]>1e-8:o.vertex_groups[names[j]].add([int(i)],float(W[i,j]/total),'REPLACE')
# Keep garment waist inside the belt with an axial overlap, no free flaps.
for i in np.where((pv==1)&(co[:,2]<1.03)&(abs(co[:,0])<.34))[0]:
 v=o.data.vertices[int(i)];t=max(0,min(1,(1.03-v.co.z)/.055));v.co.x*=1-.035*t;v.co.y*=1-.035*t;v.co.z-=.015*t
# New hand-only UV layout, independent of head and clothing.
handmat=o.data.materials[0].copy();handmat.name='MerchantHands_A';o.data.materials.append(handmat)
for f in o.data.polygons:f.material_index=2 if pv[f.vertices[0]] in [3,4]else f.material_index
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
for f in o.data.polygons:f.select=f.material_index==2
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=1.45,island_margin=.066,scale_to_bounds=True);bpy.ops.object.mode_set(mode='OBJECT')
C.reset();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round3/master_pretexture.blend'))
common.workbench_clay(s,True)
for role,t in [('Standing',0),('Attack',.375),('Attack',.9167),('Death',1.3)]:
 C.activate(role,t);common.render_views(str(P/'review/round3'/f'weights_{role}_{t}'),1.15,1.2,views=('front','left','three_quarter'),resolution=(800,900))
(P/'review/round3/weight_method.json').write_text(json.dumps({'method':'Continuous-shirt harmonic coordinates with anatomical torso/sleeve/cuff anchors; pelvis-anchored tucked waist','seed_vertices':int(seed.sum()),'free_vertices':len(free),'iterations':iteration+1},indent=2))
