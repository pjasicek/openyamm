"""Layered closed feather meshes, measured against the accepted front silhouette."""
from pathlib import Path
import bpy,bmesh,json,math,sys
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'))
meta=[];piece=1000
mat=bpy.data.materials.new('FeathersProvisional');mat.diffuse_color=(.11,.12,.13,1)
def mesh_object(name,verts,faces,record):
 global piece
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 me.attributes.new('piece','INT','POINT').data.foreach_set('value',[piece]*len(me.vertices))
 ob=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(ob);me.materials.append(mat)
 for f in me.polygons:f.use_smooth=True
 record.update({'name':name,'piece':piece,'triangles':len(me.polygons)});meta.append(record);piece+=1
 return ob
def feather(name,root,tip,width,bone,parent,side,kind,index,covert=False):
 root=Vector(root);tip=Vector(tip);axis=(tip-root).normalized()
 across=Vector((-axis.z,0,axis.x));normal=axis.cross(across).normalized()
 ts=(.22,.67) if covert else (.05,.23,.46,.68,.86)
 verts=[tuple(root)];faces=[];length=(tip-root).length
 for t in ts:
  centre=root+(tip-root)*t+normal*(.018*math.sin(math.pi*t))
  # Rounded shoulders taper steadily to a slightly curved, pointed feather tip.
  w=width*(math.sin(math.pi*t)**.65)
  h=(.004 if covert else .006)*math.sin(math.pi*t)
  for off in (across*(-w*.48),normal*h,across*(w*.52),normal*(-h)):
   verts.append(tuple(centre+off))
 end=len(verts);verts.append(tuple(tip))
 for j in range(4):faces.append((0,1+(j+1)%4,1+j))
 for k in range(len(ts)-1):
  a=1+k*4;b=a+4
  for j in range(4):faces.append((a+j,a+(j+1)%4,b+(j+1)%4,b+j))
 last=1+(len(ts)-1)*4
 for j in range(4):faces.append((last+j,last+(j+1)%4,end))
 return mesh_object(name,verts,faces,{'bone':bone,'parent':parent,'root':list(root),'tip':list(tip),'side':side,'kind':kind,'index':index,'covert':covert})
for side,sg in (('L',1),('R',-1)):
 def point(x,y,z):return (sg*x,y,z)
 joints=[point(.16,.14,1.43),point(.30,.20,1.49),point(.59,.23,1.64),point(.98,.23,1.93),point(1.77,.23,2.02)]
 bones=[f'Wing_{side}_{n}' for n in ('Root','Arm','Fore','Hand')]
 # A slender supporting wing under the overlapping feather rows.
 path=[]
 for i in range(4):
  for t in (0,.5):
   p=Vector(joints[i]).lerp(Vector(joints[i+1]),t);path.append((p,i+t))
 path.append((Vector(joints[-1]),4))
 verts=[];faces=[]
 for i,(p,along) in enumerate(path):
  prev=path[max(0,i-1)][0];nxt=path[min(len(path)-1,i+1)][0];axis=(nxt-prev).normalized()
  across=Vector((-axis.z,0,axis.x));normal=axis.cross(across).normalized()
  radius=np.interp(along,[0,1,2,3,4],[.075,.065,.055,.065,.008])
  for j in range(8):
   a=j*math.tau/8;verts.append(tuple(p+normal*(math.cos(a)*radius*.45)+across*(math.sin(a)*radius)))
 for i in range(len(path)-1):
  for j in range(8):faces.append((i*8+j,i*8+(j+1)%8,(i+1)*8+(j+1)%8,(i+1)*8+j))
 faces.extend([(0,3,2,1),(0,7,6,5),(0,5,4,3)])
 a=(len(path)-1)*8;faces.extend([(a,a+1,a+2,a+3),(a,a+5,a+6,a+7),(a,a+3,a+4,a+5)])
 mesh_object(f'WingCore_{side}',verts,faces,{'side':side,'kind':'core','joints':joints,'bones':bones,'path':[[list(p),t] for p,t in path]})
 tips=[(1.80,2.08),(1.87,1.96),(1.87,1.81),(1.82,1.66),(1.73,1.51),(1.62,1.38),(1.50,1.26),(1.37,1.17),(1.23,1.11),(1.10,1.07)]
 flights=[]
 for i,(tx,tz) in enumerate(tips):
  root=point(.98+.13*(1-i/9),.235,1.93-.055*i/9)
  tip=point(tx,.235+.025*math.sin(i*.5),tz);bone=f'Feather_{side}_P{i:02d}'
  feather(bone,root,tip,.19,bone,bones[3],side,'primary',i);flights.append((root,tip,bone,bones[3],i))
 for i in range(8):
  t=i/7;root=point(.22+.69*t,.245,1.46+.41*t)
  tip=point(.27+.70*t,.25,1.03+.015*math.sin(t*math.pi));bone=f'Feather_{side}_S{i:02d}'
  parent=bones[1] if i<4 else bones[2]
  feather(bone,root,tip,.18,bone,parent,side,'secondary',i);flights.append((root,tip,bone,parent,i+10))
 for root,tip,bone,parent,i in flights:
  a=Vector(root);b=Vector(tip);axis=(b-a).normalized()
  for row in range(2):
   # Coverts lie on both faces; each stays rigid with its flight feather.
   for face_sg in (-1,1):
    start=a+axis*(-.065+row*.16);start.y+=face_sg*(.014+(.012 if row==0 else .004))
    end=start+axis*(.27 if row==0 else .30)
    feather(f'Covert_{side}_{i:02d}_{row}_{face_sg}',start,end,.17,bone,parent,side,'covert',i,True)
(P/'work/wings.json').write_text(json.dumps(meta,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/neutral_wings.blend'))
scene=bpy.context.scene;common.workbench_clay(scene);scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.45,.45,.45)
common.render_views(str(P/'review/layered_wings'),1.03,4.35,views=('front','back','three_quarter','left'),resolution=(1200,780))
# Every feather is a closed shell with its own rigid owner, including the back faces.
for o in bpy.data.objects:
 if o.type!='MESH' or o.name=='Body':continue
 bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_manifold for e in bm.edges),o.name;bm.free()
print('WINGS',sum(r['triangles'] for r in meta),'triangles',len(meta),'pieces')
