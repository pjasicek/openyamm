import bpy,bmesh,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/pre_neck_master.blend'));o=bpy.data.objects['Body'];me=o.data;bm=bmesh.new();bm.from_mesh(me)
# Match the replacement neck's bottom cross section to the actual body cut ring, with a buried overlap.
ring={v for e in bm.edges if e.is_boundary for v in e.verts if abs(v.co.x)<.08 and v.co.y<-.26 and .53<v.co.z<.59 and any(f.material_index==0 for f in v.link_faces)};assert len(ring)>12
center=sum((v.co for v in ring),Vector())/len(ring);points=sorted([(math.atan2(v.co.y-center.y,v.co.x-center.x),v.co.copy()) for v in ring]);print('RING',list(center),len(ring))
bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index==1 and max(v.co.z for v in f.verts)<.538],context='FACES')
deform=bm.verts.layers.deform.active;jaw=o.vertex_groups['Jaw'].index
head={v for f in bm.faces if f.material_index==1 for v in f.verts}
for v in head:
 if v.co.z>=.635 or v[deform].get(jaw,0)>.1:continue
 t=max(0,min(1,(.635-v.co.z)/.115));angle=math.atan2(v.co.y+.324,v.co.x);_,target=min(points,key=lambda p:abs(math.atan2(math.sin(p[0]-angle),math.cos(p[0]-angle))))
 target=center+(target-center)*.94;target.z=.540;v.co=v.co.lerp(target,t)
# Remove the old upper crest, now replaced by the head model's integrated crest.
bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index==0 and abs(f.calc_center_median().x)<.13 and f.calc_center_median().y<-.17 and f.calc_center_median().z>.57],context='FACES')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(me);bm.free();me.validate(verbose=True);me.update()
ids=[v.index for v in me.vertices if abs(v.co.x)<.12 and v.co.y<-.20 and .48<v.co.z<.57]
for g in o.vertex_groups:g.remove(ids)
o.vertex_groups['Neck3'].add(ids,1,'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'))
