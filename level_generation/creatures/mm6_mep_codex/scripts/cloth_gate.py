import bpy,numpy as np,json,os
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/os.environ.get('GATE_BLEND','work/texture_master.blend')));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];me=b.data;pv=np.array([v.value for v in me.attributes['piece'].data]);co=np.array([v.co[:] for v in me.vertices]);top=json.loads((p/'work/cloth_topology.json').read_text());sc=bpy.context.scene
# Caps close numerical ray volumes only. Their surfaces are excluded from contact findings.
def volume(P,tag):
 verts=[Vector(x) for x in P];fs=[tuple(f) for f in tag['faces']];caps=set()
 for loop in tag['loops']:
  k=len(verts);verts.append(sum((verts[i] for i in loop),Vector())/len(loop))
  for a,z in zip(loop,loop[1:]+loop[:1]):caps.add(len(fs));fs.append((z,a,k))
 return BVHTree.FromPolygons(verts,fs),caps
D=Vector((.811,.357,.463)).normalized()
def signed(tree,x):
 q,n,fi,d=tree.find_nearest(x);o=x.copy();hits=0
 for _ in range(64):
  q=tree.ray_cast(o,D,5)[0]
  if q is None:return (-d if hits%2 else d),fi
  hits+=1;o=q+D*.000001
 raise AssertionError('Unresolved ray parity')
report={}
for act in bpy.data.actions:
 if not act.use_fake_user:continue
 r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];row={k:{'worst_penetration_mm':0.,'hits':0} for k in ['L_sleeve','R_sleeve','coat']};count=0
 for f in sorted(set(list(np.arange(0,float(act.frame_range[1])+.0001,30/48))+[float(act.frame_range[1])])):
  sc.frame_set(int(f),subframe=f%1);ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();P=[v.co.copy() for v in em.vertices];ev.to_mesh_clear();count+=1
  for kind,tag in top.items():
   tree,caps=volume(P,tag);ids=np.where((pv==(2 if kind=='L' else 3)) if kind!='coat' else (np.isin(pv,[1,5,6])&(co[:,2]>.79)&(co[:,2]<1.14)))[0];label=kind+'_sleeve' if kind!='coat' else kind
   for i in ids:
    d,fi=signed(tree,P[i])
    if d<-.0001 and fi not in caps:
     row[label]['hits']+=1
     if -d*1000>row[label]['worst_penetration_mm']:row[label].update(worst_penetration_mm=-d*1000,frame=float(f),vertex=int(i))
 row['samples_48hz']=count;row['pass']=all(row[k]['worst_penetration_mm']<=2 for k in ['L_sleeve','R_sleeve','coat']);report[act.name]=row;print('CLOTH',act.name,row,flush=True)
(p/'work/cloth_gate.json').write_text(json.dumps({'method':'Signed nearest distance with ray parity in closed cloth component volumes; artificial cut caps are excluded. Every forearm/hand vertex and pants/leg vertex above the measured 0.804 m coat hem, at 48 Hz.','clips':report},indent=2))
