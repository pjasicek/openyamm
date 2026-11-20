import bpy,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1/adaptive_subpixel_lod3/step_06.blend'));s=bpy.context.scene;c=s.camera;print('CAMERA_ACTUAL',c.data.angle,c.data.angle_x,c.data.angle_y,s.render.pixel_aspect_x,s.render.pixel_aspect_y,c.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=960,y=960));print('THEORY_FOCAL',480/math.tan(math.radians(35)/2))
