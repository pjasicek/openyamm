"""Two UV domains: a dedicated head set and a full-body Meshy unwrap upload."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();me=body.data;body.data.materials.clear()
for name in ['HarpyBody','HarpyHead']:
 m=bpy.data.materials.new(name);m.use_nodes=True;body.data.materials.append(m)
hg=body.vertex_groups['Head'].index
for f in me.polygons:
 w=sum(sum(g.weight for g in me.vertices[i].groups if g.group==hg) for i in f.vertices)/len(f.vertices)
 c=sum((me.vertices[i].co for i in f.vertices),start=me.vertices[f.vertices[0]].co*0)/len(f.vertices)
 f.material_index=int(w>.4 or (abs(c.x+.01)<.11 and c.y>.135 and c.z>1.33))
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
for slot in [0,1]:
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
 for f in me.polygons:f.select=f.material_index==slot
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=math.radians(50),island_margin=.004,area_weight=0,correct_aspect=True,scale_to_bounds=True);bpy.ops.uv.pack_islands(rotate=True,margin=.004,margin_method='FRACTION');bpy.ops.object.mode_set(mode='OBJECT')
me.calc_loop_triangles();uv=me.uv_layers.active;stats={}
for slot in [0,1]:
 ratios=[];bad=[]
 for t in me.loop_triangles:
  if t.material_index!=slot:continue
  c=np.array([me.vertices[i].co[:] for i in t.vertices]);u=np.array([uv.data[i].uv[:] for i in t.loops]);a=np.linalg.norm(np.cross(c[1]-c[0],c[2]-c[0]))*.5;b=abs(np.linalg.det(np.column_stack([u[1]-u[0],u[2]-u[0]])))*.5
  if a>1e-10:
   if b<1e-12:bad.append(t.polygon_index)
   ratios.append(b/a)
 assert not bad,('Collapsed UVs',slot,bad)
 stats[str(slot)]={'triangles':len(ratios),'density_percentiles':np.percentile(ratios,[1,5,50,95]).tolist()}
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_uv.blend'));(P/'texturing').mkdir(exist_ok=True)
for label in ['body_full','head']:
 obj=body.copy();obj.data=me.copy();obj.parent=None;obj.modifiers.clear();obj.vertex_groups.clear();bpy.context.collection.objects.link(obj)
 if label=='head':
  bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=1],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(obj.data);bm.free()
 obj.data.materials.clear();m=bpy.data.materials.new('Neutral');m.use_nodes=True;obj.data.materials.append(m)
 for f in obj.data.polygons:f.material_index=0
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 bpy.ops.export_scene.gltf(filepath=str(P/'texturing'/f'hrp_{label}_upload.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False,export_morph=False)
 bpy.data.objects.remove(obj,do_unlink=True)
(P/'work/uv_stats.json').write_text(json.dumps(stats,indent=2));print('UV',stats,flush=True)
