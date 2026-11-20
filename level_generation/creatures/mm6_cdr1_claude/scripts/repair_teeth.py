"""Replace the generated tooth islands with closed 22-triangle curved fangs; retain all other geometry/UVs/actions."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/before_teeth_v2/export/mm6_cdr1.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
labels=np.load(P/'work/mouth_components.npy');assert len(labels)==len(me.vertices)
remove={1,6,8,10,14,15,16,18,21,25,28,31,34,39,40,46,48,49,50,51,52,53,54,55,56,57,58}
removed_vertices={i for i,c in enumerate(labels) if c in remove}
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();old_tri=sum(len(f.verts)-2 for f in bm.faces);removed_faces=[f for f in bm.faces if any(v.index in removed_vertices for v in f.verts)];removed_tris=sum(len(f.verts)-2 for f in removed_faces)
assert all(all(v.index in removed_vertices for v in f.verts) for f in removed_faces)
bmesh.ops.delete(bm,geom=[bm.verts[i] for i in removed_vertices],context='VERTS')
uv=bm.loops.layers.uv.active;deform=bm.verts.layers.deform.verify();tooth_layer=bm.faces.layers.int.get('tooth_id') or bm.faces.layers.int.new('tooth_id');tile=json.loads((P/'work/teeth_tile.json').read_text());pad=tile['padding']
u0=(tile['x']+pad)/2048;u1=(tile['x']+tile['width']-pad)/2048;vtop=1-(tile['y']+pad)/2048;vbottom=1-(tile['y']+tile['height']-pad)/2048
# Centres follow the measured gum arches in bind space. Root rings sit inside the gums.
upper=[(.007,-1.523,.905,.0038,.016),(.019,-1.507,.915,.0050,.024),(.029,-1.487,.925,.0065,.036),(.036,-1.466,.934,.0060,.030),(.041,-1.443,.942,.0058,.027),(.044,-1.420,.944,.0052,.022)]
lower=[(.008,-1.515,.838,.0036,.014),(.020,-1.501,.846,.0044,.020),(.028,-1.482,.857,.0054,.028),(.034,-1.463,.870,.0052,.025),(.039,-1.443,.879,.0051,.022),(.043,-1.422,.890,.0045,.017)]
report=[]
for row,arch,sign,bone in [('upper',upper,-1,'Head'),('lower',lower,1,'Jaw')]:
 for side in [-1,1]:
  for number,(x,y,z,radius,length) in enumerate(arch):
   tooth_id=len(report)+1;base=Vector((side*x,y,z-(.003 if row=='lower' else 0)));axis=Vector((-side*.07,.22,sign)).normalized();u=Vector((1,0,0));u=(u-axis*u.dot(axis)).normalized();v=axis.cross(u);rings=[];uv_values={}
   for t,r in [(0,1),(.56,.57)]:
    ring=[];center=base+axis*(length*t)+Vector((0,length*.11*t*t,0))
    for j in range(6):
     a=math.tau*j/6;co=center+radius*r*(u*math.cos(a)*.82+v*math.sin(a));vert=bm.verts.new(co);vert[deform][body.vertex_groups[bone].index]=1;ring.append(vert)
    rings.append(ring)
   tip=bm.verts.new(base+axis*length+Vector((0,length*.11,0)));tip[deform][body.vertex_groups[bone].index]=1
   def face(vertices,coords,smooth=True):
    f=bm.faces.new(vertices);f.material_index=1;f.smooth=smooth;f[tooth_layer]=tooth_id
    for loop,(s,t) in zip(f.loops,coords):loop[uv].uv=(u0+(u1-u0)*s,vbottom+(vtop-vbottom)*t)
    return f
   for j in range(6):
    k=(j+1)%6;a=j/6;b=(j+1)/6
    face([rings[0][j],rings[0][k],rings[1][k],rings[1][j]],[(a,0),(b,0),(b,.56),(a,.56)])
    face([rings[1][j],rings[1][k],tip],[(a,.56),(b,.56),((a+b)/2,1)])
   face(list(reversed(rings[0])),[(.5,0)]*6,False)
   report.append({'id':tooth_id,'row':row,'side':side,'bone':bone,'length_m':length,'base':list(base),'triangles':22})
bmesh.ops.recalc_face_normals(bm,faces=[f for f in bm.faces if f[tooth_layer]>0]);bm.to_mesh(me);bm.free();me.update();me.calc_loop_triangles()
assert len(me.materials)==3
assert len(me.loop_triangles)==old_tri-removed_tris+22*len(report)
for v in me.vertices:assert abs(sum(g.weight for g in v.groups)-1)<1e-5
rig.animation_data.action=bpy.data.actions['Standing'];bpy.context.scene.frame_set(0)
(P/'review/teeth_v2').mkdir(exist_ok=True);(P/'review/teeth_v2/geometry.json').write_text(json.dumps({'old_triangles':old_tri,'removed_triangles':removed_tris,'new_teeth_triangles':22*len(report),'teeth_count':len(report),'new_triangles':len(me.loop_triangles),'teeth':report,'texture_tile':tile},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/teeth_v2.blend'));print('TEETH',len(report),'triangles',len(me.loop_triangles),'removed',removed_tris)
