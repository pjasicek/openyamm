"""Recover diagnostic piece labels from the retained UV charts, not adjacent cloth surfaces."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round4_before/work/export_reimport.blend'));body=bpy.data.objects['Body'];me=body.data;me.calc_loop_triangles();trees={};labels={};src=[]
for slot in [0,1]:
 coords=[];faces=[];tags=[]
 for tri in me.loop_triangles:
  if me.polygons[tri.polygon_index].material_index!=slot:continue
  inds=[]
  for li,vi in zip(tri.loops,tri.vertices):
   uv=me.uv_layers['UVMap'].data[li].uv;inds.append(len(coords));coords.append(Vector((uv.x,uv.y,0)))
  faces.append(inds);tags.append([me.attributes['piece'].data[vi].value for vi in tri.vertices])
 trees[slot]=BVHTree.FromPolygons(coords,faces);labels[slot]=tags
report={}
for level in [1,2,3]:
 for kind,file in [('selected',P/f'work/round4/selected_lod{level}.blend'),('final',P/f'work/round4/final_lod{level}.blend'),('accepted',P/f'work/round4/accepted_lod{level}.blend')]:
  bpy.ops.wm.open_mainfile(filepath=str(file));me=bpy.data.objects['Body'].data;votes={};old=[x.value for x in me.attributes['piece'].data]
  for poly in me.polygons:
   if poly.material_index not in trees:continue
   for li,vi in zip(poly.loop_indices,poly.vertices):
    uv=me.uv_layers['UVMap'].data[li].uv;loc,n,fi,d=trees[poly.material_index].find_nearest(Vector((uv.x,uv.y,0)))
    tag=max(set(labels[poly.material_index][fi]),key=labels[poly.material_index][fi].count);votes.setdefault(vi,[]).append(tag)
  changes=[]
  for vi,v in votes.items():
   tag=max(set(v),key=v.count)
   if old[vi]!=tag:changes.append([vi,old[vi],tag])
   me.attributes['piece'].data[vi].value=tag
  report[f'{kind}_lod{level}']={'changes':changes,'method':'Nearest accepted triangle in the same material UV chart, majority label per vertex; geometry, UVs, weights and action data unchanged.'};bpy.ops.wm.save_as_mainfile(filepath=str(file))
  if kind=='final':
   path=P/'scripts/skirt_intersections.py';s=path.read_text().replace("P/'work/export_reimport.blend'",f"P/'work/round4/final_lod{level}.blend'").replace("P/'review/skirt_intersections.json'",f"P/'review/round4/lod{level}/skirt_intersections_uv_labels.json'")
   exec(compile(s,str(path),'exec'),{'__file__':str(path),'__name__':'__main__'})
(P/'review/round4/diagnostic_labels.json').write_text(json.dumps(report,indent=2)+'\n')

