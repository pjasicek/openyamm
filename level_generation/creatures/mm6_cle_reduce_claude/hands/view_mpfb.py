import bpy, json, math, sys
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath='mpfb_hands.blend')
F = json.load(open('mpfb_frames.json'))
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 400
L = F['HandL']; ax = Vector(L['axis']); c = Vector(L['centre'])
bpy.ops.mesh.primitive_cylinder_add(radius=L['r'], depth=0.3, location=c)
cyl = bpy.context.object; cyl.rotation_euler = ax.to_track_quat('Z', 'Y').to_euler()
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.25
for name in ('HandL', 'HandR'):
    for o in bpy.data.objects:
        if o.type == 'MESH': o.hide_render = o.name not in (name, 'Cylinder') or (name == 'HandR' and o.name == 'Cylinder')
    fr = F[name]; w = Vector(fr['wrist']); hd = Vector(fr['h']); t = Vector(fr['t']); n = Vector(fr['n'])
    ctr = w + hd * 0.08
    for v, d in (('palm', n), ('back', -n), ('thumb', t), ('pinky', -t), ('tip', hd)):
        cam.location = ctr + d.normalized() * 2; cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/fc464a9e-a7be-4d5c-b6c8-ca43b5ae23d9/scratchpad/mp_{name}_{v}.png'
        bpy.ops.render.render(write_still=True)
