"""Measure limb rings near the service estimates; the source-proportion scan hit fingers and boot folds."""
from pathlib import Path
import bpy,bmesh,numpy as np,json
from mathutils import Vector
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/step1.blend'))
body=bpy.data.objects['Body'];base=bmesh.new();base.from_mesh(body.data);pv=base.verts.layers.int['piece']
bmesh.ops.delete(base,geom=[v for v in base.verts if v[pv] not in [0,1]],context='VERTS')
seeds=json.loads((p/'work/meshy_joints.json').read_text())['joints'];joints={k:list(v) for k,v in seeds.items()};report={}
def ring_at(point,normal):
 bm=base.copy();res=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=point,plane_no=normal)
 edges={e for e in res['geom_cut'] if isinstance(e,bmesh.types.BMEdge)};todo={v for e in edges for v in e.verts};rings=[]
 while todo:
  v=todo.pop();stack=[v];comp=[v]
  while stack:
   v=stack.pop()
   for e in v.link_edges:
    if e not in edges:continue
    n=e.other_vert(v)
    if n in todo:todo.remove(n);stack.append(n);comp.append(n)
  es=[e for e in edges if e.verts[0] in comp]
  if len(comp)<8 or any(sum(e in edges for e in v.link_edges)!=2 for v in comp):continue
  centre=sum((v.co for v in comp),Vector())/len(comp);perimeter=sum(e.calc_length() for e in es)
  if .14<perimeter<.85 and (centre-point).length<.12:rings.append((centre.copy(),perimeter,len(comp)))
 bm.free()
 return min(rings,key=lambda r:(r[0]-point).length) if rings else None
for side in ['L','R']:
 for name,parent,search in [('Hand','Forearm',True),('Forearm','UpperArm',False),('Foot','Calf',True),('Calf','Thigh',False)]:
  key=f'{side}_{name}';seed=Vector(seeds[key]);axis=(seed-Vector(seeds[f'{side}_{parent}'])).normalized();rows=[]
  offsets=np.linspace(-.05,.09,29) if name=='Hand' else np.linspace(-.04,.04,17) if name=='Foot' else [0]
  for offset in offsets:
   point=seed+axis*float(offset);r=ring_at(point,axis)
   if r:rows.append({'offset':float(offset),'centre':list(r[0]),'perimeter':r[1],'vertices':r[2]})
  assert rows,key
  selected=min(rows,key=lambda r:r['perimeter']) if search else rows[0]
  joints[key]=selected['centre'];movement=(Vector(joints[key])-seed).length
  assert movement<.125,(key,movement)
  report[key]={'seed':list(seed),'selected':selected,'move_m':movement,'samples':rows};print('FITTED',key,'seed',list(seed),'measured',joints[key],'perimeter',selected['perimeter'],'move',movement,flush=True)
base.free()
(p/'work/joints_final.json').write_text(json.dumps({'height_m':2.4,'joints':joints,'report':report},indent=2))
