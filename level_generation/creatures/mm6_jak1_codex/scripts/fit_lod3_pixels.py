"""Fit the distant mesh's visible edges to the eight-view reference, keeping hands and soles fixed."""
import bpy,sys,json,math,subprocess,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_rebake as red
W=red.W;R=red.R;selected=json.loads((R/'selection.json').read_text());maps=P/selected['maps'];fields=np.load(W/'outline_distance88.npy')
bpy.ops.wm.open_mainfile(filepath=str(W/'lod3_material02.blend'));body=bpy.data.objects['Jackalman'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene;a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(0)
matrices={g.index:np.array(rig.pose.bones[g.name].matrix@rig.data.bones[g.name].matrix_local.inverted())for g in body.vertex_groups if g.name in rig.pose.bones};names={g.index:g.name for g in body.vertex_groups}
transforms=[];fixed=[]
for v in body.data.vertices:
 pairs=[(matrices[g.group],g.weight)for g in v.groups if g.group in matrices];total=sum(w for m,w in pairs);transforms.append(sum(m*w/total for m,w in pairs));fixed.append(any(g.weight>.2 and ('Hand'in names[g.group]or'Finger'in names[g.group]or names[g.group]=='Staff')for g in v.groups))
transforms=np.array(transforms);inverse=np.linalg.inv(transforms);co=np.einsum('nij,nj->ni',transforms,np.c_[[v.co[:]for v in body.data.vertices],np.ones(len(body.data.vertices))])[:,:3];hands=np.array(fixed);staff=np.array([any(g.weight>.5 and names[g.group]=='Staff'for g in v.groups)for v in body.data.vertices]);soles=co[:,2]<.015;fixed=staff;original=co.copy();body.data.calc_loop_triangles();faces=np.array([tuple(f.vertices)for f in body.data.loop_triangles]);edge_faces={}
for i,f in enumerate(faces):
 for a,b in zip(f,np.roll(f,-1)):edge_faces.setdefault(tuple(sorted((int(a),int(b)))),[]).append(i)
edges=np.array(list(edge_faces));first=np.array([v[0]for v in edge_faces.values()]);last=np.array([v[-1]for v in edge_faces.values()]);boundary=first==last
height=json.loads((P/'review/posture.json').read_text())['Standing']['body_height_m'];center=np.array([0,0,height/2+.003]);cameras=[]
for i in range(8):
 d=Vector((math.sin(i*math.pi/4),-math.cos(i*math.pi/4),.05)).normalized();q=(-d).to_track_quat('-Z','Y');cameras.append((np.array(d),np.array(q@Vector((1,0,0))),np.array(q@Vector((0,1,0)))))
def sample(field,xy):
 x,y=xy;x=max(0,min(998,x));y=max(0,min(998,y));ix,iy=int(x),int(y);fx,fy=x-ix,y-iy;return (field[iy,ix]*(1-fx)+field[iy,ix+1]*fx)*(1-fy)+(field[iy+1,ix]*(1-fx)+field[iy+1,ix+1]*fx)*fy
curve=[];best=None
for iteration in range(61):
 if iteration in [0,5,10,20,40,60]:
  for v,pos,inv in zip(body.data.vertices,co,inverse):v.co=(inv@np.r_[pos,1])[:3]
  body.data.update();tag=f'lod3_pixel{iteration:02d}';red.render(body,rig,tag,maps,88);metric=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/reduction_images.py'),'compare',str(R),'lod3_reference',tag],text=True));path=W/f'{tag}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));row={'level':3,'iteration':iteration,'body_triangles':sum(f.material_index!=2 for f in body.data.loop_triangles),'staff_triangles':sum(f.material_index==2 for f in body.data.loop_triangles),'pixels':88,'blend':str(path.relative_to(P)),**metric,'visual_pass':metric['pooled_iou']>=.97,'max_displacement_m':float(np.linalg.norm(co-original,axis=1).max())};curve.append(row);(R/'lod3_pixel_curve.json').write_text(json.dumps(curve,indent=2));print('OUTLINE FIT',iteration,metric['pooled_iou'],row['max_displacement_m'],flush=True)
  if best is None or row['pooled_iou']>best['pooled_iou']:best=row
 if iteration==60:break
 normals=np.cross(co[faces[:,1]]-co[faces[:,0]],co[faces[:,2]]-co[faces[:,0]]);normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12);tree=BVHTree.FromPolygons(co.tolist(),faces.tolist(),all_triangles=True);forces=np.zeros_like(co);weights=np.zeros(len(co))
 for view,(direction,right,up)in enumerate(cameras):
  front=normals@direction;take=boundary|(front[first]*front[last]<=0)
  for ia,ib in edges[take]:
   if fixed[ia]and fixed[ib]:continue
   for t in [.25,.5,.75]:
    point=co[ia]*(1-t)+co[ib]*t
    if tree.ray_cast(Vector(point+direction*.0001),Vector(direction),10)[0]is not None:continue
    p=point-center;xy=np.array([499.5+p@right*88/height,499.5-p@up*88/height]);distance,gx,gy=sample(fields[view],xy)
    if abs(distance)>1.5:continue
    gradient=right*gx-up*gy;force=-np.clip(distance,-1.5,1.5)*height/88*gradient/max(gx*gx+gy*gy,.25)
    for index,w in [(ia,1-t),(ib,t)]:forces[index]+=force*w;weights[index]+=w
 movement=forces/np.maximum(weights[:,None],1)*.45;size=np.linalg.norm(movement,axis=1);movement*=np.minimum(1,.003/np.maximum(size,1e-12))[:,None];movement[fixed]=0;co+=movement
 displacement=co-original;length=np.linalg.norm(displacement,axis=1);co=original+displacement*np.minimum(1,np.where(hands,.002,.035)/np.maximum(length,1e-12))[:,None]
 co[soles,2]=original[soles,2]
 assert np.array_equal(co[fixed],original[fixed])
(R/'lod3_pixel_selection.json').write_text(json.dumps([best],indent=2));assert best['visual_pass'],best['pooled_iou']
