import bpy,sys,json
from pathlib import Path
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/runtime_reimport.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];staff=bpy.data.objects['Staff'];pv=[a.value for a in body.data.attributes['piece'].data]
def co(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=[x.co.copy() for x in m.vertices];ev.to_mesh_clear();return v
for role,f,i in [('Walking',15,737)]:
 rig.animation_data.action=bpy.data.actions[role];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(f)
 v=co(body);s=co(staff);faces=[tuple(f.vertices) for f in body.data.polygons if all(pv[i]!=3 for i in f.vertices)];tree=BVHTree.FromPolygons(v,faces);q,n,j,d=tree.find_nearest(s[i]);ids=faces[j]
 print('CONTACT',role,'staff',list(s[i]),'body',list(q),'piece',[pv[x] for x in ids],'ids',ids,'weights',[[(body.vertex_groups[g.group].name,round(g.weight,2)) for g in body.data.vertices[x].groups] for x in ids],flush=True)
 common.workbench_clay(bpy.context.scene,textured=True);common.render_views(str(p/'review/round1'/('contact_'+role)),.95,2.5,views=('front','left','three_quarter'),resolution=(600,750))
