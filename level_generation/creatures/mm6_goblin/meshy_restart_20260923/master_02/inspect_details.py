import bpy
from pathlib import Path
from mathutils import Vector
s=bpy.data.scenes['MM6 Goblin Restart - Master 02'];bpy.context.window.scene=s;c=s.camera;out=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/master_02/review')
s.render.resolution_x=800;s.render.resolution_y=800
for name,point,offset,scale in [('head_profile',(0,-.01,.71),(-4,-.05,0),.63),('head_front',(0,-.04,.73),(0,-4,0),.60),('right_hand',(-.49,-.04,.03),(-3,-4,.5),.49),('left_hand',(.49,-.04,.03),(3,-4,.5),.49)]:
 target=Vector(point);c.location=target+Vector(offset);c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=scale;s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
c.data.ortho_scale=2.17;c.location=(0,-4,0);c.rotation_euler=(Vector((0,0,0))-c.location).to_track_quat('-Z','Y').to_euler()
print('Rendered face and hand details')
