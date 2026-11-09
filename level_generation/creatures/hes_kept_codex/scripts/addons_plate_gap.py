import bpy,sys,os
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];path=P/'work/addons_v2/equipped.blend';bpy.ops.wm.open_mainfile(filepath=str(path))
for v in bpy.data.objects['hes_kept_plate'].data.vertices:
 p=v.co;p+=Vector((p.x+.03255,p.y-.022,0)).normalized()*.004
bpy.ops.wm.save_as_mainfile(filepath=str(path));sys.stdout.flush();sys.stderr.flush();os._exit(0)
