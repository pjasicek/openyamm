"""Rest-frame identity and fitted finger-chain containment in closed arm skin."""
import bpy,sys,os,json,math,hashlib
from pathlib import Path
from collections import Counter
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];kind=os.environ['KEPT_BODY'];src=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];me=b.data
pc=[v.value for v in me.attributes['piece'].data];co=[v.co.copy() for v in me.vertices]
off=json.loads(bpy.context.scene['rig_offsets']);errors={n:math.degrees(r.data.bones[n].matrix_local.to_quaternion().rotation_difference((Quaternion(v['q']).to_matrix()@Matrix(v['R_src'])).to_quaternion()).angle) for n,v in off.items()}
def inside(tree,p):
 direction=Vector((.719,.371,.588)).normalized();origin=p.copy();hits=0
 for _ in range(64):
  hit,n,ix,d=tree.ray_cast(origin,direction,10.)
  if hit is None:return hits%2==1
  hits+=1;origin=hit+direction*1e-5
 raise AssertionError('Ray did not leave skin')
report={'source_sha256':hashlib.sha256(Path(src).read_bytes()).hexdigest(),'rest_frame_error_deg':max(errors.values()),'closed_skin':{},'finger_samples':[]}
for side,part in [('L',4 if kind=='male' else 3),('R',3 if kind=='male' else 4)]:
 faces=[list(p.vertices) for p in me.polygons if pc[p.vertices[0]]==part];edges=Counter(tuple(sorted((f[i],f[(i+1)%len(f)])))for f in faces for i in range(len(f)))
 report['closed_skin'][side]={'boundary':sum(v==1 for v in edges.values()),'nonmanifold':sum(v>2 for v in edges.values())};assert all(v==2 for v in edges.values()),report['closed_skin']
 tree=BVHTree.FromPolygons(co,faces)
 for bone in r.data.bones:
  if not bone.name.startswith(f'B_{side}_Finger'):continue
  # Joint heads and mid-segment points; the measured tip lies on the surface.
  samples=[bone.head_local]
  if bone.children:samples.append((bone.head_local+bone.children[0].head_local)*.5)
  for p in samples:
   near,normal,_,distance=tree.find_nearest(p);outside=not inside(tree,p)
   report['finger_samples'].append({'bone':bone.name,'point':list(p),'distance_m':distance,'outside':bool(outside)})
report['pass']=report['rest_frame_error_deg']<.1 and all(not s['outside'] or s['distance_m']<.001 for s in report['finger_samples'])
(P/'review'/kind/'joint_gate.json').write_text(json.dumps(report,indent=2)+'\n')
print('JOINT_GATE',kind,report['pass'],report['closed_skin'],'outside',[(s['bone'],s['distance_m'])for s in report['finger_samples'] if s['outside']],flush=True)

sys.stdout.flush();sys.stderr.flush();os._exit(0)
