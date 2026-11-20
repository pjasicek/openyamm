"""Fit the two layered shoulder caps as rigid hinges, preserving the accepted arm and hammer motion."""
import bpy,sys,os,runpy,json,math
from pathlib import Path
import numpy as np
from mathutils import Matrix,Vector,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];S=P/'scripts';sys.path.insert(0,str(S));import armik
src=P/'work/forge_edgefit.blend';out=P/'work/forge_hinged.blend'
sys.argv=['armour_gate.py','--',str(src),'forge_hinge_masks',str(S/'armour_forge.json')];g=runpy.run_path(str(S/'armour_gate.py'),run_name='__main__');r=g['rig'];sc=bpy.context.scene
roles=sys.argv[sys.argv.index('--')+1:] if False else ['Forge_Attack','Forge_Hit','Forge_Cast']
report={}
for clip in roles:
 a=bpy.data.actions[clip];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 frames=[]
 for f in np.arange(a.frame_range[0],a.frame_range[1]+.001,1):
  sc.frame_set(int(f),subframe=float(f%1));frames.append((float(f),{b.name:b.matrix_basis.copy() for b in r.pose.bones}))
 r.animation_data.action=None
 tracks={}
 for side in 'LR':
  pn=f'B_{side}_Pauldron';cn=f'B_{side}_Clavicle';un=f'B_{side}_UpperArm';caps=['Arm_pauldron_'+side,'Arm_pauldron_lower_'+side]
  rel=r.data.bones[cn].matrix_local.inverted()@r.data.bones[pn].matrix_local
  local={n:np.array([tuple(r.data.bones[pn].matrix_local.inverted()@Vector(v)) for v in g['REST_P'][n]]) for n in caps}
  states=[(.8,0,0,0)]+[(k,dx,dz,roll) for k in (.6,.8,1.) for dx in (0,.04,.08) for dz in (0,.04) for roll in (-90,-60,-30,0,30,60,90) if (k,dx,dz,roll)!=(.8,0,0,0)]
  table=[]
  for f,snap in frames:
   for n,m in snap.items():r.pose.bones[n].matrix_basis=m
   bpy.context.view_layer.update();body=g['ev'](g['body'])[0];bt=BVHTree.FromPolygons(body.tolist(),g['BFK']);rest=r.data.bones[cn].matrix_local.to_3x3().inverted()@r.data.bones[un].matrix_local.to_3x3().col[1];posed=r.pose.bones[cn].matrix.to_3x3().inverted()@r.pose.bones[un].matrix.to_3x3().col[1];swing=rest.rotation_difference(posed);base=r.pose.bones[cn].matrix@rel
   torso=r.pose.bones['B_Spine2'].matrix.to_3x3()@r.data.bones['B_Spine2'].matrix_local.to_3x3().inverted();outward=torso@Vector((1 if side=='L' else -1,0,0));outward.z=0;outward.normalize()
   other={ob.name:g['ev'](ob)[0] for ob in g['plates'] if ob.name not in caps and g['BONE'][ob.name]!=pn};ot={n:BVHTree.FromPolygons(v.tolist(),g['pfaces'][n]) for n,v in other.items()};bounds={n:(v.min(0),v.max(0)) for n,v in other.items()};gun=g['ev'](g['gun'])[0]
   rows=[]
   for k,dx,dz,roll in states:
    q=Quaternion(swing.axis,swing.angle*k) if swing.angle>1e-6 else Quaternion();rb=rel.to_3x3();basis=(rb.inverted()@q.to_matrix()@rb).to_4x4();m=base@basis;axis=r.pose.bones[un].matrix.to_3x3().col[1].normalized();rot=Quaternion(axis,math.radians(roll)).to_matrix()@m.to_3x3();translation=m.translation.copy();m=rot.to_4x4();m.translation=translation+outward*dx+Vector((0,0,dz));dep=0;why=''
    for n in caps:
     pp=local[n]@np.array(m.to_3x3()).T+np.array(m.translation);pt=BVHTree.FromPolygons(pp.tolist(),g['pfaces'][n]);ti=BVHTree.FromPolygons(pp.tolist(),g['ifaces'][n]);lo,hi=pp.min(0),pp.max(0)
     d=g['inside_closed'](bt,pp[g['BASE_PLATE'][n]],1.2,g['HIDFK'])[0]
     d=max(d,g['inside_closed'](pt,body[g['cand'][n]])[0],g['through_depth'](ti,body[g['cand'][n]])[0],g['inside_closed'](pt,gun)[0])
     for on,tree in ot.items():
      ol,oh=bounds[on]
      if np.any(lo>oh) or np.any(hi<ol):continue
      d=max(d,g['inside_closed'](tree,pp[g['PV'][n]])[0],g['inside_closed'](pt,other[on][g['PV'][on]])[0])
     if d>dep:dep=d;why=n
    cost=1e7*max(0,dep-.0015)+1500*(dx*dx+dz*dz)+2*(k-.8)**2+.0001*roll*roll
    rows.append(dict(cost=cost,depth=dep,k=k,dx=dx,dz=dz,roll=roll,part=why,m=m,q=list(m.to_quaternion())))
    if len(rows)==1 and dep<.0015:break
   table.append(rows)
   if f%5==0:print('HINGE_FRAME',clip,side,f,{k:v for k,v in min(rows,key=lambda x:x['cost']).items() if k not in ('m','q')},flush=True)
  cost=np.array([x['cost'] for x in table[0]]);backs=[]
  for prev,rows in zip(table,table[1:]):
   qa=np.array([x['q'] for x in prev]);qb=np.array([x['q'] for x in rows]);ang=np.degrees(2*np.arccos(np.clip(np.abs(qa@qb.T),0,1)));pos=np.array([[x['dx'],x['dz']] for x in rows]);old=np.array([[x['dx'],x['dz']] for x in prev]);transition=2*ang**2+2e5*np.sum((old[:,None]-pos[None,:])**2,axis=2);choices=cost[:,None]+transition;back=choices.argmin(0);cost=choices[back,np.arange(len(rows))]+[x['cost'] for x in rows];backs.append(back)
  idx=int(cost.argmin());path=[idx]
  for back in reversed(backs):idx=int(back[idx]);path.append(idx)
  path.reverse();tracks[side]=[rows[i] for rows,i in zip(table,path)]
  report[clip+'_'+side]=[{k:v for k,v in row.items() if k not in ('m','q')} for row in tracks[side]]
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];prev={}
 for j,(f,snap) in enumerate(frames):
  sc.frame_set(int(f),subframe=f%1)
  for side in 'LR':
   n=f'B_{side}_Pauldron';armik.set_world(r,n,tracks[side][j]['m']);b=r.pose.bones[n];q=b.matrix_basis.to_quaternion()
   if side in prev and q.dot(prev[side])<0:q=-q
   b.rotation_mode='QUATERNION';b.rotation_quaternion=q;prev[side]=q.copy();b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
 print('HINGE_CLIP',clip,flush=True)
r.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(out));(P/'review/forge_hinge_fit.json').write_text(json.dumps(report,indent=2)+'\n')
for name,args in [('gates.py',[out,'forge_hinged',*roles]),('armour_gate.py',[out,'forge_hinged',S/'armour_forge.json',*roles])]:
 sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(S/name),run_name='__main__')
sys.stdout.flush();os._exit(0)
