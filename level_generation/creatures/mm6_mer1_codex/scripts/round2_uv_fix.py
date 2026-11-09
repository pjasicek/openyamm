import bpy,bmesh,numpy as np,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
print('SMART PARAM',bpy.ops.uv.smart_project.get_rna_type().properties['angle_limit'].default,bpy.ops.uv.smart_project.get_rna_type().properties['angle_limit'].hard_max,flush=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/body_lod0.blend'));o=bpy.data.objects['Body'];me=o.data;bm=bmesh.new();bm.from_mesh(me);before=len(bm.verts);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bm.to_mesh(me);bm.free();print('WELD',before,len(me.vertices),len(me.polygons),flush=True)
for e in me.edges:e.use_seam=False;e.use_edge_sharp=False
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.context.tool_settings.mesh_select_mode=(False,False,True)
for mi in [0,1]:
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
 for f in me.polygons:f.select=f.material_index==mi
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=1.55,island_margin=(.017 if mi==0 else .033),margin_method='FRACTION',area_weight=.25,correct_aspect=True,scale_to_bounds=True);bpy.ops.object.mode_set(mode='OBJECT')
 me.calc_loop_triangles();uv=me.uv_layers.active.data;areas=[]
 for t in me.loop_triangles:
  if me.polygons[t.polygon_index].material_index!=mi:continue
  q=np.array([uv[i].uv[:]for i in t.loops]);a=q[1]-q[0];b=q[2]-q[0];areas.append(abs(a[0]*b[1]-a[1]*b[0]))
 print('UV AREA',mi,float(sum(areas)),sum(x>1e-9 for x in areas),len(areas),flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2/bake_target.blend'))
