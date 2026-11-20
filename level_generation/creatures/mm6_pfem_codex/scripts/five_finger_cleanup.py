import bpy,sys,runpy,json,bmesh,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
runpy.run_path(str(p/'scripts/build_rig.py'),run_name='__main__')
sys.argv=['fit_fingers.py','--',str(p/'work/rig_v1.blend')]
runpy.run_path(str(p/'scripts/fit_fingers.py'),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(p/'work/step1.blend'))
me=bpy.data.objects['Body'].data;bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
pv=bm.verts.layers.int['piece']
drop=[];pinkies=[]
for side in 'RL':
 d=json.load(open(p/f'work/finger_geometry_{side}.json'))
 comps=sorted(d['fingers'],key=lambda ids:np.mean([bm.verts[i].co.y for i in ids]),reverse=True)
 drop += [bm.verts[i] for i in comps[0]]
 pinkies.append([bm.verts[i] for i in comps[1]])
 print('EXTRA FINGER removed',side,len(comps[0]))
bmesh.ops.delete(bm,geom=drop,context='VERTS')
for comp in pinkies:
 base=max(comp,key=lambda v:v.co.z).co.copy()
 for v in comp:v.co=base+(v.co-base)*.88
# Close the cut at the outer web with a small, smoothed cap.
unused=set(e for e in bm.edges if e.is_boundary and all(v[pv] in (3,4) for v in e.verts))
while unused:
 e=unused.pop();loop=list(e.verts);last=loop[-1]
 while last!=loop[0]:
  ne=next((a for a in last.link_edges if a in unused),None)
  if ne is None:break
  unused.remove(ne);last=ne.other_vert(last)
  if last!=loop[0]:loop.append(last)
 if last!=loop[0]:raise RuntimeError('Finger cut boundary not closed')
 print('HAND boundary',len(loop),min(v.co.z for v in loop),max(v.co.z for v in loop))
 if sum(v.co.z for v in loop)/len(loop)>.930:continue
 mi=loop[0].link_faces[0].material_index
 f=bm.faces.new(loop);f.material_index=mi;f.smooth=True
 # Retract the removed digit's web into a continuous outer palm edge.
 if min(v.co.z for v in loop)<.89:
  region={v:1.0 for v in loop};front=set(loop)
  for weight in (.65,.3,.1):
   nxt={e.other_vert(v) for v in front for e in v.link_edges}-set(region)
   for v in nxt:region[v]=weight
   front=nxt
  sign=1 if sum(v.co.x for v in loop)>0 else -1
  for v,w in region.items():
   v.co+=Vector((-sign*.014,-.006,.015))*w
  for _ in range(7):
   updates={v:v.co.lerp(sum((e.other_vert(v).co for e in v.link_edges),Vector())/len(v.link_edges),.36*w) for v,w in region.items()}
   for v,co in updates.items():v.co=co
 bmesh.ops.triangulate(bm,faces=[f])
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
me.attributes['orig_co'].data.foreach_set('vector',np.array([tuple(v.co) for v in me.vertices]).ravel())
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
common.workbench_clay(bpy.context.scene)
for side,x in [('R',-.465),('L',.462)]:
 common.render_views(str(p/f'review/hand_five_{side}'),.891,.20,views=('left','right'),resolution=(600,600),target=(x,-.056))
runpy.run_path(str(p/'scripts/build_rig.py'),run_name='__main__')
sys.argv=['fit_fingers.py','--',str(p/'work/rig_v1.blend')]
runpy.run_path(str(p/'scripts/fit_fingers.py'),run_name='__main__')
