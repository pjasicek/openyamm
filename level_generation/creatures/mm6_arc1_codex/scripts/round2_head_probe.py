import bpy,json,math,numpy as np,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
def act(n,f):
 a=bpy.data.actions[n];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(int(f),subframe=f-int(f))
results={}
for label,path in [(f'lod{i}',f'work/round2/lod{i}.blend')for i in range(4)]:
 bpy.ops.wm.open_mainfile(filepath=str(P/path));r=bpy.data.objects['Rig'];sc=bpy.context.scene;report={'head_contacts_cm':{}}
 exec("body=bpy.data.objects['Body'];piece=[x.value for x in body.data.attributes['piece'].data];gn={g.index:g.name for g in body.vertex_groups};heads=[v.index for v in body.data.vertices if sum(g.weight for g in v.groups if gn[g.group]=='B_Head')>.5];faces=[tuple(f.vertices)for f in body.data.polygons if all(piece[i]in([4]+list(range(13,20)))for i in f.vertices)]\nfor a in bpy.data.actions:\n worst=0;worst_info=None;raw_worst=0\n for f in np.linspace(0,float(a.frame_range[1]),math.ceil(a.frame_range[1]*48/30)+1):\n  act(a.name,float(f));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=[x.co.copy()for x in m.vertices];ev.to_mesh_clear();tree=BVHTree.FromPolygons(v,faces)\n  for i in heads:\n   p,n,idx,d=tree.find_nearest(v[i],.03)\n   if p is not None and (v[i]-p).dot(n)<-.7*d and d>worst:\n    raw_worst=max(raw_worst,d)\n    # The open quiver lip has coincident inner/outer faces. A single nearest normal is not an inside test.\n    inside=0\n    for direction in [(1,.371,.123),(-1,.217,.623),(.137,1,.341),(.539,-1,.269)]:\n     direction=Vector(direction).normalized();start=v[i].copy();count=0\n     for k in range(20):\n      hit,normal,face,distance=tree.ray_cast(start,direction)\n      if hit is None:break\n      count+=1;start=hit+direction*.00001\n     inside+=count%2\n    if inside>=3:worst=d;worst_info={'frame':float(f),'vertex':i,'piece':piece[i],'point':list(v[i]),'nearest':list(p),'hit_piece':piece[faces[idx][0]]}\n report['head_contacts_cm'][a.name]=worst*100\n print('HEAD CONTACT',a.name,worst,worst_info,'raw_nearest_normal_depth',raw_worst)\n")
 results[label]=report
(P/'review/round2/reduction/head_selected.json').write_text(json.dumps(results,indent=2));print('HEAD_PROBE',results)

assert all(max(r['head_contacts_cm'].values())<=1 for r in results.values()),results
