"""Restore reduced contact vertices without changing the shared animation."""
import bpy,sys,json,numpy as np,subprocess
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from round3_candidate_gates import check
from rebake_render import render
for level,src in [(1,'plain1'),(2,'contour2'),(3,'qem3a')]:
 tag=f'contact{level}';bpy.ops.wm.open_mainfile(filepath=str(P/f'work/rebake/{src}.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;names=[g.name for g in body.vertex_groups];pv=np.array([v.value for v in me.attributes['piece'].data]);weights=np.zeros((len(me.vertices),len(names)))
 for v in me.vertices:
  for g in v.groups:weights[v.index,g.group]=g.weight
 inv=rig.data.bones['Bow'].matrix_local.inverted();local=[inv@v.co for v in me.vertices];wrap=[list(f.vertices)for f in me.polygons if all(pv[i]==201 and abs(local[i].z)<.1 for i in f.vertices)];tree=BVHTree.FromPolygons(local,wrap)
 frames=[('Standing',0),('Fidget',15),('Walking',12),('Running',12),('Attack',22),('Death',0),('Death',15),('Death',31)]
 maps=[]
 for role,f in frames:
  a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(f);B=rig.pose.bones['Bow'].matrix.inverted();maps.append({g.index:B@rig.pose.bones[g.name].matrix@rig.data.bones[g.name].matrix_local.inverted()for g in body.vertex_groups if g.name in rig.pose.bones})
 moves=[]
 if level>1:
  used=set()
  for digit in [0,1,2,4]:
   digitweights=weights[:,[i for i,n in enumerate(names)if n.startswith(f'B_L_Finger{digit}')]].sum(1);candidates=np.where((pv==3)&(digitweights>.4))[0];assert len(candidates),(tag,digit)
   matrices={}
   for i in candidates:
    matrices[i]=[sum((m[g.group]*g.weight for g in me.vertices[i].groups if g.group in m),Matrix([[0]*4 for _ in range(4)]))for m in maps]
   scored=[(max(tree.find_nearest(matrix@me.vertices[i].co)[3]for matrix in matrices[i]),i)for i in candidates if i not in used];_,index=min(scored);used.add(index);v=me.vertices[index];before=v.co.copy()
   for iteration in range(12):
    A=[];rhs=[]
    for matrix in matrices[index]:
     p=matrix@v.co;loc,n,_,dist=tree.find_nearest(p);target=loc+n*.0006;arr=np.array(matrix);A.extend(arr[:3,:3]);rhs.extend(np.array(target)-arr[:3,3])
    v.co=Vector(np.linalg.lstsq(np.asarray(A),np.asarray(rhs),rcond=None)[0])
   residual=max(tree.find_nearest(matrix@v.co)[3]for matrix in matrices[index]);moves.append({'digit':digit,'vertex':int(index),'move_mm':1000*(v.co-before).length,'contact_mm':1000*residual})
  if level==3:
   a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);foot=weights[:,[i for i,n in enumerate(names)if n in ['B_L_Foot','B_L_Toe0','B_R_Foot','B_R_Toe0']]].sum(1)>.55
   for v in me.vertices:
    if not foot[v.index]or pv[v.index]!=1:continue
    matrix=sum((rig.pose.bones[names[g.group]].matrix@rig.data.bones[names[g.group]].matrix_local.inverted()*g.weight for g in v.groups),Matrix([[0]*4 for _ in range(4)]));point=matrix@v.co
    if point.z<.0105:point.z=.0018;v.co=matrix.inverted()@point
 rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update();path=P/f'work/rebake/{tag}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));(P/f'review/rebake/{tag}_contact_fit.json').write_text(json.dumps(moves,indent=2))
 try:r=check(path)
 except Exception as e:r={'passed':False,'error':repr(e)}
 (P/f'review/rebake/{tag}_gates.json').write_text(json.dumps(r,indent=2));print('CONTACT_GATES',tag,{k:v for k,v in r.items()if k!='motion'},r.get('motion',{}).get('issues',[]),flush=True)
 render(path,'reference_pbr',level,True,parts=['actor']);render(path,tag,level,parts=['actor'])
 metrics=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/rebake_measure.py'),tag,str(level),'8','actor'],text=True));(P/f'review/rebake/{tag}_actor_metrics.json').write_text(json.dumps(metrics,indent=2));print('ACTOR_LOD',tag,metrics['actor']['pooled_iou'],flush=True)
