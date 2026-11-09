"""Resolve the remaining measured attachment and rear-panel contacts on the selected runtime assets."""
import bpy,sys,json,math,shutil,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path[:0]=[str(P/'scripts'),str(P.parent/'claude_shared/gates')];import run_gates as G,reduction_common as C
cfg=json.loads((P/'gates.json').read_text());g=G.Glb(P/'export/mm6_natm.glb');rep=G.Report(cfg);props=G.load_props(cfg,P,g,rep);meshes=G.load_meshes(g);clips={n:(a,s,e)for n,a,s,e in g.clips()};oldreport=json.loads((P/'review/runtime_gates/gates.json').read_text());records={'props':[],'cloth':{}}
for m in meshes:G.configure_mesh(m,cfg,rep)
# Resolve only the audited buckler samples, against the entire body surface (straps included).
prop=props[1];prop_delta={}
for level in range(4):
 pm=prop['meshes'][level];vertices=G.transform(np.linalg.inv(G.C),pm.rest);base=vertices.copy();rows=[x for x in oldreport['gates']if x['gate']=='prop_body_penetration_mm'and x['region']=='buckler'and x['status']=='FAIL'and x['lod'].endswith(str(level))]
 cases=[]
 for row in rows:
  m=next(m for m in meshes if m.label==row['lod']);pose=g.pose(clips[row['clip']][0],np.array([row['time_s']]))[0];points=m.posed(pose);surface=G.Surface(m,m.solid).build(points);matrix=pose[g.names['Buckler']];cases.append((surface,matrix))
 for iteration in range(10):
  worst=0
  for surf,M in cases:
   points=G.transform(M,vertices);ds,faces=surf.signed(points)
   for i in np.flatnonzero(ds<-.0007):
    q,n,fi,d=surf.tree.find_nearest(Vector(points[i]));corr=np.array(n)*(d+.0008);vertices[i]+=np.linalg.solve(M[:3,:3],corr);worst=max(worst,d)
  if worst<.0008:break
 prop_delta[level]=(base,vertices);records['props'].append({'lod':level,'max_brush_mm':float(np.linalg.norm(vertices-base,axis=1).max()*1000)})
# Four existing cloth controls: root translation plus the three row offsets.
names=['ClothBack','ClothBack1','ClothBack2','ClothBack3'];weights={}
for m in meshes:
 w=np.column_stack([m.weight([n])for n in names]);w[:,0]=w.sum(1);weights[m.label]=w
cloth_deltas={}
for clip in ['Death','Hit','Running']:
 a,start,end=clips[clip];last=round(end*48);out=[];previous=np.zeros((4,3))
 for f in range(last+1):
  pose=g.pose(a,np.array([f/48]))[0];cases=[]
  for m in meshes:
   points=m.posed(pose);name,surface,samples,cont=next(row for row in m.cloth if row[0]=='ClothBack');W=weights[m.label];skin=None
   cases.append((m,points,surface,samples,W,skin))
  delta=previous*.75
  for iteration in range(15):
   worst=0
   for m,points,surf,samples,W,skin in cases:
    posed=points+W@delta;surf.build(posed,pose);ids=np.flatnonzero(samples);ds,faces=surf.signed(posed[ids])
    for j in np.flatnonzero(ds<-.0008):
     p=posed[ids[j]];q,n,fi,d=surf.tree.find_nearest(Vector(p))
     if fi>=len(surf.faces):continue
     tri=m.weld_first[surf.faces[fi]];v=posed[tri];A=np.column_stack([v[1]-v[0],v[2]-v[0]]);uv=np.linalg.lstsq(A,np.array(q)-v[0],rcond=None)[0];b=np.array([1-uv.sum(),uv[0],uv[1]]);w=b@W[tri];den=w@w
     if den>1e-5:delta+=np.outer(w,-np.array(n)*(d+.0010))*.65/den;worst=max(worst,d)
    # Floor constraints accompany the shared cloth-volume collision measurement.
    ids=np.flatnonzero(m.regions['ClothBack']&(W[:,0]>.25)&(m.rest[:,2]<.93))
    for i in ids:
     deficit=.0005-(points[i,2]+W[i]@delta[:,2])
     if deficit>0:delta[:,2]+=W[i]*deficit/(W[i]@W[i]);worst=max(worst,deficit)
   lengths=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,.045/np.maximum(lengths,1e-9))[:,None]
   if worst<.001:break
  out.append(delta.copy());previous=delta.copy()
 cloth_deltas[clip]=np.array(out);records['cloth'][clip]={'max_control_shift_mm':float(np.linalg.norm(out,axis=2).max()*1000)}
 print('CLOTH CONTACT',clip,records['cloth'][clip],flush=True)
(P/'review/cloth_control_deltas.json').write_text(json.dumps({k:v.tolist()for k,v in cloth_deltas.items()}))
# Apply the same action correction to every LOD and retain the current editable sources.
for level in range(4):
 path=P/f'work/runtime_lod{level}.blend';backup=P/f'work/pre_contact_finish_lod{level}.blend'
 if not backup.exists():shutil.copy2(path,backup)
 bpy.ops.wm.open_mainfile(filepath=str(backup));r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
 C.reset();ob=bpy.data.objects['BucklerMesh'];rest=r.data.bones['Buckler'].matrix_local;inv=rest.inverted();base,new=prop_delta[level];kd=KDTree(len(base))
 for i,p in enumerate(base):kd.insert(Vector(p),i)
 kd.balance()
 for v in ob.data.vertices:
  p=inv@v.co;q,i,d=kd.find(p)
  if d<.00002:v.co+=rest.to_3x3()@Vector(new[i]-base[i])
 # Exact contact with the detailed handle, including its non-circular wrapped profile.
 if level<2:
  C.activate('Standing',0);me=body.data;ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();posed=np.array([v.co[:]for v in em.vertices]);ev.to_mesh_clear();M=np.array(r.pose.bones['Spear'].matrix);local=G.transform(G.C@np.linalg.inv(M),posed);me.calc_loop_triangles();tri=np.array([t.vertices[:]for t in me.loop_triangles]);pattern='B_R_Finger2'if level==0 else'B_R_Finger4';w=np.array([sum(vg.weight for vg in v.groups if body.vertex_groups[vg.group].name.startswith(pattern))for v in me.vertices]);bary=np.array([[1,0,0],[0,1,0],[0,0,1],[.5,.5,0],[0,.5,.5],[.5,0,.5],[1/3]*3]);mask=np.any(w[tri]>.3,axis=1);tt=tri[mask];pts=np.einsum('sk,tkj->tsj',bary,local[tt]);ww=np.einsum('sk,tk->ts',bary,w[tt]);surf=props[0]['grip_surfaces']['R'][level];best=None
  for j,k in np.argwhere(ww>.3):
   q,n,fi,d=surf.tree.find_nearest(Vector(pts[j,k]))
   if best is None or d<best[0]:best=(d,j,k,np.array(q))
  d,j,k,q=best;sample=pts[j,k];target=q+(sample-q)/d*.0011;corr=G.C[:3,:3].T@(target-sample);world=M[:3,:3]@corr
  for vi,b in zip(tt[j],bary[k]):
   if b==0:continue
   A=sum((np.array(r.pose.bones[body.vertex_groups[x.group].name].matrix@r.data.bones[body.vertex_groups[x.group].name].matrix_local.inverted())*x.weight for x in me.vertices[vi].groups),np.zeros((4,4)));me.vertices[vi].co+=Vector(np.linalg.solve(A[:3,:3],world*b/(bary[k]@bary[k])))
 for clip,rows in cloth_deltas.items():
  a=bpy.data.actions[clip];locations=[]
  for f,delta in enumerate(rows):
   C.activate(clip,f/48);r.animation_data.action=None;loc={}
   for i,name in enumerate(names):
    pb=r.pose.bones[name];worldbasis=pb.matrix.to_3x3()@pb.rotation_quaternion.to_matrix().inverted();pb.location+=worldbasis.inverted()@Vector(delta[i]);bpy.context.view_layer.update();loc[name]=pb.location.copy()
   locations.append(loc)
  r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
  for f,loc in enumerate(locations):
   for name,l in loc.items():pb=r.pose.bones[name];pb.location=l;pb.keyframe_insert('location',frame=f)
  if clip=='Death':
   death_last=locations[-1]
 a=bpy.data.actions['Dead'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for f in [0,1]:
  for name,l in death_last.items():pb=r.pose.bones[name];pb.location=l;pb.keyframe_insert('location',frame=f)
 C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(path))
 if level==0:bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_natm.blend'))
(P/'review/contact_finish.json').write_text(json.dumps(records,indent=2));print('CONTACT_FINISH',records,flush=True)
