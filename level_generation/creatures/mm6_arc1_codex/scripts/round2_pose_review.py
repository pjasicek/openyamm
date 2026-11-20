import bpy,sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];prop=bpy.data.objects['BowAsset'];sc=bpy.context.scene
names={g.index:g.name for g in b.vertex_groups};keep=[sum(g.weight for g in v.groups if 'Hand'in names[g.group]or'Finger'in names[g.group])<=.5 for v in b.data.vertices];faces=[tuple(f.vertices)for f in b.data.polygons if all(keep[i]for i in f.vertices)]
for clip,f,idx in [('Standing',44,370),('Walking',23.75,370)]:
 a=bpy.data.actions[clip];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(int(f),subframe=f-int(f));deps=bpy.context.evaluated_depsgraph_get()
 def posed(o):
  e=o.evaluated_get(deps);m=e.to_mesh();v=[x.co.copy()for x in m.vertices];e.to_mesh_clear();return v
 v=posed(b);q=posed(prop);tree=BVHTree.FromPolygons(v,faces);p,n,i,d=tree.find_nearest(q[idx]);ids=faces[i]
 print('COLLIDER',clip,'bow_vertex',idx,tuple(q[idx]),'body_pieces',[b.data.attributes['piece'].data[j].value for j in ids],'body_bones',[[names[g.group]for g in b.data.vertices[j].groups if g.weight>.2]for j in ids],flush=True)
 common.workbench_clay(sc,True);common.render_views(str(P/f'review/round2/carry_{clip}'),.87,1.95,views=('front','left'),resolution=(600,900))
