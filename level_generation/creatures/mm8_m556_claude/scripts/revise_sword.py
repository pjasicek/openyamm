"""Replace only the original rigid sword; preserve body/shield geometry, UVs and weights."""
from pathlib import Path
import bpy,bmesh,math,json,numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv.blend'))
rig=bpy.data.objects['Wasp_Rig'];body=bpy.data.objects['Wasp'];owner=body.vertex_groups['Sword'].index
keep=[v.index for v in body.data.vertices if not any(g.group==owner and g.weight>.5 for g in v.groups)]
original=np.array([body.data.vertices[i].co[:] for i in keep]);uv_before=[tuple(body.data.uv_layers.active.data[i].uv) for f in body.data.polygons if all(i in set(keep) for i in f.vertices) for i in f.loop_indices]
bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table();layer=bm.verts.layers.deform.active
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer].get(owner,0)>.5],context='VERTS');bm.to_mesh(body.data);bm.free()
assert np.allclose(original,np.array([v.co[:] for v in body.data.vertices]),atol=0)
assert uv_before==[tuple(v.uv) for v in body.data.uv_layers.active.data]
mat=body.data.materials[1];parts=[];cx,cz=.263,.459

def finish(obj,name,swatch,smooth=False):
 obj.name=name;bpy.context.view_layer.objects.active=obj;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 obj.data.materials.clear();obj.data.materials.append(mat);uv=obj.data.uv_layers.active or obj.data.uv_layers.new(name='UVMap')
 for v in uv.data:v.uv=((swatch%2+.5)/2,(swatch//2+.5)/2)
 obj.vertex_groups.new(name='Sword').add(list(range(len(obj.data.vertices))),1,'REPLACE')
 for f in obj.data.polygons:f.use_smooth=smooth
 parts.append(obj);return obj

def mesh(name,vertices,faces,swatch):
 data=bpy.data.meshes.new(name);data.from_pydata(vertices,[],faces);data.update();obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj);return finish(obj,name,swatch)

def cylinder(name,y,radius,depth,swatch,segments=12):
 bpy.ops.mesh.primitive_cylinder_add(vertices=segments,radius=radius,depth=depth,location=(cx,y,cz),rotation=(math.pi/2,0,0));return finish(bpy.context.object,name,swatch,True)
# Eight vertices per cross-section: raised centre, broad planes and distinct edge bevels.
sections=[(-.145,.013,.0032),(-.181,.016,.0030),(-.285,.014,.0025),(-.391,.009,.0019),(-.440,.003,.0009)]
verts=[]
for y,w,h in sections:
 verts += [(cx-w,y,cz),(cx-.70*w,y,cz+h*.50),(cx,y,cz+h),(cx+.70*w,y,cz+h*.50),(cx+w,y,cz),(cx+.70*w,y,cz-h*.50),(cx,y,cz-h),(cx-.70*w,y,cz-h*.50)]
verts.append((cx,-.466,cz));faces=[tuple(range(7,-1,-1))]
for i in range(len(sections)-1):
 for j in range(8):faces.append((i*8+j,i*8+(j+1)%8,(i+1)*8+(j+1)%8,(i+1)*8+j))
for j in range(8):faces.append(((len(sections)-1)*8+j,(len(sections)-1)*8+(j+1)%8,len(verts)-1))
blade=mesh('SwordBroadBlade',verts,faces,0)
# Broad brushed-steel planes remain legible; narrow polished bevels catch the light.
for f in blade.data.polygons:
 if f.index>0 and (f.index-1)%8 in (1,2,5,6):
  for i in f.loop_indices:blade.data.uv_layers.active.data[i].uv=(.25,.75)

# Dark recessed central fuller stops before the tapered point, on both faces.
for sign in [-1,1]:
 vs=[]
 for y,w,h in sections[:4]:vs.extend([(cx-.0022,y,cz+sign*(h+.00008)),(cx+.0022,y,cz+sign*(h+.00008))])
 mesh('SwordFuller',vs,[(i*2,i*2+1,i*2+3,i*2+2) if sign>0 else (i*2+2,i*2+3,i*2+1,i*2) for i in range(3)],3)
cylinder('SwordLeatherGrip',-.096,.0053,.067,3)
for i in range(9):
 bpy.ops.mesh.primitive_torus_add(major_radius=.00525,minor_radius=.00065,major_segments=12,minor_segments=4,location=(cx,-.066-i*.0075,cz),rotation=(math.pi/2,0,0));finish(bpy.context.object,'SwordGripWrap',3,True)
for y in [-.061,-.130]:cylinder('SwordGripFerrule',y,.0062,.004,0)
# Swept steel quillons have real depth and taper, with tier-coloured caps.
for sign in [-1,1]:
 vs=[]
 for x,y,w in [(0,-.139,.0055),(.020,-.141,.005),(.034,-.151,.0035)]:
  vs += [(cx+sign*x,y-w,cz-w*.8),(cx+sign*x,y+w,cz-w*.8),(cx+sign*x,y+w,cz+w*.8),(cx+sign*x,y-w,cz+w*.8)]
 fs=[(3,2,1,0),(8,9,10,11)]+[(i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j) for i in range(2) for j in range(4)]
 o=mesh('SwordSweptGuard',vs,fs,0)
 if sign<0:
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(o.data);bm.free()
 bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=1,location=(cx+sign*.034,-.151,cz));o=bpy.context.object;o.scale=(.0045,.0045,.0045);finish(o,'SwordGuardCap',1,True)
bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=1,location=(cx,-.054,cz));o=bpy.context.object;o.scale=(.009,.009,.007);finish(o,'SwordPommel',0,True)
for sign in [-1,1]:
 bpy.ops.mesh.primitive_uv_sphere_add(segments=10,ring_count=6,radius=1,location=(cx,-.054,cz+sign*.006));o=bpy.context.object;o.scale=(.004,.004,.002);finish(o,'SwordPommelInset',1,True)
for o in parts:
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(o.data);bm.free()
bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
assert np.array_equal(original,np.array([v.co[:] for v in body.data.vertices[:len(original)]]))
body.data.calc_loop_triangles();tri=sum(all(any(g.group==owner and g.weight>.99 for g in body.data.vertices[v].groups) for v in t.vertices) for t in body.data.loop_triangles)
(P/'work/sword_v2.json').write_text(json.dumps(dict(blade_length_m=.321,blade_width_m=.032,guard_span_m=.077,grip_radius_m=.0053,sword_triangles=tri,body_shield_preserved_vertices=len(original),body_shield_geometry_uv_preserved=True),indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_uv_sword_v2.blend'));print('NEW SWORD',tri,'triangles; body and shield unchanged')
