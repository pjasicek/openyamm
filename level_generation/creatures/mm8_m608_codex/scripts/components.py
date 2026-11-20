import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/"work/geometry_v1.blend"))
m=bpy.data.objects["Juggernaut"];bpy.context.view_layer.objects.active=m
bpy.ops.object.mode_set(mode="EDIT");bpy.ops.mesh.select_all(action="SELECT");bpy.ops.mesh.separate(type="LOOSE");bpy.ops.object.mode_set(mode="OBJECT")
info=[]
for o in sorted([o for o in bpy.data.objects if o.type=="MESH"],key=lambda o:-len(o.data.vertices)):
 c=[v.co for v in o.data.vertices];lo=[min(v[i] for v in c) for i in range(3)];hi=[max(v[i] for v in c) for i in range(3)];info.append(dict(name=o.name,vertices=len(c),triangles=len(o.data.polygons),bounds=[lo,hi]))
(P/"work/components.json").write_text(json.dumps(info,indent=2));print(info,flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/"work/components.blend"))
