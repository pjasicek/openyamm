import bpy,bmesh,sys,json,math,os
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];args=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=str(p/args[0]));tag=args[1]
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;staff=bpy.data.objects.get('Staff');scene=bpy.context.scene
rest=np.array([v.co[:] for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);names=[g.name for g in body.vertex_groups];w=np.zeros((len(rest),len(names)))
for v in me.vertices:
 for g in v.groups:w[v.index,g.group]=g.weight
E=np.array([e.vertices[:] for e in me.edges]);rl=np.maximum(np.linalg.norm(rest[E[:,0]]-rest[E[:,1]],axis=1),1e-6)
faces=[tuple(f.vertices) for f in me.polygons]
def weight(sd,parts):return w[:,[i for i,n in enumerate(names) if n.startswith(f'B_{sd}_') and any(k in n for k in parts)]].sum(1)
parts={};edge={};bodyfaces={}
for sd in 'RL':
 arm=weight(sd,['UpperArm','Forearm','Hand']);hand=weight(sd,['Hand','Finger']);allarm=weight(sd,['Clavicle','UpperArm','Forearm','Hand','Finger'])
 edge[sd+'arm']=(arm[E[:,0]]>.3)&(arm[E[:,1]]>.3);edge[sd+'hand']=(hand[E[:,0]]>.3)&(hand[E[:,1]]>.3)
 parts[sd+'forearm']=np.where(weight(sd,['Forearm'])>.5)[0];parts[sd+'hand']=np.where(hand>.5)[0]
 keep=allarm<.2;bodyfaces[sd]=[f for f in faces if all(keep[i] for i in f)]
# Close the neck, sleeve-cut and hem boundaries before asking whether a point is inside.
# Keep disconnected garment pieces separate: parity across overlapping shells is not a union.
closed_body={}
for sd in 'RL':
 closed_body[sd]=[]
 for part in sorted(set(pv)):
  fs=[f for f in bodyfaces[sd] if all(pv[i]==part for i in f)]
  if not fs:continue
  bm=bmesh.new();vs=[bm.verts.new(Vector(x)) for x in rest]
  for f in fs:
   try:bm.faces.new([vs[i] for i in f])
   except ValueError:pass
  bm.verts.index_update();boundary=[e for e in bm.edges if e.is_boundary]
  if boundary:bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
  closed_body[sd].append([tuple(v.index for v in f.verts) for f in bm.faces]);bm.free()
headids=np.where((pv==2)&(rest[:,2]>1.43))[0]
shoulderfaces=[f for f in faces if all(pv[i] in [1,9,10] and rest[i,2]>1.27 and abs(rest[i,0])>.11 for i in f)]
clothfaces=[f for f in faces if all(pv[i]==100 for i in f)]
shoeids=np.where(np.isin(pv,[101,102])&(rest[:,2]>.125))[0]
G=json.loads((p/os.environ.get('GRIP_JSON','work/grip_pose.json')).read_text());report={}
def coords(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();out=[o.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear();return out

def depth(tree,points,limit=.05):
 best=(0,None)
 for ix,pt in points:
  loc,n,fi,d=tree.find_nearest(pt,limit)
  if loc is not None and d>best[0] and (pt-loc).dot(n)<-.7*d:best=(d,ix)
 return best
sys.path.insert(0,str(p/'scripts'));from contacts_r3 import solid_depth,inside
for role in [n for n in ['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget'] if n in bpy.data.actions and (not os.environ.get('GATE_ROLES') or n in os.environ['GATE_ROLES'].split(','))]:
 act=bpy.data.actions[role];rig.animation_data_create();rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 rig.animation_data.action=act
 if act.slots:rig.animation_data.action_slot=act.slots[0]
 result={'sample_fps':scene.render.fps/float(os.environ.get('GATE_STEP','1')),'clip_fps':scene.render.fps,'G4_p99':{},'G4_max':{},'G5_max':{},'G6_mm':{},'head_shoulder_mm':0,'grip_min_mm':1e6,'floor_min_mm':1e6,'pelvis_height_m':[],'trunk_lean_deg':[],'palm_trajectory':[]}
 for f in np.arange(float(act.frame_range[0]),float(act.frame_range[1])+.01,float(os.environ.get('GATE_STEP','1'))):
  scene.frame_set(int(f),subframe=float(f-int(f)));V=coords(body);co=np.array(V);stretch=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1)/rl
  for sd in 'RL':
   for key,mask in [('G4_p99',edge[sd+'arm']),('G4_max',edge[sd+'arm']),('G5_max',edge[sd+'hand'])]:
    val=float(np.percentile(stretch[mask],99) if key=='G4_p99' else stretch[mask].max())
    if val>result[key].get(sd,[0])[0]:result[key][sd]=[val,f]
   trees=[BVHTree.FromPolygons(V,fs) for fs in closed_body[sd]];surface=BVHTree.FromPolygons(V,bodyfaces[sd])
   for part in ['forearm','hand']:
    val,vi=0,None
    for i in parts[sd+part]:
     loc,n,fi,d=surface.find_nearest(V[i],.05)
     # Auxiliary caps classify containment; only an inward ORIGINAL surface measures penetration.
     if loc is not None and d>val and (V[i]-loc).dot(n)<-.7*d and any(inside(tree,V[i]) for tree in trees):val,vi=d,int(i)
    if val*1000>result['G6_mm'].get(sd+part,[0])[0]:result['G6_mm'][sd+part]=[val*1000,f,vi]
  ht=BVHTree.FromPolygons(V,[fc for fc in faces if all(pv[i]==2 for i in fc)]);hd,_=solid_depth(ht,[(int(i),V[i]) for i in set(j for fc in shoulderfaces for j in fc)],.05);result['head_shoulder_mm']=max(result['head_shoulder_mm'],hd*1000)
  if staff:
   sv=coords(staff)
   tree=BVHTree.FromPolygons(V,[fc for fc in faces if all(pv[i] not in [3,4] for i in fc)])
   val,vi=depth(tree,list(enumerate(sv)))
   handtree=BVHTree.FromPolygons(V,[fc for fc in faces if all(pv[i]==4 for i in fc)]);handval,handvi=solid_depth(handtree,list(enumerate(sv)))
   if handval>val:val,vi=handval,handvi
   if val*1000>result['G6_mm'].get('staff',[0])[0]:result['G6_mm']['staff']=[val*1000,f,vi]
  # Shoes should emerge below the hem, never through its sides.
  # The robe is an open tube: boots can emerge through the hem legitimately. Test cloth inside the CLOSED
  # shoe surfaces, which detects actual intersections without treating an uncovered ankle as a collision.
  shoe_faces=[fc for fc in faces if all(pv[i] in [101,102] for i in fc)]
  ct=[BVHTree.FromPolygons(V,[fc for fc in faces if all(pv[i]==part for i in fc)]) for part in [101,102]]
  val,vi=max((solid_depth(tree,[(int(i),V[i]) for i in np.where(pv==100)[0]],.04) for tree in ct),key=lambda x:x[0])
  if val*1000>result['G6_mm'].get('cloth_in_shoe',[0])[0]:result['G6_mm']['cloth_in_shoe']=[val*1000,f,vi]
  lt=[BVHTree.FromPolygons(V,[fc for fc in faces if all(pv[i]==part for i in fc)]) for part in [103,104]]
  val,vi=max((solid_depth(tree,[(int(i),V[i]) for i in np.where(pv==100)[0]],.04) for tree in lt),key=lambda x:x[0])
  if val*1000>result['G6_mm'].get('cloth_in_leg',[0])[0]:result['G6_mm']['cloth_in_leg']=[val*1000,f,vi]
  hm=rig.matrix_world@rig.pose.bones['B_R_Hand'].matrix;C=hm@Vector(G['handle_centre_hand_local']);A=(hm.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized();hp=co[pv==3]-np.array(C);ax=hp@np.array(A);near=np.abs(ax)<.055
  radius=np.linalg.norm(hp[near]-np.outer(ax[near],np.array(A)),axis=1).min();result['grip_min_mm']=min(result['grip_min_mm'],float(radius*1000))
  if float(co[:,2].min()*1000)<result['floor_min_mm']:
   result['floor_min_mm']=float(co[:,2].min()*1000);result['floor_frame']=float(f);result['floor_vertex']=int(co[:,2].argmin())
  pelvis=rig.matrix_world@rig.pose.bones['B_Pelvis'].head;neck=rig.matrix_world@rig.pose.bones['B_Neck'].head
  result['pelvis_height_m'].append(float(pelvis.z));result['trunk_lean_deg'].append(math.degrees((neck-pelvis).angle(Vector((0,0,1)))))
  H=rig.pose.bones['B_L_Hand'];result['palm_trajectory'].append(list(H.head))
 result['pelvis_height_m']=[min(result['pelvis_height_m']),max(result['pelvis_height_m'])];result['trunk_lean_deg']=[min(result['trunk_lean_deg']),max(result['trunk_lean_deg'])]
 result['G4_pass']=all(x[0]<2 for x in result['G4_p99'].values());result['G5_pass']=all(x[0]<=4.5 for x in result['G5_max'].values());result['G6_pass']=all(x[0]<=2 for x in result['G6_mm'].values()) and result['head_shoulder_mm']<=10
 report[role]=result
 print('GATES',role,json.dumps({k:v for k,v in result.items() if k!='palm_trajectory'}),flush=True)
(p/'work'/f'gates_{tag}.json').write_text(json.dumps(report,indent=2))

assert all(r[k] for r in report.values() for k in ["G4_pass","G5_pass","G6_pass"]), "Rig gate failed; inspect the saved report"
