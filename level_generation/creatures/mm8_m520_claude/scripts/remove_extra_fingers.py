from pathlib import Path
import bpy,bmesh,json,numpy as np,sys
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/step1_six_fingers.blend'))
body=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table()
report={}
for side in ['R','L']:
 data=json.loads((p/f'work/extra_finger_{side}.json').read_text());centre=Vector(np.mean(data['co'],axis=0));seed=min(bm.verts,key=lambda v:(v.co-centre).length)
 selected=None
 for z in np.arange(1.06,1.28,.002):
  seen={seed};stack=[seed]
  while stack:
   v=stack.pop()
   for e in v.link_edges:
    n=e.other_vert(v)
    if n not in seen and n.co.z<z:seen.add(n);stack.append(n)
  if 30<len(seen)<90:selected=(float(z),seen)
  elif selected and len(seen)>=90:break
 assert selected,side
 z,verts=selected;print('REMOVE',side,z,len(verts),flush=True)
 bmesh.ops.delete(bm,geom=list(verts),context='VERTS')
 edges=[e for e in bm.edges if e.is_boundary and (e.verts[0].co-centre).length<.22]
 vs={v for e in edges for v in e.verts};assert len(vs)==len(edges) and 6<len(vs)<40,(side,len(vs),len(edges))
 # The branch ends at the back of the palm; a shallow fan restores that surface.
 c=sum((v.co for v in vs),Vector())/len(vs);v=bm.verts.new(c);v.co=c
 for layer in bm.verts.layers.float_vector.values():v[layer]=c
 for e in edges:bm.faces.new((e.verts[0],e.verts[1],v))
 for _ in range(4):bmesh.ops.smooth_vert(bm,verts=list(vs)+[v],factor=.5,use_axis_x=True,use_axis_y=True,use_axis_z=True)
 report[side]={'cut_z':z,'removed_vertices':len(verts),'cap_edges':len(edges),'cap_centre':list(c)}
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 assert not [e for e in bm.edges if e.is_boundary and (e.verts[0].co-centre).length<.22]
bm.to_mesh(body.data);bm.free();body.data.update()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
(p/'work/hand_cleanup.json').write_text(json.dumps(report,indent=2))
common.workbench_clay(bpy.context.scene)
for side in ['R','L']:
 c=Vector(report[side]['cap_centre']);common.render_views(str(p/f'review/hand_clean_{side}'),c.z-.05,.5,views=('front','back','left'),resolution=(600,600),target=(c.x,c.y))
