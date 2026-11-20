"""Add the missing left little claw and an inset skin backing beneath open belly plates."""
import bpy,bmesh,json,math
import numpy as np
from mathutils import Matrix,Vector
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/socket_fit.blend'))
queen=bpy.data.objects['BroodMother'];mat=queen.data.materials[0]
fit=json.loads((P/'work/fingers_fit.json').read_text());spec=json.loads((P/'work/joints.json').read_text())['raw_to_blender']
# The four original left-hand branches are intact. This short fifth claw roots inside the outer palm.
points=np.array(fit['L']['chains']['pinky']['points']);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
verts=[];faces=[];rings=11;sides=10
for i,t in enumerate(np.linspace(0,arc[-1],rings)):
 c=np.array([np.interp(t,arc,points[:,k]) for k in range(3)]);k=min(np.searchsorted(arc,t,side='right')-1,2);k=max(k,0)
 direction=Vector(points[k+1]-points[k]).normalized();u=direction.cross(Vector((0,1,0))).normalized();v=direction.cross(u).normalized()
 rad=float(np.interp(t/arc[-1],[0,.25,.65,.88,1],[.067,.059,.040,.017,.002]))
 for j in range(sides):
  q=Vector(c)+rad*(math.cos(2*math.pi*j/sides)*u+math.sin(2*math.pi*j/sides)*v);verts.append(tuple(q))
for i in range(rings-1):
 for j in range(sides):
  a=i*sides+j;b=i*sides+(j+1)%sides;c=b+sides;d=a+sides;faces.extend([(a,b,c),(a,c,d)])
faces.extend([tuple(reversed(range(sides))),tuple((rings-1)*sides+j for j in range(sides))])
mesh=bpy.data.meshes.new('LeftLittleFinger');mesh.from_pydata(verts,[],faces);mesh.materials.append(mat)
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
for f in mesh.polygons:f.use_smooth=True
o=bpy.data.objects.new('LeftLittleFinger',mesh);bpy.context.scene.collection.objects.link(o)
# Existing belly plate surface points define an inset convex backing; exclude both hands from the hull.
co=np.array([tuple(v.co) for v in queen.data.vertices]);R=np.array(Matrix.Rotation(math.radians(-45),3,'Z'))
raw=co@R.T/spec['scale'];raw[:,2]+=spec['floor_raw_z'];centre=np.array([0,-.06,-.10]);radius=np.array([.23,.30,.23]);r=np.linalg.norm((raw-centre)/radius,axis=1)
sel=(r>.70)&(r<1.10)&(raw[:,2]>.30*-1)&(raw[:,2]<.105)&(raw[:,1]<.15)
for side in fit:sel[fit[side]['hand_vertices']]=False
pts=co[sel];assert len(pts)>200
bm=bmesh.new();vv=[bm.verts.new(Vector(p)) for p in pts];result=bmesh.ops.convex_hull(bm,input=vv,use_existing_faces=False)
bmesh.ops.delete(bm,geom=list(set(result['geom_interior']+result['geom_unused'])),context='VERTS')
bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
centre_world=Matrix.Rotation(math.radians(45),3,'Z')@Vector((centre-[0,0,spec['floor_raw_z']])*spec['scale'])
for v in bm.verts:
 delta=v.co-centre_world;v.co-=delta.normalized()*.018
mesh=bpy.data.meshes.new('BellyInnerSkin');bm.to_mesh(mesh);bm.free();mesh.materials.append(mat)
for f in mesh.polygons:f.use_smooth=True
o=bpy.data.objects.new('BellyInnerSkin',mesh);bpy.context.scene.collection.objects.link(o)
report={'left_hand':'Four returned digits plus locally repaired little finger; fitted reference position and topology retained.',
 'belly_backing':{'sampled_surface_vertices':len(pts),'triangles':len(mesh.polygons),'inset_m':.018,'intent':'Skin under plate cracks; static with belly, cradle holes remain open.'}}
(P/'review/surface_repairs.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/repaired_geometry.blend'));print(json.dumps(report))
