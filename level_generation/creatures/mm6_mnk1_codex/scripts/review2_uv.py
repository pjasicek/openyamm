"""Continuous metric cloth mapping; clip geometry at mirrored atlas tile boundaries."""
import bpy,bmesh,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/animation_finish.blend'))
b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];sc=bpy.context.scene;me=b.data
r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0)
# Relax the original elbow transition in the covered pose, preserving the new hem rings.
me.calc_loop_triangles();tags=[f.value for f in me.attributes['cuff'].data];pieces=[v.value for v in me.attributes['piece'].data]
fixed=set(i for f in me.polygons if tags[f.index] for i in f.vertices);adj=[[] for v in me.vertices]
for e in me.edges:
 a,z=e.vertices;adj[a].append(z);adj[z].append(a)
matrices={g.index:r.pose.bones[g.name].matrix@r.data.bones[g.name].matrix_local.inverted() for g in b.vertex_groups if g.name in r.data.bones}
M=[];P=[];smooth=[]
for v in me.vertices:
 mat=sum((matrices[g.group]*g.weight for g in v.groups),Matrix(((0,0,0,0),)*4));M.append(mat);P.append(mat@v.co)
 if pieces[v.index]!=0 or v.index in fixed or abs(v.co.x+.006)<.22:continue
 sd='L' if v.co.x>0 else 'R';el=r.data.bones[f'B_{sd}_Forearm'].head_local;d=r.data.bones[f'B_{sd}_Hand'].head_local-el;t=(v.co-el).dot(d)/d.length_squared
 if -.65<t<.10:smooth.append((v.index,min(1,(t+.65)/.25)))
for _ in range(7):
 old=[v.copy() for v in P]
 for i,amount in smooth:
  if adj[i]:P[i]=old[i].lerp(sum((old[j] for j in adj[i]),Vector())/len(adj[i]),.45*amount)
for i,_ in smooth:me.vertices[i].co=M[i].inverted()@P[i]
me.update();bpy.context.view_layer.update()
ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();world=[v.co.copy() for v in em.vertices];ev.to_mesh_clear()
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table();piece=bm.verts.layers.int['piece'];cuff=bm.faces.layers.int['cuff'];uv=bm.loops.layers.uv['UVMap'];deform=bm.verts.layers.deform.verify()
# Original torso samples define 617 px/m. The 64px torso cloth island contains the same fine woven yarn.
density=617.;size=64.;center=np.array([1803.,604.]);selected=[]
for face in list(bm.faces):
 if not all(v[piece]==0 for v in face.verts):continue
 if face[cuff] or all(abs(v.co.x+.006)>.22 for v in face.verts):selected.append(face)
# Triangulate before clipping: positions and skin weights interpolate along the same exported surface.
bmesh.ops.triangulate(bm,faces=selected);selected=[f for f in bm.faces if all(v[piece]==0 for v in f.verts) and (f[cuff] or all(abs(v.co.x+.006)>.22 for v in f.verts))]
created=[];source_area=0;new_area=0
for face in selected:
 verts=list(face.verts);P=np.array([world[v.index] for v in verts]);C=np.array([v.co[:] for v in verts]);weights=[dict(v[deform]) for v in verts]
 area=np.linalg.norm(np.cross(C[1]-C[0],C[2]-C[0]))/2
 if area<1e-12:continue
 source_area+=area
 # Use cylindrical coordinates on the new forearm cloth; tangent-plane coordinates on generated elbow folds.
 if face[cuff]==1:
  sd='L' if C[:,0].mean()>0 else 'R';el=np.array(r.pose.bones[f'B_{sd}_Forearm'].head);w=np.array(r.pose.bones[f'B_{sd}_Hand'].head);axis=(w-el);axis/=np.linalg.norm(axis)
  z=np.array([0.,0.,1.]);side=np.cross(axis,z);delta=P-el;theta=np.arctan2(delta@z+.016,-delta[:,1])
  theta=np.unwrap(theta);U=np.stack([theta*.086,(P-el)@axis],1)*density
 else:
  normal=np.cross(P[1]-P[0],P[2]-P[0]);normal/=max(np.linalg.norm(normal),1e-12);major=int(np.argmax(abs(normal)))
  # Each cardinal projection is anchored in world coordinates so adjacent patches do not stamp one motif.
  ex=np.eye(3)[(major+1)%3];ex-=normal*np.dot(ex,normal);ex/=np.linalg.norm(ex);ey=np.cross(normal,ex)
  U=np.stack([P@ex,P@ey],1)*density
 if face[cuff]!=1:
  local=U-U.mean(0);span=np.ptp(local,axis=0);scale=min(1,(size-4)/max(span))
  local*=scale
  # The fine irregular wool patch avoids a per-face stamped motif; each facet retains its metric aspect ratio.
  for loop,co2 in zip(face.loops,local):
   pixel=center+co2;loop[uv].uv=(pixel[0]/2048,1-pixel[1]/2048)
  face[cuff]=face[cuff] or 3;new_area+=area
  continue
 lo=np.floor(U.min(0)/size).astype(int);hi=np.floor(U.max(0)/size).astype(int)
 def clip(poly,axis,bound,keep_greater):
  result=[]
  for prev,cur in zip(poly[-1:]+poly[:-1],poly):
   a=prev[0][axis]-bound;z=cur[0][axis]-bound;ia=a>=-1e-9 if keep_greater else a<=1e-9;ib=z>=-1e-9 if keep_greater else z<=1e-9
   if ia!=ib:
    t=a/(a-z);result.append((prev[0]+(cur[0]-prev[0])*t,prev[1]+(cur[1]-prev[1])*t))
   if ib:result.append(cur)
  return result
 for ix in range(lo[0],hi[0]+1):
  for iy in range(lo[1],hi[1]+1):
   poly=[(U[i],np.eye(3)[i]) for i in range(3)]
   for ax,k in [(0,ix),(1,iy)]:
    poly=clip(poly,ax,k*size,True) if poly else [];poly=clip(poly,ax,(k+1)*size,False) if poly else []
   if len(poly)<3:continue
   # Reject duplicate/zero-area clipping corners before creating a face.
   clean=[]
   for point in poly:
    if not clean or np.linalg.norm(point[1]-clean[-1][1])>1e-7:clean.append(point)
   if len(clean)>2 and np.linalg.norm(clean[0][1]-clean[-1][1])<1e-7:clean.pop()
   if len(clean)<3:continue
   coords=np.array([bary@C for _,bary in clean]);ar=sum(np.linalg.norm(np.cross(coords[i]-coords[0],coords[i+1]-coords[0]))/2 for i in range(1,len(coords)-1))
   if ar<1e-12:continue
   new_area+=ar;vv=[]
   for _,bary in clean:
    v=bm.verts.new(bary@C);v[piece]=0;blend={}
    for coef,ws in zip(bary,weights):
     for group,weight in ws.items():blend[group]=blend.get(group,0)+float(coef)*weight
    blend=sorted(blend.items(),key=lambda q:q[1],reverse=True)[:8];total=sum(w for _,w in blend)
    for group,weight in blend:
     if weight>1e-8:v[deform][group]=weight/total
    vv.append(v)
   nf=bm.faces.new(vv);nf.smooth=True;nf[cuff]=face[cuff] or 3;created.append(nf)
   for loop,(coord,_) in zip(nf.loops,clean):
    loc=(coord-np.array([ix,iy])*size)/size
    if ix%2:loc[0]=1-loc[0]
    if iy%2:loc[1]=1-loc[1]
    pixel=center+(loc-.5)*size;loop[uv].uv=(pixel[0]/2048,1-pixel[1]/2048)
 bmesh.ops.delete(bm,geom=[face],context='FACES_ONLY')
assert abs(new_area-source_area)<1e-6,(source_area,new_area)
# Shared seam vertices keep normals continuous; only UV corners remain split.
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
loose=[v for v in bm.verts if not v.link_faces]
if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
(p/'work/review2_uv_mapping.json').write_text(json.dumps({'reference_density_px_m':density,'cloth_patch_center_px':center.tolist(),'cloth_patch_width_px':size,'source_area_m2':source_area,'mapped_area_m2':new_area,'original_triangles_mapped':len(selected),'tiled_faces':len(created),'method':'Continuous cylindrical outer cuffs and metric elbow tangent projections; mirrored atlas tiles clipped at their geometric boundaries.'},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/animation_finish.blend'))
