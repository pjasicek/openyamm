"""Fit one coherent rear-panel clearance, following its existing normal, without per-row contact jitter."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path[:0]=[str(P/'scripts'),str(P.parent/'claude_shared/gates')];import run_gates as G,reduction_common as C
cfg=json.loads((P/'gates.json').read_text());g=G.Glb(P/'export/mm6_natm.glb');rep=G.Report(cfg);meshes=G.load_meshes(g)
for m in meshes:G.configure_mesh(m,cfg,rep)
clips={n:a for n,a,s,e in g.clips()};names=['ClothBack','ClothBack1','ClothBack2','ClothBack3'];W={m.label:m.weight(['ClothBack*'])for m in meshes}
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pre_contact_finish_lod0.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene
assert np.max(abs(np.array(r.data.bones['ClothBack'].matrix_local)-g.rest[g.names['ClothBack']]))<1e-5
data={};report={}
for clip in ['Death','Hit','Running']:
 a=bpy.data.actions[clip];last=round(a.frame_range[1]);cases=[];required=[];original=[]
 for f in range(last+1):
  C.activate(clip,f/48);pose=g.pose(clips[clip],np.array([f/48]))[0]
  original.append({n:r.pose.bones[n].location.copy()for n in names})
  for n in names:pose[g.names[n]]=np.array(r.pose.bones[n].matrix)
  normal=np.array((r.pose.bones['ClothBack'].matrix@r.data.bones['ClothBack'].matrix_local.inverted()).to_3x3()@Vector((0,1,0)));normal/=np.linalg.norm(normal);rows=[];minz=1e6
  for m in meshes:
   points=m.posed(pose);_,surf,samples,_=next(row for row in m.cloth if row[0]=='ClothBack');ids=np.flatnonzero(m.regions['ClothBack']&(W[m.label]>.25));rows.append((m,points,surf,samples))
   if 'colour'in m.label:minz=min(minz,float(points[ids,2].min()))
  def evaluate(s):
   d=normal*s;d[2]=max(d[2],.0005-minz);worst=0.
   for m,points,surf,samples in rows:
    posed=points+W[m.label][:,None]*d;depth,_=G.penetration(surf.build(posed,pose),posed[samples]);worst=max(worst,depth)
   return worst,d
  best=None
  for s in np.arange(0,.081,.002):
   depth,d=evaluate(s)
   if best is None or depth<best[0]:best=(depth,s,d.copy())
   if depth<=1.1:break
  required.append(best[1]);cases.append((rows,pose,normal,minz))
  if best[0]>2:print('PANEL RESIDUAL',clip,f,best[0],best[1],flush=True)
 required=np.array(required)
 # Spread the small clearance over five samples; a local maximum preserves required contact clearance.
 periodic=clip=='Running';core=required[:-1]if periodic else required
 pad=np.pad(core,(4,4),mode='wrap'if periodic else'edge');envelope=np.maximum.reduce([pad[k:k+len(core)+4]for k in range(5)])
 envelope=np.convolve(envelope,np.array([1,4,6,4,1])/16,mode='valid')+.001
 if periodic:envelope=np.r_[envelope,envelope[0]]
 out=[];worst=0
 for f,(rows,pose,normal,minz)in enumerate(cases):
  d=normal*envelope[f];d[2]=max(d[2],.0005-minz);out.append(d)
  for m,points,surf,samples in rows:
   posed=points+W[m.label][:,None]*d;depth,_=G.penetration(surf.build(posed,pose),posed[samples]);worst=max(worst,depth)
 data[clip]={'original':original,'delta':np.array(out)};report[clip]={'max_clearance_mm':float(envelope.max()*1000),'worst_cloth_mm':worst,'max_world_step_mm':float(np.linalg.norm(np.diff(out,axis=0),axis=1).max()*1000),'samples':len(out),'clearance_m':envelope.tolist()}
 print('SMOOTH PANEL',clip,{k:v for k,v in report[clip].items()if k!='clearance_m'},flush=True)
for level in range(4):
 path=P/f'work/runtime_lod{level}.blend';bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['Rig'];sc=bpy.context.scene
 for clip,d in data.items():
  a=bpy.data.actions[clip]
  for f,(old,delta)in enumerate(zip(d['original'],d['delta'])):
   C.activate(clip,f/48)
   for n in names:r.pose.bones[n].location=old[n]
   bpy.context.view_layer.update();pb=r.pose.bones['ClothBack'];basis=pb.matrix.to_3x3()@pb.rotation_quaternion.to_matrix().inverted();pb.location+=basis.inverted()@Vector(delta)
   for n in names:r.pose.bones[n].keyframe_insert('location',frame=f)
  if clip=='Death':
   C.activate('Death',a.frame_range[1]/48);final={n:r.pose.bones[n].location.copy()for n in names}
 a=bpy.data.actions['Dead'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for f in [0,1]:
  for n,l in final.items():r.pose.bones[n].location=l;r.pose.bones[n].keyframe_insert('location',frame=f)
 C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(path))
 if level==0:bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_natm.blend'))
(P/'review/panel_clearance.json').write_text(json.dumps(report,indent=2))
