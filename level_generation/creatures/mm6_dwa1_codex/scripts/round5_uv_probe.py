import bpy,sys,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True;import round4_search as S
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round4_before/work/export_reimport.blend'));S.reset();high={}
for name in ['Body','Axe']:
 ob=bpy.data.objects[name];me=ob.data;me.calc_loop_triangles();d={}
 for tri in me.loop_triangles:
  points=[tuple(round(float(x),5)for x in me.vertices[i].co)for i in tri.vertices];key=tuple(sorted(points));d[key]=(dict(zip(points,[me.uv_layers.active.data[i].uv[:]for i in tri.loops])),tri.material_index)
 high[name]=d
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round5/authoring_source.blend'));S.reset()
for name in ['Body','Axe']:
 me=bpy.data.objects[name].data;me.calc_loop_triangles();errors=[];missing=0;matwrong=0
 for tri in me.loop_triangles:
  points=[tuple(round(float(x),5)for x in me.vertices[i].co)for i in tri.vertices];key=tuple(sorted(points));h=high[name].get(key)
  if h is None:missing+=1;continue
  matwrong+=h[1]!=tri.material_index
  for point,li in zip(points,tri.loops):errors.append(np.linalg.norm(np.array(me.uv_layers.active.data[li].uv)-h[0][point]))
 print('UV_PROBE',name,missing,matwrong,np.percentile(errors,[0,50,99,100]).tolist(),flush=True)
