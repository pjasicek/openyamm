"""Hidden-leg poke-through: flat renders (front, back, both sides) with the hidden leg piece above 17 cm (rest) in red
and everything else white, every 2nd frame of every clip; counts red pixels per frame for the source and a ladder
candidate (whose leg faces are kept source faces, found by src_index). The legs show only where the dress does not
cover them, so a reduced dress that lets the legs through raises the count. Usage:
blender -b -P leg_poke.py -- <ladder blend> <Cand_82> -> work/leg_poke_<cand>.json"""
import os, sys, json, bpy, numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
blend, cn = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', blend))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; src = bpy.data.objects['Body']; cand = bpy.data.objects[cn]
d = np.load(os.path.join(HERE, 'work/mesh_in.npz')); g = np.load(os.path.join(HERE, 'work/groups.npy'))
f, v = d['faces'], d['verts']
legv = np.zeros(len(v), bool); legv[f[g == 5].ravel()] = True; legv &= v[:, 2] > .17
src_leg = legv[f].all(1)
cd = np.load(os.path.join(HERE, 'work', f"mesh_r{cn.split('_')[1]}.npz")); si = cd['src_index']
cv = np.where(si >= 0, legv[np.maximum(si, 0)], False); cand_leg = cv[cd['faces']].all(1)
white = bpy.data.materials.new('W'); white.diffuse_color = (1, 1, 1, 1)
red = bpy.data.materials.new('R'); red.diffuse_color = (1, 0, 0, 1)
for o, leg in ((src, src_leg), (cand, cand_leg)):
    o.data.materials.clear(); o.data.materials.append(white); o.data.materials.append(red)
    o.data.polygons.foreach_set('material_index', leg.astype(np.int32))
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'MATERIAL'
sh.show_cavity = False; sh.show_backface_culling = False
sc.render.film_transparent = True; sc.render.resolution_x = sc.render.resolution_y = 256
cam = bpy.data.objects.new('PokeCam', bpy.data.cameras.new('PokeCam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.2; cam.data.clip_end = 20
tmp = os.path.join(HERE, 'work', 'poke.png'); out = {}
for act in bpy.data.actions:
    rig.animation_data.action = act; f0, f1 = (int(x) for x in act.frame_range)
    for fr in range(f0, f1 + 1, 2):
        sc.frame_set(fr); c = rig.matrix_world @ rig.pose.bones['B_Pelvis'].head
        for view, dv in (('front', (0, -1, 0)), ('back', (0, 1, 0)), ('left', (1, 0, 0)), ('right', (-1, 0, 0))):
            cam.location = c + Vector(dv) * 5; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
            for label, o in (('source', src), ('cand', cand)):
                for p in (src, cand):
                    p.hide_render = p is not o
                sc.render.filepath = tmp; bpy.ops.render.render(write_still=True)
                px = np.array(bpy.data.images.load(tmp, check_existing=False).pixels[:]).reshape(-1, 4)
                n = int(((px[:, 0] > .5) & (px[:, 1] < .3) & (px[:, 3] > .5)).sum())
                out.setdefault(f'{act.name}:{fr}:{view}', {})[label] = n
tot = {k: sum(x[k] for x in out.values()) for k in ('source', 'cand')}
worse = {k: x for k, x in out.items() if x['cand'] > x['source'] + 5}
json.dump({'total': tot, 'worse': worse, 'frames': out}, open(os.path.join(HERE, 'work', f'leg_poke_{cn}.json'), 'w'), indent=1)
print('LEGPOKE', cn, 'total red pixels', tot, 'views worse by >5 px', len(worse), sorted(worse.items(), key=lambda kv: kv[1]['source'] - kv[1]['cand'])[:8])
