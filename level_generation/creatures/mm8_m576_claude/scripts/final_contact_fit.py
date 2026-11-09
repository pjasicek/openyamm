"""Use the exported sole selectors for the running heading and preserve any remaining LOD grip samples."""
import bpy,runpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,kdtree
P=Path(__file__).resolve().parents[1];g=runpy.run_path(str(P.parent/'claude_shared/gates/run_gates.py'),run_name='probe');a=g['Glb'](P/'export/mm8_m576.glb');cfg=json.loads((P/'gates.json').read_text());r=g['Report'](cfg);m=g['load_meshes'](a)[0];g['configure_mesh'](m,cfg,r)
checkpoint=P/'work/master_before_sole_heading.blend'
if not checkpoint.exists():
 import shutil;shutil.copyfile(P/'work/master_textured_uv.blend1',checkpoint)
bpy.ops.wm.open_mainfile(filepath=str(checkpoint));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;sys.path.insert(0,str(P/'scripts'));import armik
tree=kdtree.KDTree(len(body.data.vertices))
for v in body.data.vertices:tree.insert(body.matrix_world@v.co,v.index)
tree.balance();soles={}
for side,(ids,heel,toe) in m.feet.items():
 soles[side]=tuple(np.array([tree.find(Vector(m.rest[i]))[1] for i in subset]) for subset in (ids,heel,toe))
def verts():
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=np.array([tuple(body.matrix_world@x.co) for x in me.vertices]);ev.to_mesh_clear();return v
# The sole must belong to the foot/toes, not the calf. Blend the correction out before the ankle.
groups=[x.name for x in body.vertex_groups];changed=[]
for v in body.data.vertices:
 for side in 'LR':
  foot=body.vertex_groups[f'B_{side}_Foot'];calf=body.vertex_groups[f'B_{side}_Calf'];weights={groups[e.group]:e.weight for e in v.groups};share=weights.get(foot.name,0)+weights.get(f'B_{side}_Toe0',0)
  moved=weights.get(calf.name,0)*float(np.clip((.08-v.co.z)/.04,0,1))
  if share>.3 and moved>1e-7:
   foot.add([v.index],weights.get(foot.name,0)+moved,'REPLACE');calf.add([v.index],weights[calf.name]-moved,'REPLACE');changed.append((v.index,moved))
print('HEEL WEIGHTS',len(changed),max(x[1] for x in changed),flush=True)
heading={}
for name in ('Standing','Walking','Running','Attack','Hit','Fidget','Death'):
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];frames=np.arange(0,float(act.frame_range[1])+.001,.25);rows=[];before=[];after=[];snapshots=[]
 for f in frames:
  sc.frame_set(int(f),subframe=float(f%1));snapshots.append({b.name:b.matrix_basis.copy() for b in rig.pose.bones})
 for f,snap in zip(frames,snapshots):
  rig.animation_data.action=None
  for n,M in snap.items():rig.pose.bones[n].matrix_basis=M
  bpy.context.view_layer.update()
  if name!='Death':
   for it in range(2):
    for side,(ids,heel,toe) in soles.items():
     V=verts();M=armik.W(rig,f'B_{side}_Foot');pivot=M.translation.copy()
     if name in ('Standing','Attack','Hit','Fidget'):
      patch=V[ids];_,_,vv=np.linalg.svd(patch-patch.mean(0),full_matrices=False);normal=Vector(vv[-1]);normal=normal if normal.z>=0 else -normal;M=normal.rotation_difference(Vector((0,0,1))).to_matrix().to_4x4()@M;M.translation=pivot;armik.set_world(rig,f'B_{side}_Foot',M);V=verts()
     d=Vector(V[toe].mean(0)-V[heel].mean(0));d.z=0;goal=Vector((0,-1,0));yaw=np.arctan2(d.cross(goal).z,d.dot(goal))
     if it==0:before.append(float(abs(yaw)*180/np.pi))
     M=armik.W(rig,f'B_{side}_Foot');M=Matrix.Rotation(float(yaw),4,'Z')@M;M.translation=pivot;armik.set_world(rig,f'B_{side}_Foot',M)
   V=verts()
   for side,(ids,heel,toe) in soles.items():
    d=Vector(V[toe].mean(0)-V[heel].mean(0));d.z=0;after.append(float(d.angle(Vector((0,-1,0)))*180/np.pi))
  rows.append({f'B_{s}_Foot':rig.pose.bones[f'B_{s}_Foot'].rotation_quaternion.copy() for s in 'LR'})
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];prev={}
 for f,row in zip(frames,rows):
  for n,q in row.items():
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=float(f))
 heading[name]={'before_max_degrees':max(before,default=0),'after_max_degrees':max(after,default=0)};print('SOLE HEADING',name,heading[name],flush=True);assert max(after,default=0)<1
(P/'review/running_sole_heading.json').write_text(json.dumps({'clips':heading,'weight_corrections':len(changed),'maximum_calf_weight_transferred':max(x[1] for x in changed),'selector':'Exported GLB welded sole and heel/toe indices'},indent=2)+'\n')
# Collect the LOD hand triangles that enter the shaft, then retain their closest authored vertices.
prop=g['load_props'](cfg,P,a,r)[0];lod=g['load_meshes'](a)[3];g['configure_mesh'](lod,cfg,r);stand=next(c for n,c,s,e in a.clips() if n=='Standing');pose=a.pose(stand,np.array([0.]))[0];V=lod.posed(pose);tris,bary,groups,signature=g['grip_points'](lod,'L',cfg);samples=np.einsum('sk,tkj->tsj',bary,V[tris]).reshape(-1,3);local=g['transform'](g['C']@np.linalg.inv(pose[a.names['Trident']]),samples);distances,_=prop['solid_surfaces'][3].signed(local);bad=distances.reshape(-1,len(bary)).min(1)<-.0025;badverts=np.unique(tris[bad]);selected=[]
for i in badverts:
 _,j,dist=tree.find(Vector(lod.rest[i]));selected.append(list(body.matrix_world@body.data.vertices[j].co))
print('LOD GRIP BAD FACES',int(bad.sum()),'AUTHOR CONTACTS',len(selected),flush=True)
(P/'work/lod_extra_grip_points.json').write_text(json.dumps(selected,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/clean_foot_weights.blend'))
sys.argv=['contact_fix.py','--',str(P/'work/clean_foot_weights.blend'),str(P/'work/master_textured_uv.blend')];runpy.run_path(str(P/'scripts/contact_fix.py'),run_name='__main__')
sys.argv=['export_runtime.py'];runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
