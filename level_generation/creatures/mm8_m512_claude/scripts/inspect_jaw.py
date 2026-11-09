import bpy
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm8_wolf.blend'))
rig=bpy.data.objects['Wolf_Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
mesh=bpy.data.objects['Wolf'];group=mesh.vertex_groups['Jaw'].index
points=np.array([v.co[:] for v in mesh.data.vertices if sum(g.weight for g in v.groups if g.group==group)>.3])
for y0,y1 in [(-.55,-.49),(-.49,-.46),(-.46,-.43),(-.43,-.40)]:
    c=points[(points[:,1]>y0)&(points[:,1]<y1)]
    print('JAW',y0,y1,len(c),'center',np.median(c,axis=0).tolist(),'bounds',c.min(0).tolist(),c.max(0).tolist(),flush=True)
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.color_type='TEXTURE'
sc.display.shading.light='STUDIO';sc.display.shading.show_cavity=True
sc.world=bpy.data.worlds.new('ReviewWorld');sc.world.color=(.12,.12,.12)
sc.render.resolution_x=1000;sc.render.resolution_y=800;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam)
sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.45
for name,loc in [('front',(0,-2,.25)),('below',(0,-.43,-2)),('top',(0,-.43,2))]:
    center=Vector((0,-.43,.25));cam.location=loc;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=str(P/f'review/jaw_after_{name}.png');bpy.ops.render.render(write_still=True)
