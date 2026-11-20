"""Close-ups of the source and ladder candidates (work/<blend>) for the MM7 Devil (faces -y, 1.7 m): face front,
three-quarter, side and mouth, horns from above, head and shoulder spikes from behind, chest, arm spikes, both clawed
hands and the claws in the attack, both feet, heel spurs, legs, hips, tail root and tail, Attack, Running, Death; textured (Eevee) and clay
(workbench + cavity). The welded source's custom normals are rotated by the weld, so they are cleared here (judge
final shading from GLBs, glb_close.py).
Usage: blender -b -P close_m178.py -- <blend> <Cand_75,...> [spot,...]  -> review/close/<label>_<spot>_<mode>.png"""
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
VG = {g.index: g.name for g in src.vertex_groups}
DOM = [max(v.groups, key=lambda g: g.weight).group if v.groups else -1 for v in src.data.vertices]


def bone(n):
    # 'V:<group>': centroid of the posed source vertices dominated by that group (the clawed hands reach 60 cm below
    # the wrist, so the bone midpoint frames the forearm)
    if n.startswith('P:'):   # a rest-pose point (use with the REST pseudo clip)
        return Vector([float(x) for x in n[2:].split(';')])
    if n.startswith('V:'):
        ids = [i for i, g in enumerate(DOM) if g >= 0 and VG[g] == n[2:]]
        ev = src.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        c = sum((src.matrix_world @ m.vertices[i].co for i in ids), Vector()) / len(ids); ev.to_mesh_clear(); return c
    return rig.matrix_world @ ((pb[n].head + pb[n].tail) / 2)
SPOTS = {'face_front': ('Standing', 0, 'B_Head', .32, (0, -1, .1)), 'face_q34': ('Standing', 0, 'B_Head', .36, (-.7, -.7, .2)),
         'face_l': ('Standing', 0, 'B_Head', .36, (1, -.1, .05)), 'helmet_back': ('Standing', 0, 'B_Head', .45, (.3, 1, .5)),
         'chest': ('Standing', 0, 'B_Spine1', .75, (0, -1, .1)), 'back': ('Standing', 0, 'B_Spine1', .8, (0, 1, .15)),
         'shoulder_r': ('Standing', 0, 'B_R_UpperArm', .45, (-.8, -.4, .4)), 'shoulder_l': ('Standing', 0, 'B_L_UpperArm', .45, (.8, -.4, .4)),
         'fists': ('Standing', 0, 'B_Spine', .6, (-.3, -1, .2)), 'fist_r': ('Standing', 0, 'V:B_R_Hand', .25, (-.6, -.7, .3)), 'hand_r_in': ('Standing', 0, 'V:B_R_Hand', .25, (.6, -.6, .1)),
         'fist_l': ('Standing', 0, 'V:B_L_Hand', .25, (.5, -.8, .3)),
         'belt': ('Standing', 0, 'B_Pelvis', .6, (.3, -1, .1)), 'tabard_low': ('Standing', 0, 'B_Pelvis', .8, (0, -1, -.2)),
         'knees': ('Standing', 0, 'B_R_Calf', .7, (-.2, -1, .2)), 'boots': ('Standing', 0, 'B_R_Foot', .7, (-.3, -1, .4)),
         'legs_side': ('Standing', 0, 'B_R_Calf', 1.0, (-1, 0, .05)),
         'tabard_front': ('REST', 0, 'P:0;-0.1;0.75', .55, (0, -1, .05)), 'torso_front': ('REST', 0, 'P:0;-0.1;1.15', .5, (0, -1, .05)),
         'coat_r': ('REST', 0, 'P:-0.22;0;0.7', .6, (-1, -.2, .05)), 'coat_l': ('REST', 0, 'P:0.22;0;0.7', .6, (1, -.2, .05)),
         'coat_back': ('REST', 0, 'P:0;0.1;0.75', .7, (0, 1, .05)),
         'fidget': ('Fidget', 70, 'V:B_L_Hand', .35, (.2, -1, .3)), 'hit': ('Hit', 12, 'B_Spine1', 2.0, (-.7, -.7, .3)),
         'walk': ('Walking', 6, 'B_Spine1', 2.0, (-.5, -1, .2)), 'death': ('Death', 38, 'B_Pelvis', 2.2, (.6, -.6, .6))}
if len(args) > 2:
    SPOTS = {k: SPOTS[k] for k in args[2].split(',')}
out = os.path.join(HERE, 'review', 'close'); os.makedirs(out, exist_ok=True)
for spot, (act, frame, b, size, d) in SPOTS.items():
    if act == 'REST':
        rig.animation_data.action = None
        for p_ in pb:
            p_.matrix_basis.identity()
        bpy.context.view_layer.update()
    else:
        rig.animation_data.action = bpy.data.actions[act]; sc.frame_set(frame)
    c = bone(b); cam.location = c + Vector(d).normalized() * 6
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
    for label, o in objs.items():
        for p in objs.values():
            p.hide_render = p is not o
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('CLOSE', list(objs), list(SPOTS))
