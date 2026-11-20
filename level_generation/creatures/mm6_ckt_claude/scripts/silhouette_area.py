"""Front and side silhouette area (m^2) of the rest-pose Standing frame, for the binding scale."""
import bpy, numpy as np, os
from mathutils import Vector, Matrix
rig = bpy.data.objects['Ckt_Rig']; rig.animation_data.action = bpy.data.actions['Standing']; bpy.context.scene.frame_set(1)
mesh = bpy.data.objects['Cockatrice']
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'SINGLE'; sh.single_color = (1, 1, 1)
sh.background_type = 'VIEWPORT'; sh.background_color = (0, 0, 0)
N = 1000; S = 1.2; sc.render.resolution_x = sc.render.resolution_y = N
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = S
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for name, loc in (('front', (0, -3, 0.25)), ('side', (-3, 0, 0.25))):
    d = (Vector((0, 0, 0.25)) - Vector(loc)).normalized()
    cam.matrix_world = Matrix.Translation(Vector(loc)) @ d.to_track_quat('-Z', 'Y').to_matrix().to_4x4()
    p = f'/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/af1c507f-ae69-4496-b7d4-e4f312117d62/scratchpad/sil_{name}.png'
    sc.render.filepath = p; bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(p); a = np.array(img.pixels[:]).reshape(N, N, 4)[..., 0]
    print('AREA', name, round(float((a > 0.5).sum()) * (S / N) ** 2, 5))
