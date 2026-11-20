"""Native stone-fragment death, with a preserved band and UVs from the living surface."""
import bpy,bmesh,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Euler,Matrix
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv.blend'))
sys.path.insert(0,str(P/'scripts'));import motion as M
rig=M.rig;M.pose('Hit',.25);rng=np.random.default_rng(608)
materials=[bpy.data.materials.new('JuggernautBody'),bpy.data.materials.new('JuggernautHead')]
chunks=[]
def source(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();a=np.array([v.co[:] for v in me.vertices]);e.to_mesh_clear();return a
def hull(points,name,source_obj,source_points,material):
 bm=bmesh.new()
 for p in points:bm.verts.new(p)
 bm.verts.ensure_lookup_table();bmesh.ops.convex_hull(bm,input=bm.verts[:],use_existing_faces=False)
 loose=[v for v in bm.verts if not v.link_faces]
 if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
 bmesh.ops.triangulate(bm,faces=bm.faces[:]);bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
 mesh=bpy.data.meshes.new(name);bm.to_mesh(mesh);bm.free();obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
 mesh.materials.append(materials[material]);uv=mesh.uv_layers.new(name='UVMap').data
 source_obj.data.calc_loop_triangles();triangles=list(source_obj.data.loop_triangles);su=source_obj.data.uv_layers.active.data
 tree=KDTree(len(triangles))
 for i,tr in enumerate(triangles):tree.insert(Vector(source_points[list(tr.vertices)].mean(0)),i)
 tree.balance()
 for f in mesh.polygons:
  center=sum((mesh.vertices[i].co for i in f.vertices),Vector())/len(f.vertices);_,ti,_=tree.find(center);tr=triangles[ti]
  for li,sl in zip(f.loop_indices,tr.loops):uv[li].uv=su[sl].uv
 chunks.append((obj,'stone'))
def partition(o,ids,count,material):
 a=source(o);pts=a[ids];centres=[pts[np.argmin(pts[:,2])]]
 for _ in range(count-1):centres.append(pts[np.argmax(np.min([((pts-c)**2).sum(1) for c in centres],axis=0))])
 centres=np.array(centres)
 for _ in range(12):
  labels=np.argmin(((pts[:,None]-centres[None,:])**2).sum(2),axis=1)
  for i in range(count):
   if np.any(labels==i):centres[i]=pts[labels==i].mean(0)
 for i in range(count):
  p=pts[labels==i]
  if len(p)>80:p=p[np.linspace(0,len(p)-1,80).astype(int)]
  if len(p)>=6:hull(p,f'{o.name}Shard_{i}',o,a,material)
body=bpy.data.objects['Body'];head=bpy.data.objects['Head'];a=source(body)
bandfaces=[f for f in body.data.polygons if body.data.attributes['band'].data[f.index].value]
bandverts=sorted(set(v for f in bandfaces for v in f.vertices));remap={v:i for i,v in enumerate(bandverts)}
me=bpy.data.meshes.new('BandShard');me.from_pydata([a[i] for i in bandverts],[],[[remap[i] for i in f.vertices] for f in bandfaces]);me.materials.append(materials[0]);uv=me.uv_layers.new(name='UVMap').data
for f,src in zip(me.polygons,bandfaces):
 for li,sl in zip(f.loop_indices,src.loop_indices):uv[li].uv=body.data.uv_layers.active.data[sl].uv
band=bpy.data.objects.new('BandShard',me);bpy.context.collection.objects.link(band);chunks.append((band,'band'))
partition(body,np.array(sorted({i for f in body.data.polygons for i in f.vertices}-set(bandverts))),56,0)
partition(head,np.array(sorted({i for f in head.data.polygons for i in f.vertices})),6,1)
M.pose('Standing',0)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');records=[]
for i,(o,kind) in enumerate(chunks):
 points=np.array([v.co[:] for v in o.data.vertices]);c=points.mean(0);bone=rig.data.edit_bones.new(f'D_{i:02d}');bone.head=c;bone.tail=c+[0,0,.05]
 axis=rng.normal(size=3);axis/=np.linalg.norm(axis);q=Quaternion(axis,float(rng.uniform(-2.5,2.5)))
 end=np.array([c[0]*.8,c[1]*.4,0])+rng.uniform(-.035,.035,3);end[2]=0
 if kind=='band':q=Euler((.08,.20,.3)).to_quaternion();end=np.array([0,.02,0])
 records.append(dict(bone=bone.name,kind=kind,centre=c.tolist(),points=(points-c).tolist(),end=end.tolist(),rotation=list(q)))
flashbone=rig.data.edit_bones.new('FlashControl');flashbone.head=(0,-.255,.615);flashbone.tail=(0,-.255,.67);flashbone.parent=rig.data.edit_bones['Chest']
bpy.ops.object.mode_set(mode='OBJECT')
for (o,_),r in zip(chunks,records):
 g=o.vertex_groups.new(name=r['bone']);g.add(list(range(len(o.data.vertices))),1,'REPLACE');o.parent=rig;mod=o.modifiers.new('Armature','ARMATURE');mod.object=rig
 for f in o.data.polygons:f.use_smooth=False
bpy.ops.object.select_all(action='DESELECT')
for o,_ in chunks:o.select_set(True)
bpy.context.view_layer.objects.active=chunks[0][0];bpy.ops.object.join();bpy.context.object.name='Rubble'
# A short emissive burst between the palms, matching the native melee flash.
vertices=[];faces=[];center=Vector((0,-.255,.615))
for axis in range(3):
 start=len(vertices);vertices.append(tuple(center))
 for i in range(24):
  angle=2*math.pi*i/24;radius=.082 if i%2==0 else .024;p=[0.,0.,0.];p[(axis+1)%3]=radius*math.cos(angle);p[(axis+2)%3]=radius*math.sin(angle);vertices.append(tuple(center+Vector(p)))
 for i in range(24):faces.append((start,start+1+i,start+1+(i+1)%24))
mesh=bpy.data.meshes.new('Flash');mesh.from_pydata(vertices,[],faces);bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.create_icosphere(bm,subdivisions=2,radius=.035,matrix=Matrix.Translation(center));bm.to_mesh(mesh);bm.free();flash=bpy.data.objects.new('Flash',mesh);bpy.context.collection.objects.link(flash);flash.parent=rig;mod=flash.modifiers.new('Armature','ARMATURE');mod.object=rig
g=flash.vertex_groups.new(name='FlashControl');g.add(list(range(len(mesh.vertices))),1,'REPLACE')
(P/'work/fragments.json').write_text(json.dumps(records,indent=2));assert len(records)==63
for b in rig.pose.bones:
 if b.name.startswith('D_') or b.name=='FlashControl':b.scale=(.00001,)*3
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_complete.blend'))
print('RUBBLE',len(records),sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),flush=True)
