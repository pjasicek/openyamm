"""Connect the exposed shoes to the body when the long robe lifts during a fall."""
import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
def add_trousers(body,rig):
 me=body.data
 if any(a.value==103 for a in me.attributes['piece'].data):return
 bm=bmesh.new();bm.from_mesh(me);piece=bm.verts.layers.int['piece'];deform=bm.verts.layers.deform.verify();uv=bm.loops.layers.uv['UVMap'];paint=json.loads((p/'work/trousers_uv.json').read_text());u,v=paint['uv_centre'];spread=paint['uv_half_size'];names={g.name:g.index for g in body.vertex_groups}
 for sd,pid in [('R',103),('L',104)]:
  hip,knee,ankle=[rig.data.bones[f'B_{sd}_{n}'].head_local.copy() for n in ['Thigh','Calf','Foot']]
  length=(knee-hip).length+(ankle-knee).length;fraction=(knee-hip).length/length;rings=[];rows=17;sides=12
  for j in range(rows):
   t=j/(rows-1)
   if t<=fraction:c=hip.lerp(knee,t/fraction);axis=(knee-hip).normalized();radius=.062+(.042-.062)*t/fraction
   else:c=knee.lerp(ankle,(t-fraction)/(1-fraction));axis=(ankle-knee).normalized();radius=.042+(.032-.042)*(t-fraction)/(1-fraction)
   across=Vector((1,0,0));across=(across-axis*across.dot(axis)).normalized();other=axis.cross(across).normalized();ring=[]
   calf=max(0.,min(1.,(t-fraction+.09)/.18))
   for k in range(sides):
    angle=2*math.pi*k/sides;vert=bm.verts.new(c+radius*(across*math.cos(angle)+other*math.sin(angle)));vert[piece]=pid
    pelvis=max(0.,1-t/.18)
    vert[deform][names['B_Pelvis']]=pelvis;vert[deform][names[f'B_{sd}_Thigh']]=(1-calf)*(1-pelvis);vert[deform][names[f'B_{sd}_Calf']]=calf*(1-pelvis);ring.append(vert)
   rings.append(ring)
  faces=[]
  for j in range(rows-1):
   for k in range(sides):faces.append(bm.faces.new([rings[j][k],rings[j][(k+1)%sides],rings[j+1][(k+1)%sides],rings[j+1][k]]))
  faces += [bm.faces.new(list(reversed(rings[0]))),bm.faces.new(rings[-1])]
  for f in faces:
   f.material_index=0;f.smooth=True
   for k,loop in enumerate(f.loops):loop[uv].uv=(u+spread*math.cos(2*math.pi*k/len(f.loops)),v+spread*math.sin(2*math.pi*k/len(f.loops)))
  bmesh.ops.recalc_face_normals(bm,faces=faces);bmesh.ops.triangulate(bm,faces=faces)
 bm.to_mesh(me);bm.free();me.update()
