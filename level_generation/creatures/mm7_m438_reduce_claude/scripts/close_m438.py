"""Close-ups of the source and ladder candidates (work/<blend>) for the MM7 Zombie (zspots.py: face, head and
headband, chest and flank wounds, back, stump and its bone shafts, the fist, trouser holes front/back, knees, the
lathe right shin and its rods, feet, rope, Fidget neck, Attack, Walking, Death); textured (Eevee) and clay
(workbench + cavity). The welded source's custom normals are rotated by the weld, so they are cleared here (judge
final shading from GLBs, glb_close.py).
Usage: blender -b -P close_m438.py -- <blend> <Cand_75,...> [spot,...]  -> review/close/<blend label>_<cand>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zspots import SPOTS, centre
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', args[0]))
tag = args[0].replace('ladder_', '').replace('.blend', '')
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; src = bpy.data.objects['Body']
bpy.context.view_layer.objects.active = src; src.select_set(True)
bpy.ops.mesh.customdata_custom_splitnormals_clear()
objs = {'source': src, **{f"{tag}{c.replace('Cand_', 'r')}": bpy.data.objects[c] for c in args[1].split(',') if c}}
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = True
cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
if cam.name not in sc.collection.objects:
    sc.collection.objects.link(cam)
sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.clip_end = 20
sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get('CLOSE_RES', '420'))
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (.8, .78, .74); sc.display.shading.show_cavity = True; sc.display.shading.cavity_type = 'BOTH'
spots = SPOTS if len(args) < 3 else {k: SPOTS[k] for k in args[2].split(',')}
out = os.path.join(HERE, 'review', 'close'); os.makedirs(out, exist_ok=True)
for spot, (act, frame, b, size, d) in spots.items():
    rig.animation_data.action = bpy.data.actions[act]; sc.frame_set(frame)
    c = centre(rig, b); cam.location = c + Vector(d).normalized() * 6
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
    for label, o in objs.items():
        if label == 'source' and os.environ.get('SKIP_SOURCE') == '1':
            continue
        for p in objs.values():
            p.hide_render = p is not o
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('CLOSE', list(objs), list(spots))
