"""Fit the distant mesh's visible edges to the eight-view reference, keeping hands and soles fixed."""
import bpy,sys,json,math,subprocess,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_rebake as red
W=red.W;R=red.R;selected=json.loads((R/'selection.json').read_text());maps=P/selected['maps'];fields=np.load(W/'outline_distance.npy')
bpy.ops.wm.open_mainfile(filepath=str(W/'lod3_material02.blend'));body=bpy.data.objects['Jackalman'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene;a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(0)
matrices={g.index:np.array(rig.pose.bones[g.name].matrix@rig.data.bones[g.name].matrix_local.inverted())for g in body.vertex_groups if g.name in rig.pose.bones};names={g.index:g.name for g in body.vertex_groups}
transforms=[];fixed=[]
for v in body.data.vertices:
 pairs=[(matrices[g.group],g.weight)for g in v.groups if g.group in matrices];total=sum(w for m,w in pairs);transforms.append(sum(m*w/total for m,w in pairs));fixed.append(any(g.weight>.2 and ('Hand'in names[g.group]or'Finger'in names[g.group]or names[g.group]=='Staff')for g in v.groups))
transforms=np.array(transforms);inverse=np.linalg.inv(transforms);co=np.einsum('nij,nj->ni',transforms,np.c_[[v.co[:]for v in body.data.vertices],np.ones(len(body.data.vertices))])[:,:3];fixed=np.array(fixed)|(co[:,2]<.015);original=co.copy();body.data.calc_loop_triangles();faces=np.array([tuple(f.vertices)for f in body.data.loop_triangles]);edge_faces={}
for i,f in enumerate(faces):
 for a,b in zip(f,np.roll(f,-1)):edge_faces.setdefault(tuple(sorted((int(a),int(b)))),[]).append(i)
edges=np.array(list(edge_faces));first=np.array([v[0]for v in edge_faces.values()]);last=np.array([v[-1]for v in edge_faces.values()]);boundary=first==last
height=json.loads((P/'review/posture.json').read_text())['Standing']['body_height_m'];center=np.array([0,0,height/2+.003]);cameras=[]
for i in range(8):
 d=Vector((math.sin(i*math.pi/4),-math.cos(i*math.pi/4),.05)).normalized();q=(-d).to_track_quat('-Z','Y');cameras.append((np.array(d),np.array(q@Vector((1,0,0))),np.array(q@Vector((0,1,0)))))
def sample(field,xy):
 x,y=xy;x=max(0,min(998,x));y=max(0,min(998,y));ix,iy=int(x),int(y);fx,fy=x-ix,y-iy;return (field[iy,ix]*(1-fx)+field[iy,ix+1]*fx)*(1-fy)+(field[iy+1,ix]*(1-fx)+field[iy+1,ix+1]*fx)*fy

np.savez(W/"lod3_raster_input.npz",co=co,faces=faces,inverse=inverse,fixed=fixed,height=height,cameras=np.array(cameras),center=center)
print("RASTER INPUT",len(co),len(faces),flush=True)
