"""All-frame deformation, rigid-axe and anatomical-contact gates on the fitted rig."""
import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
blend=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'work/rig_v6.blend'
bpy.ops.wm.open_mainfile(filepath=str(P/blend));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];axe=bpy.data.objects['AxeMesh'];me=body.data
rest=np.array([tuple(v.co) for v in me.vertices]);W=np.zeros((len(rest),len(body.vertex_groups)));names=[g.name for g in body.vertex_groups]
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
def w(s,keys):return W[:,[i for i,n in enumerate(names) if n.startswith('B_'+s+'_') and any(k in n for k in keys)]].sum(1)
E=np.array([tuple(e.vertices) for e in me.edges]);rl=np.linalg.norm(rest[E[:,0]]-rest[E[:,1]],axis=1);faces=[tuple(p.vertices) for p in me.polygons];piece=np.array([a.value for a in me.attributes['piece'].data]);lab=np.array([a.value for a in me.attributes['finger'].data])
parts={};fl={};em={}
for s in 'RL':
 arm=w(s,['UpperArm','Forearm','Hand','Finger','Clavicle']);hand=w(s,['Hand','Finger']);fore=w(s,['Forearm']);skinarm=w(s,['UpperArm','Forearm','Hand']);
 parts[s]={'hand':np.where(hand>.5)[0],'forearm':np.where(fore>.5)[0]};fl[s]=[fc for fc in faces if all(arm[i]<.2 and piece[i]!=1 for i in fc)]
 em[s]={'arm':(skinarm[E[:,0]]>.3)&(skinarm[E[:,1]]>.3),'hand':(hand[E[:,0]]>.3)&(hand[E[:,1]]>.3)}
partfaces={}
for s in 'RL':
 partfaces[s]={}
 for part,ids in parts[s].items():
  chosen=set(ids);partfaces[s][part]=[fc for fc in faces if all(v in chosen for v in fc)]
armall=w('R',['Hand','Finger'])+w('L',['Hand','Finger']);fl['axe']=[fc for fc in faces if all(armall[i]<.2 for i in fc)]
headids=np.where((piece==0)&((rest[:,2]>1.67)|((rest[:,2]>1.61+.25*(rest[:,1]+.03))&(rest[:,1]<.025)&(np.abs(rest[:,0])<.20))))[0];shoulderids=(piece==0)&(np.abs(rest[:,0])>.12)&(rest[:,2]>1.27)&(rest[:,2]<1.54);fl['head']=[fc for fc in faces if all(shoulderids[i] for i in fc)]
headset=set(headids);headfaces=[fc for fc in faces if all(i in headset for i in fc)]
clothfaces=[fc for fc in faces if all(piece[i]==1 and rest[i,2]<.99 for i in fc)]
skirtids=np.where((piece==1)&(rest[:,2]<.95))[0];fl['skirt']=[fc for fc in faces if all(piece[i]==0 and rest[i,2]<1.10 for i in fc)]
def co(obj):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();a=np.array([tuple(obj.matrix_world@v.co) for v in m.vertices]);ev.to_mesh_clear();return a
def depth(tree,points,ids):
 best=(0,None,None)
 for i in ids:
  loc,nrm,fi,d=tree.find_nearest(Vector(points[i]),.05)
  if loc is not None and d>best[0] and (Vector(points[i])-loc).dot(nrm)<-.7*d:best=(d,int(i),int(fi))
 return best
# The current source-frame G6 table supersedes the older 2 cm prose: contacts <= 2 mm, head <= 1 cm.
assert BVHTree.FromPolygons([(-1,-1,0),(1,-1,0),(0,1,0)],[(0,1,2)]).overlap(BVHTree.FromPolygons([(0,-.5,-1),(0,-.5,1),(0,.5,0)],[(0,1,2)]))
report={};GR={s:json.loads((P/f'work/grip_pose_{s}.json').read_text()) for s in 'RL'}
for nm in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Fidget','Dead']:
 act=bpy.data.actions.get(nm)
 if act is None:continue
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];r={'G4':{},'G5':{},'G6':{},'posture':{},'grip':{}};pel=[];lean=[];shaft=[]
 for f in sorted(set(np.arange(float(act.frame_range[0]),float(act.frame_range[1]),bpy.context.scene.render.fps/48).tolist()+[float(act.frame_range[1])])):
  bpy.context.scene.frame_set(int(f),subframe=float(f%1));pts=co(body);axp=co(axe);am=rig.matrix_world@rig.pose.bones['Axe'].matrix@rig.data.bones['Axe'].matrix_local.inverted();shaftOrigin=np.array(am.translation);shaftA=np.array((am.to_3x3()@Vector((0,0,1))).normalized());ratio=np.linalg.norm(pts[E[:,0]]-pts[E[:,1]],axis=1)/np.maximum(rl,1e-8)
  for s in 'RL':
   for group,gate in [('arm','G4'),('hand','G5')]:
    vals=ratio[em[s][group]];metric=float(np.percentile(vals,99)) if gate=='G4' else float(vals.max())
    if metric>r[gate].get(s,{}).get('value',0):r[gate][s]={'value':metric,'frame':f,'max':float(vals.max())}
   tree=BVHTree.FromPolygons(pts.tolist(),fl[s])
   for part,ids in parts[s].items():
    # Removing the same limb leaves an open surface; reject its empty back half-space.
    limbfaces=partfaces[s][part];pairs=BVHTree.FromPolygons(pts.tolist(),limbfaces).overlap(tree);crossing=sorted({v for li,ti in pairs for v in limbfaces[li]});d,i,fi=depth(tree,pts,crossing);k=s+'_'+part
    # The skirt is an open sheet, so its back half-space is not a solid collision volume.
    limbfaces=partfaces[s][part]
    ct=BVHTree.FromPolygons(pts.tolist(),clothfaces);lp=BVHTree.FromPolygons(pts.tolist(),limbfaces).overlap(ct)
    if lp:
     nearids=sorted({v for li,ci in lp for v in limbfaces[li]});cd,cv,cfi=depth(ct,pts,nearids)
     if cd>d:d,i,fi=cd,cv,None

    if d>r['G6'].get(k,{}).get('depth_m',-1):r['G6'][k]={'depth_m':d,'frame':f,'sample':i,'hit_face':list(fl[s][fi]) if fi is not None else None}
   hm=rig.matrix_world@rig.pose.bones[f'B_{s}_Hand'].matrix;c=np.array(hm@Vector(GR[s]['handle_centre_hand_local']));a=np.array((hm.to_3x3()@Vector(GR[s]['handle_axis_hand_local'])).normalized());off=c-shaftOrigin;off-=shaftA*(off@shaftA);error=float(np.linalg.norm(off));key=s+'_shaft_error';r['grip'][key]=max(r['grip'].get(key,0),error) if not (nm=='Dead' or (nm=='Death' and f>=bpy.context.scene.render.fps/6)) else r['grip'].get(key,0);a=shaftA;c=shaftOrigin+shaftA*((c-shaftOrigin)@shaftA);ids=parts[s]['hand'];v=pts[ids]-c;along=v@a;rad=np.linalg.norm(v-np.outer(along,a),axis=1);near=abs(along)<.05;minimum=float(rad[near].min())
   if not (nm=='Dead' or (nm=='Death' and f>=bpy.context.scene.render.fps/6)) and minimum<r['grip'].get(s,{}).get('skin_radius_m',1):r['grip'][s]={'skin_radius_m':minimum,'frame':f}
  for k,points,ids in [('axe',axp,range(len(axp))),('head',pts,headids),('skirt',pts,skirtids)]:
   tree=BVHTree.FromPolygons(pts.tolist(),fl[k])
   if k=='head':
    hp=BVHTree.FromPolygons(pts.tolist(),headfaces).overlap(tree);ids=sorted({v for a,bb in hp for v in headfaces[a]})
   if k=='skirt':
    # Hidden hip faces are removed: signed nearest distance across an open boundary is not a cloth poke.
    # Require an actual cloth/skin triangle intersection before measuring penetration depth.
    pairs=BVHTree.FromPolygons(pts.tolist(),clothfaces).overlap(tree);ids=sorted({v for ci,si in pairs for v in clothfaces[ci]})
    r.setdefault('cloth_intersections',{})[str(f)]=len(pairs)
   d,i,fi=depth(tree,points,ids)
   if d>r['G6'].get(k,{}).get('depth_m',-1):r['G6'][k]={'depth_m':d,'frame':f,'sample':i,'hit_face':list(fl[k][fi]) if fi is not None else None}
  pp=rig.pose.bones['B_Pelvis'].head;dd=rig.pose.bones['B_Neck'].head-rig.pose.bones['B_Spine'].head;pel.append(pp.z);lean.append(math.degrees(math.atan2(math.hypot(dd.x,dd.y),dd.z)))
 r['posture']={'pelvis_z_min_m':min(pel),'pelvis_z_max_m':max(pel),'trunk_lean_max_deg':max(lean)}
 r['pass']={'G4':all(v['value']<=2.0 for v in r['G4'].values()),'G5':all(v['value']<=4.5 for v in r['G5'].values()) and all(r['grip'][s]['skin_radius_m']>=.0165 for s in 'RL' if s in r['grip']) and all(r['grip'].get(s+'_shaft_error',0)<.001 for s in 'RL'),'G6':all(v['depth_m']<=(.01 if k=='head' else .002) for k,v in r['G6'].items())}
 report[nm]=r;print('GATES',nm,json.dumps(r),flush=True)
(P/'review/rig_gates.json').write_text(json.dumps(report,indent=2))
