import bpy, json
from pathlib import Path
p = Path(__file__).resolve().parents[1]
bpy.ops.import_scene.gltf(filepath=str(p / "source/mm6_wdm_source.glb"))
rig = next(o for o in bpy.data.objects if o.type == "ARMATURE")
body = next(o for o in bpy.data.objects if o.type == "MESH" and o.name == "Demon")
print("SOURCE", rig.name, body.name, len(body.data.vertices), len(body.data.polygons), flush=True)
for b in rig.data.bones:
    print(b.name, [round(v,5) for v in b.head_local], b.parent.name if b.parent else None, flush=True)
for a in bpy.data.actions:
    print("ACTION",a.name,list(a.frame_range),flush=True)
print("FPS",bpy.context.scene.render.fps,flush=True)
print("OBJECT MATRIX",list(map(list,body.matrix_world)),flush=True)
print("RIG MATRIX",list(map(list,rig.matrix_world)),flush=True)
