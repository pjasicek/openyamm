import bpy,bmesh,math,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'));o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data_clear()
for pb in rig.pose.bones:pb.matrix_basis.identity()
me=o.data;bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
for slot in range(2):
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
 for f in me.polygons:f.select=f.material_index==slot
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.004,area_weight=0,correct_aspect=True,scale_to_bounds=True);bpy.ops.uv.pack_islands(rotate=True,margin=.004,margin_method='FRACTION');bpy.ops.object.mode_set(mode='OBJECT')
me.calc_loop_triangles();stats={}
for slot,label in enumerate(['body','head']):
 ratios=[]
 for t in me.loop_triangles:
  if t.material_index!=slot:continue
  xyz=np.array([me.vertices[i].co[:] for i in t.vertices]);uv=np.array([me.uv_layers.active.data[i].uv[:] for i in t.loops]);a=np.linalg.norm(np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]))*.5;b=abs(np.linalg.det(np.column_stack([uv[1]-uv[0],uv[2]-uv[0]])))*.5
  if a>1e-10:assert b>1e-13,(slot,t.polygon_index);ratios.append(b/a)
 stats[label]={'triangles':len(ratios),'uv_density':np.percentile(ratios,[1,5,50,95,99]).tolist()}
 dup=o.copy();dup.data=me.copy();dup.parent=None;dup.modifiers.clear();dup.vertex_groups.clear();bpy.context.collection.objects.link(dup);bm=bmesh.new();bm.from_mesh(dup.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=slot],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(dup.data);bm.free();dup.data.materials.clear();m=bpy.data.materials.new('Neutral');m.use_nodes=True;dup.data.materials.append(m)
 for f in dup.data.polygons:f.material_index=0
 bpy.ops.object.select_all(action='DESELECT');dup.select_set(True);bpy.context.view_layer.objects.active=dup
 bpy.ops.export_scene.gltf(filepath=str(P/'work'/f'{label}_upload.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False,export_morph=False);bpy.data.objects.remove(dup,do_unlink=True)
bpy.context.view_layer.objects.active=o;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_uv.blend'));(P/'work/uv_report.json').write_text(json.dumps(stats,indent=2));print('UV',stats)
