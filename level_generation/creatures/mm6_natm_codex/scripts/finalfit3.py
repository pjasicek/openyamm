"""Fit far-LOD outline vertices to eight high-resolution silhouette constraints; preserve rig weights and contacts."""
import bpy,sys,json,math,subprocess,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import reduction_common as C
from reduction_render import render

def deform(level,field):
 r=bpy.data.objects['Rig'];C.activate('Standing',0);ppm=700/1.7129090557573363;total=0;maxmove=0
 for name in ['Body']:
  o=bpy.data.objects[name];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pos=np.array([v.co[:]for v in me.vertices]);norm=np.array([f.normal[:]for f in me.polygons]);edges={}
  for f in me.polygons:
   for a,b in zip(f.vertices,list(f.vertices[1:])+[f.vertices[0]]):edges.setdefault(tuple(sorted((a,b))),[]).append(f.index)
  ev.to_mesh_clear();count=len(pos);At=np.zeros((count,3,3));rhs=np.zeros((count,3));gn={g.index:g.name for g in o.vertex_groups};frozen=np.zeros(count,bool)
  if name=='Body':
   pv=np.array([x.value for x in o.data.attributes['piece'].data]);frozen=np.isin(pv,[1,10])|np.array([v.co.z<.012 for v in o.data.vertices]);frozen|=np.array([sum(g.weight for g in v.groups if 'Hand'in gn[g.group]or'Finger'in gn[g.group])>.3 for v in o.data.vertices])
  else:
   inv=r.data.bones['Spear'if name=='SpearMesh'else'Buckler'].matrix_local.inverted();local=np.array([tuple(inv@v.co)for v in o.data.vertices]);frozen=abs(local[:,2])<.15 if name=='SpearMesh'else local[:,1]>.021
  for view in range(8):
   angle=view*math.pi/4;horizontal=np.array([math.cos(angle),math.sin(angle),0.]);direction=np.array([math.sin(angle),-math.cos(angle),0.]);vertical=np.array([0.,0,1.]);basis=np.outer(horizontal,horizontal)+np.outer(vertical,vertical);nearest=field[f'nearest_{view}'];candidate=field[f'candidate_{view}'];face=norm@direction
   for (a,b),faces in edges.items():
    if len(faces)==2 and face[faces[0]]*face[faces[1]]>=0:continue
    for t in [.15,.5,.85]:
     v=pos[a]*(1-t)+pos[b]*t;x=410+v@horizontal*ppm;y=410-(v[2]-.85)*ppm;ix,iy=round(x),round(y)
     if not(0<=ix<820 and 0<=iy<820)or candidate[iy,ix]>1.5:continue
     ny,nx=nearest[:,iy,ix];dx,dy=float(nx)-x,float(ny)-y
     if math.hypot(dx,dy)>35:continue
     delta=(horizontal*dx-vertical*dy)/ppm
     for vi,w in [(a,1-t),(b,t)]:At[vi]+=basis*w*w;rhs[vi]+=delta*w
  delta=np.linalg.solve(At+np.eye(3)[None]*.18,rhs[...,None])[...,0]*.30;length=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,.008/np.maximum(length,1e-9))[:,None];delta[frozen]=0
  for v,d in zip(o.data.vertices,delta):
   if np.linalg.norm(d)<1e-8:continue
   M=np.zeros((3,3));weight=0
   for g in v.groups:
    bone=gn[g.group]
    if bone not in r.data.bones:continue
    matrix=r.pose.bones[bone].matrix@r.data.bones[bone].matrix_local.inverted();M+=np.array(matrix.to_3x3())*g.weight;weight+=g.weight
   assert weight>.99;v.co+=Vector(np.linalg.solve(M,d));total+=1;maxmove=max(maxmove,float(np.linalg.norm(d)))
  o.data.update()
 C.reset();return total,maxmove

current=P/'work/lod3_continuous.blend';tex=P/'work/reduction/lod3_continuous';curve=[]
for step in range(1,13):
 high=P/f'review/reduction/finalfit3_{step-1}_high';render(current,high,tex,700)
 field=P/'work/finalfit3_field.npz';subprocess.run(['/usr/bin/python3','-B',str(P/'scripts/field_high.py'),str(P/'review/reduction/reference700'),str(high),str(field)],check=True)
 bpy.ops.wm.open_mainfile(filepath=str(current));moved,maximum=deform(3,np.load(field));current=P/f'work/lod3_finalfit{step}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(current))
 out=P/f'review/reduction/finalfit3_{step}';render(current,out,tex,88);v=json.loads(subprocess.check_output(['/usr/bin/python3','-B',str(P/'scripts/reduction_metrics.py'),str(P/'review/reduction/lod3_reference'),str(out)],text=True));rr=list(v['views'].values());uu=[(x['reference_pixels']+x['candidate_pixels'])/(1+x['iou'])for x in rr];pooled=sum(x['iou']*u for x,u in zip(rr,uu))/sum(uu);curve.append({'step':step,'pooled_iou':pooled,'visual':v});(P/'review/reduction/finalfit3_curve.json').write_text(json.dumps(curve,indent=2));print('FINALFIT3',step,pooled,flush=True)
 if pooled>=.972:break
