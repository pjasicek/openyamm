"""Close-ups of the source and ladder candidates (work/<blend>) for the MM7 Ooze (faces -y): blob top, front, side,
back and the rim up close, Walking hump, Hit cone, the pod at its tallest and its knob (Attack), the lash, the swollen
knob (Cast), the Death column, the Dead globules, the Fidget bubbles; textured (Eevee) and clay (workbench + cavity). The welded source's custom normals are
rotated by the weld, so they are cleared here (judge final shading from GLBs, glb_close.py).
Usage: blender -b -P close_ooze.py -- <blend> <Cand_75,...> [spot,...]  -> review/close/<label>_<spot>_<mode>.png"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', args[0]))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; src = bpy.data.objects['Body']
bpy.context.view_layer.objects.active = src; src.select_set(True)
bpy.ops.mesh.customdata_custom_splitnormals_clear()
objs = {'source': src, **{c.replace('Cand_', 'r'): bpy.data.objects[c] for c in args[1].split(',')}}
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = True
cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
if cam.name not in sc.collection.objects:
    sc.collection.objects.link(cam)
sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.clip_end = 10
sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get('CLOSE_RES', '420'))
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (.8, .78, .74); sc.display.shading.show_cavity = True; sc.display.shading.cavity_type = 'BOTH'
pb = rig.pose.bones
bone = lambda n: rig.matrix_world @ ((pb[n].head + pb[n].tail) / 2)
SPOTS = {'top': ('Standing', 0, 'Lump_C', 1.15, (.1, -.2, 1)), 'front': ('Standing', 0, 'Lump_C', 1.15, (0, -1, .3)),
         'side_r': ('Standing', 0, 'Lump_C', 1.15, (1, 0, .25)), 'back': ('Standing', 0, 'Lump_C', 1.15, (-.3, 1, .35)),
         'rim_front': ('Standing', 0, 'Lump_0', .55, (.2, -1, .12)), 'rim_left': ('Standing', 0, 'Lump_4', .55, (-1, .2, .12)),
         'walk': ('Walking', 9, 'Lump_C', 1.25, (.7, -.7, .45)), 'hit': ('Hit', 9, 'Lump_C', 1.2, (-.7, -.7, .35)),
         'attack_up': ('Attack', 12, 'Pod3', 1.0, (1, -.15, .15)), 'knob': ('Attack', 12, 'Knob', .42, (.6, -.8, .25)),
         'attack_lash': ('Attack', 16, 'Pod3', 1.0, (1, 0, .15)), 'cast_swell': ('Cast', 16, 'Knob', .55, (.6, -.8, .2)),
         'death': ('Death', 6, 'Lump_C', 1.0, (.7, -.7, .4)), 'dead': ('Dead', 0, 'Lump_C', 1.8, (.5, -.6, .9)),
         'fidget': ('Fidget', 7, 'Lump_C', .9, (.6, -.7, .5))}
if len(args) > 2:
    SPOTS = {k: SPOTS[k] for k in args[2].split(',')}
out = os.path.join(HERE, 'review', 'close'); os.makedirs(out, exist_ok=True)
for spot, (act, frame, b, size, d) in SPOTS.items():
    rig.animation_data.action = bpy.data.actions[act]; sc.frame_set(frame)
    c = bone(b); cam.location = c + Vector(d).normalized() * 3
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
    for label, o in objs.items():
        for p in objs.values():
            p.hide_render = p is not o
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('CLOSE', list(objs), list(SPOTS))
