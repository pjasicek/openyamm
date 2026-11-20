"""Fit returned stalks to the layout and add level, empty socket caps; preserve raw download."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/normalised_geometry.blend'))
o=bpy.data.objects['BroodMother'];me=o.data
co=np.array([tuple(v.co) for v in me.vertices]);original=co.copy()
layout=json.loads((P/'socket_layout.json').read_text())
measured={'right':[-2.44,-.44,2.30],'left':[2.45,-.59,1.87],'rear':[.51,2.32,2.90]}
report=[]
for socket in layout['sockets']:
 name=socket['name'];start=np.array(measured[name]);target=np.array({'left':[2.7,-.2,2.2],'right':[-2.7,-.2,2.2],'rear':[0,2.9,2.9]}[name])
 radius=np.linalg.norm(original[:,:2]-start[:2],axis=1)
 lateral=np.clip((1.03-radius)/.25,0,1);lateral=lateral*lateral*(3-2*lateral)
 h=np.clip((original[:,2]-.12)/(start[2]-.20),0,1);h=h*h*(3-2*h)
 upper=np.clip((start[2]+.65-original[:,2])/.25,0,1)
 upper=upper*upper*(3-2*upper)
 factor=lateral*h*upper
 co+=factor[:,None]*(target-start)
 # Remove uneven central peaks from the usable disc; the clear disc is the new cap's top.
 local=co[:,:2]-target[:2];r=np.linalg.norm(local,axis=1)
 near=(factor>.9)&(original[:,2]>start[2]-.18)&(original[:,2]<start[2]+.65)&(r<.67)
 co[near,2]=np.minimum(co[near,2],target[2]-.045)
 # A short grown rim, closed underneath; upper central surface is precisely level.
 n=48;verts=[tuple(target)];faces=[]
 for rad,dz in ((.64,0),(.69,-.035),(.61,-.12)):
  verts.extend([(target[0]+rad*math.cos(2*math.pi*j/n),target[1]+rad*math.sin(2*math.pi*j/n),target[2]+dz) for j in range(n)])
 verts.append(tuple(target+[0,0,-.12]));bottom=len(verts)-1
 for j in range(n):
  k=(j+1)%n;faces.append((0,1+j,1+k))
  for ring in range(2):
   a=1+ring*n+j;b=1+ring*n+k;c=b+n;d=a+n;faces.extend([(a,d,c),(a,c,b)])
  faces.append((bottom,1+2*n+k,1+2*n+j))
 mesh=bpy.data.meshes.new('Socket_'+name);mesh.from_pydata(verts,[],faces);mesh.materials.append(me.materials[0])
 ob=bpy.data.objects.new('Socket_'+name,mesh);bpy.context.scene.collection.objects.link(ob)
 report.append({'name':name,'original_top_approx_m':start.tolist(),'top_centre_blender_m':target.tolist(),'clear_radius_m':.64,'triangles':len(faces),'fitted_vertices':int((factor>.01).sum())})
for v,p in zip(me.vertices,co):v.co=p
me.update()
# Close only tiny unambiguous three/four-edge cracks; retain intentional resin openings.
bm=bmesh.new();bm.from_mesh(me)
bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=4)
bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(me);bm.free();me.update()
for f in me.polygons:f.use_smooth=True
(P/'review/socket_fit.json').write_text(json.dumps(report,indent=2)+'\n')
np.savez(P/'work/fitted_mesh.npz',vertices=np.array([tuple(v.co) for v in me.vertices]),faces=np.array([tuple(f.vertices) for f in me.polygons]))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/socket_fit.blend'))
print(json.dumps(report))
