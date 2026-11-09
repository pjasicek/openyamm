import bpy, sys, os
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=a[0])
sc=bpy.context.scene
for o in sc.objects:
    if o.type=='MESH' and 'utlass' not in o.name and 'lizardorc1' not in o.name: print('hide',o.name); o.hide_render=True
    if o.type=='MESH': print(o.name,[m.name for m in o.data.materials])
arm=next(o for o in sc.objects if o.type=='ARMATURE'); arm.animation_data.action=None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
sc.render.engine='BLENDER_WORKBENCH'; sh=sc.display.shading; sh.light='FLAT'; sh.color_type='TEXTURE'; sh.show_backface_culling=False
sc.render.resolution_x=sc.render.resolution_y=800
sc.world=bpy.data.worlds.new('w'); sc.world.color=(.42,.42,.42); sh.background_type='WORLD'
cd=bpy.data.cameras.new('c'); cd.type='ORTHO'; cd.ortho_scale=1.05; cam=bpy.data.objects.new('c',cd); sc.collection.objects.link(cam); sc.camera=cam
c=Vector((-.67,-.3,.15))
for n,d in {'n':(-.434,-.312,.845),'s':(0,.0,1.),'e':(1,0,.0),'f':(.9,-.19,.39)}.items():
    d=Vector(d).normalized(); cam.location=c+d*5; cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler(); sc.render.filepath=f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
