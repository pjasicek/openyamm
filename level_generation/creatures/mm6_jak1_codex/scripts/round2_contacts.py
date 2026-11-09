import bpy,runpy,sys,json
from pathlib import Path
from collections import Counter
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_master.blend'));bpy.data.objects['Jackalman'].name='Body';bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_gate_master.blend'))
roles=['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']
for script in ['g6_contacts.py','g6_skirt_poke.py']:
 sys.argv=[script,'--',str(P/'work/final_gate_master.blend'),*roles];runpy.run_path(str(P/'scripts'/script),run_name='__main__')
body=bpy.data.objects['Body'];me=body.data;pv=[a.value for a in me.attributes['piece'].data];sp=[p for p in me.polygons if pv[p.vertices[0]]==1 and p.normal.dot(Vector((p.center.x,p.center.y,0)).normalized())>.25];edges=Counter(tuple(sorted((p.vertices[i],p.vertices[(i+1)%len(p.vertices)]))) for p in sp for i in range(len(p.vertices)));rim=[e for e,n in edges.items() if n==1];rig=bpy.data.objects['Rig']
for role,row in json.loads((P/'work/g6_fauld.json').read_text()).items():
 if row['frame'] is None:continue
 rig.animation_data.action=bpy.data.actions[role];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(int(row['frame']));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();point=Vector(row['cloth_point']);distance=[]
 for i,j in rim:
  a,b=mesh.vertices[i].co,mesh.vertices[j].co;ab=b-a;t=max(0,min(1,(point-a).dot(ab)/max(ab.length_squared,1e-12)));distance.append(((point-a-ab*t).length,(i,j)))
 vi=me.vertices[row['skin_vertex']];print('SKIRT DIAGNOSTIC',role,'rim',min(distance),'rest',tuple(vi.co),'weights',[(body.vertex_groups[g.group].name,g.weight) for g in vi.groups],flush=True);ev.to_mesh_clear()

for script,args in [("g6_staff_mesh.py",[P/"export/mm6_jak1_runtime_lod0.glb"]),("grip_floor_audit.py",[])]:
 sys.argv=[script,"--",*map(str,args)];runpy.run_path(str(P/"scripts"/script),run_name="__main__")
