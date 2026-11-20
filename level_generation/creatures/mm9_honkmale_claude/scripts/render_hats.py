import bpy, sys, math, os
from mathutils import Vector
for g,p in (('source/mm9/honkhat.glb','hat'),('source/mm9/elderhonkhat.glb','elder')):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=g)
    sc=bpy.context.scene
    dg=bpy.context.evaluated_depsgraph_get()
    pts=[]
    for o in sc.objects:
        if o.type=='MESH':
            pts+=[o.matrix_world@v.co for v in o.data.vertices]
    c=Vector([(min(p_[i] for p_ in pts)+max(p_[i] for p_ in pts))/2 for i in range(3)])
    print('HAT',g,[max(p_[i] for p_ in pts)-min(p_[i] for p_ in pts) for i in range(3)], len(pts))
    sc.render.engine='BLENDER_WORKBENCH'
    sh=sc.display.shading; sh.light='STUDIO'; sh.color_type='TEXTURE'; sh.show_backface_culling=False
    sc.render.resolution_x=sc.render.resolution_y=400
    w=bpy.data.worlds.new('w'); sc.world=w; w.color=(.4,.4,.4); sh.background_type='WORLD'
    cd=bpy.data.cameras.new('cam'); cd.type='ORTHO'; cd.ortho_scale=0.7; cd.clip_end=100
    cam=bpy.data.objects.new('cam',cd); sc.collection.objects.link(cam); sc.camera=cam
    for v,d in {'a':Vector((-1,-1.2,.5)),'b':Vector((1,0,.1)),'c':Vector((0,1,.1))}.items():
        d=d.normalized(); cam.location=c+d*10
        cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler()
        sc.render.filepath=os.path.abspath(f'work/refs/{p}_{v}.png'); bpy.ops.render.render(write_still=True)
