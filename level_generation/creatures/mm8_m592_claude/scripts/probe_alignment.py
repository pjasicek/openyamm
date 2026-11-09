from pathlib import Path
import bpy,numpy as np,json,sys
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'))
o=bpy.data.objects['P00'];co=np.array([tuple(o.matrix_world@v.co) for v in o.data.vertices]);np.save(P/'work/geometry_coordinates.npy',co)
sys.path.insert(0,str(P.parent/'mm6_ogr_claude/scripts'));import common
common.workbench_clay(bpy.context.scene)
cam=common.ortho_camera('top',(0,0,3),(0,0,0),2.2);bpy.context.scene.camera=cam;bpy.context.scene.render.resolution_x=900;bpy.context.scene.render.resolution_y=900;bpy.context.scene.render.filepath=str(P/'review/geometry/top.png');bpy.ops.render.render(write_still=True)
print('MATRIX',list(o.matrix_world),flush=True)
