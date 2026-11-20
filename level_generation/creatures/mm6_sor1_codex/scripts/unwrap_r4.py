"""UV-only candidate: coherent robe cylinder and independent garment/anatomy pieces."""
import bpy,math,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/round3_lod0.blend'));o=bpy.data.objects['Body'];m=o.data
for x in bpy.context.selected_objects:x.select_set(False)
o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.context.tool_settings.mesh_select_mode=(False,False,True)
parts=np.array([a.value for a in m.attributes['piece'].data]);old=np.array([v.uv[:] for v in m.uv_layers.active.data]);uv=m.uv_layers.active
# Long seams follow piece borders and the side planes of the garment/anatomy shells.
mid={part:np.median([v.co.y for v in m.vertices if parts[v.index]==part]) for part in set(parts)}
finger=np.array([a.value for a in m.attributes['finger'].data]);group={}
finger_mid={(pt,k):np.median([v.co.y for v in m.vertices if parts[v.index]==pt and finger[v.index]==k]) for pt in [3,4] for k in range(6)}
for face in m.polygons:
 pt=int(parts[face.vertices[0]]);c=face.center;region=0
 if pt==1:region=1 if c.x<-.21 else 2 if c.x>.21 else 3 if c.z>1.40 else 0
 if pt in [3,4]:region=int(np.bincount(np.maximum(finger[list(face.vertices)],0)).argmax())
 group[face.index]=(pt,region,int(c.y>finger_mid[(pt,region)]) if pt in [3,4] else int(c.y>mid[pt]))
edges={}
for f in m.polygons:
 for key in f.edge_keys:edges.setdefault(tuple(sorted(key)),[]).append(f.index)
for e in m.edges:
 adjacent=edges.get(tuple(sorted(e.vertices)),[]);e.use_seam=len(adjacent)!=2 or group[adjacent[0]]!=group[adjacent[1]]
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.unwrap(method='ANGLE_BASED',margin=0);bpy.ops.object.mode_set(mode='OBJECT')
m=o.data;uv=m.uv_layers.active
# A single longitudinal seam at the back avoids seams across the front embroidery and robe panels.
for f in m.polygons:
 if not all(parts[v]==100 for v in f.vertices):continue
 co=np.array([m.vertices[v].co[:] for v in f.vertices]);a=np.arctan2(co[:,0],co[:,1]+.02);a=np.where(a<0,a+2*math.pi,a)
 if np.ptp(a)>math.pi:a=np.where(a>math.pi,a-2*math.pi,a)
 for li,t,z in zip(f.loop_indices,a,co[:,2]):uv.data[li].uv=(t/(2*math.pi),z)
m.calc_loop_triangles();np.savez_compressed(p/'work/uv_unpacked_r4.npz',vertices=np.array([v.co[:] for v in m.vertices]),faces=np.array([t.vertices[:] for t in m.loop_triangles]),uv=np.array([[uv.data[i].uv[:] for i in t.loops] for t in m.loop_triangles]),loops=np.array([t.loops[:] for t in m.loop_triangles]),part=parts,material=np.array([t.material_index for t in m.loop_triangles]),old_loop_uv=old)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/round4_uv_unpacked.blend'))
