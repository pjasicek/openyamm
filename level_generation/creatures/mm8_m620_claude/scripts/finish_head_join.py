"""Finish the separate head with a connected, smoothly shaded neck; run after UV repair."""
from pathlib import Path
import bpy,bmesh,math,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_textured_uv.blend'))

# Taper neck.
o=bpy.data.objects['Body'];m=o.data;h=m.attributes['head'];hf=[tuple(f.vertices) for f in m.polygons if h.data[f.index].value];hv=set(i for f in hf for i in f)
for i in hv:
 v=m.vertices[i]
 if v.co.z<=1.470001:
  angle=math.atan2((v.co.y-.026)/.047,(v.co.x+.011)/.049);scale=.7+.3*min(1,max(0,(v.co.z-1.415)/.03))
  v.co.x=-.011+.049*scale*math.cos(angle);v.co.y=.026+.047*scale*math.sin(angle)
tree=BVHTree.FromPolygons([v.co[:] for v in m.vertices],hf,all_triangles=True)
for v in m.vertices:
 if v.index not in hv and m.attributes['region'].data[v.index].value==0 and 1.445<v.co.z<1.471:
  origin=Vector((-.011,.026,v.co.z));d=v.co-origin;d.z=0;d.normalize();loc,n,fi,dist=tree.ray_cast(origin,d,.2);assert loc is not None
  t=min(1,max(0,(v.co.z-1.445)/.025));t=t*t*(3-2*t);v.co=v.co.lerp(loc-n*.0008,t)


# Smooth throat.
o=bpy.data.objects['Body'];m=o.data;hv=set(i for f in m.polygons if m.attributes['head'].data[f.index].value for i in f.vertices)
for v in m.vertices:
 if v.index in hv or m.attributes['region'].data[v.index].value!=0:continue
 z=v.co.z;dx=v.co.x+.011
 if 1.405<z<1.47 and v.co.y<.026:
  k=min(1,max(0,(z-1.42)/.05));rx=.069-.020*k;ry=.032+.015*k
  if abs(dx)<rx:
   target=.026-ry*math.sqrt(max(0,1-(dx/rx)**2));t=min(1,max(0,(z-1.405)/.030))*min(1,max(0,(1.47-z)/.006));t=t*t*(3-2*t)
   v.co.y=v.co.y*(1-t)+target*t
# Neck shaping needs geometric normals, not the original head's imported custom normals.
if m.has_custom_normals:m.normals_split_custom_set([(0,0,0)]*len(m.loops))


# Weld neck.
bm=bmesh.new();bm.from_mesh(m);reg=bm.verts.layers.int['region'];head=bm.faces.layers.int['head'];verts=[v for v in bm.verts if v[reg]==0 and 1.39<v.co.z<1.48 and all(not f[head] for f in v.link_faces)];bmesh.ops.remove_doubles(bm,verts=verts,dist=.00001);bmesh.ops.recalc_face_normals(bm,faces=[f for f in bm.faces if any(v in verts for v in f.verts)]);bm.to_mesh(m);bm.free()
if m.has_custom_normals:m.normals_split_custom_set([(0,0,0)]*len(m.loops))


# Trim head overlap.
bm=bmesh.new();bm.from_mesh(m);tag=bm.faces.layers.int['head'];faces=[f for f in bm.faces if f[tag]];geom=set(faces)|{e for f in faces for e in f.edges}|{v for f in faces for v in f.verts}
bmesh.ops.bisect_plane(bm,geom=list(geom),dist=1e-7,plane_co=(0,0,1.465),plane_no=(0,0,1),clear_inner=True);bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3]);bm.to_mesh(m);bm.free()
if m.has_custom_normals:m.normals_split_custom_set([(0,0,0)]*len(m.loops))


# Bridge head neck.
bm=bmesh.new();bm.from_mesh(m);bridge=bm.faces.layers.int.new('neck_bridge');hd=bm.faces.layers.int['head'];reg=bm.verts.layers.int['region'];fs=[f for f in bm.faces if not f[hd] and all(v[reg]==0 for v in f.verts)];geom=set(fs)|{e for f in fs for e in f.edges}|{v for f in fs for v in f.verts}
bmesh.ops.bisect_plane(bm,geom=list(geom),dist=1e-7,plane_co=(0,0,1.455),plane_no=(0,0,1),clear_outer=True)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
verts=[v for v in bm.verts if v[reg]==0 and 1.44<v.co.z<1.48];bmesh.ops.remove_doubles(bm,verts=verts,dist=.000001)
edges=[e for e in bm.edges if e.is_boundary and (all(abs(v.co.z-1.455)<1e-5 for v in e.verts) or all(abs(v.co.z-1.465)<1e-5 for v in e.verts))]
assert len(edges)>30
made=bmesh.ops.bridge_loops(bm,edges=edges,use_pairs=True)['faces'];assert made
uv=bm.loops.layers.uv['HeadUV'];buv=bm.loops.layers.uv['UVMap']
occupied=np.load(p/'work/uvraster_HeadUV.npz')['coverage'];N=2048;w,h=160,32;integral=np.pad(occupied.astype(np.int32),((1,0),(1,0))).cumsum(0).cumsum(1);areas=integral[h:,w:]-integral[:-h,w:]-integral[h:,:-w]+integral[:-h,:-w];free=np.argwhere(areas[::4,::4]==0);assert len(free);y,x=free[0]*4
for f in made:
 f[hd]=1;f[bridge]=1;f.smooth=True
 angles=[(math.atan2(v.co.y-.026,v.co.x+.011)/(2*math.pi))%1 for v in f.verts]
 if max(angles)-min(angles)>.5:angles=[a+1 if a<.5 else a for a in angles]
 for loop,a in zip(f.loops,angles):
  value=((x+16+a*128)/N,1-(y+8+(1.465-loop.vert.co.z)/.010*16)/N);loop[uv].uv=value;loop[buv].uv=value
bmesh.ops.recalc_face_normals(bm,faces=list(made));bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3]);bm.to_mesh(m);bm.free()
if m.has_custom_normals:m.normals_split_custom_set([(0,0,0)]*len(m.loops))


# Smooth head join.
bm=bmesh.new();bm.from_mesh(m);reg=bm.verts.layers.int['region'];verts=[v for v in bm.verts if v[reg]==0 and 1.44<v.co.z<1.48 and v.co.y>-.03]
for i in range(3):bmesh.ops.smooth_vert(bm,verts=verts,factor=.4,use_axis_x=True,use_axis_y=True,use_axis_z=False)
bm.to_mesh(m);bm.free()
if m.has_custom_normals:m.normals_split_custom_set([(0,0,0)]*len(m.loops))


# Close the temples and nape beneath the separated hair strands.
cap_uv={}
for face in m.polygons:
 for li in face.loop_indices:
  vi=m.loops[li].vertex_index
  if m.attributes['piece'].data[vi].value==105:cap_uv[vi]=m.uv_layers['HeadUV'].data[li].uv.copy()
for i,uv in cap_uv.items():
 v=m.vertices[i];dx=(uv.x-.01)/.008;dy=(uv.y-.01)/.008;fraction=min(1,math.hypot(dx,dy));angle=math.atan2(dy,dx);end=2.30;theta=end*fraction
 fade=min(1,max(0,(fraction-.55)/.45));fade=fade*fade*(3-2*fade)
 back=min(1,max(0,(math.sin(angle)+.5)/.5));back=back*back*(3-2*back)
 bottom=1.604+.072*math.cos(end);target=1.54-.04*max(0,math.sin(angle));side=(1-abs(math.sin(angle)))*fade*back
 v.co.x=-.020+.060*math.sin(theta)*math.cos(angle)*(1-.1*side)
 v.co.y=.025+.057*math.sin(theta)*math.sin(angle)+.015*side
 v.co.z=1.604+.072*math.cos(theta)-max(0,bottom-target)*fade*back
if m.has_custom_normals:m.normals_split_custom_set([(0,0,0)]*len(m.loops))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_textured_uv.blend'))
