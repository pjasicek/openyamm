"""Renders of the v2 clips at the native frame times and directions (Blender), for review/motion_vs_native and the
motion gate (scripts/motion_gate.py).

Camera as in the fitter (scripts/fit_native.py): orthographic, elevation and scale from work/v2/fit/calibration.json
(1 x2 pixel = 1 / (2 * scale) m), view k orbiting the dragon's right side by 45 deg per step. Each shot is rendered
twice at 576 px: a silhouette (alpha) and a textured workbench image (base colour, studio light).
Usage: motion_render.py -- <anim.blend> <outdir>"""
import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector
P = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); out = Path(a[1]); out.mkdir(parents=True, exist_ok=True)
cal = json.loads((P / 'work/v2/fit/calibration.json').read_text()); elev = cal['elevation_rad']; scale = cal['scale_px_per_m_at_256']
body = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; sc = bpy.context.scene
for slot, label in enumerate(['body', 'head', 'wings']):
    m = body.data.materials[slot]; m.use_nodes = True; nt = m.node_tree
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(str(P / f'textures/dragon_{label}_basecolor_2k.png'))
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None:
        bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); outn = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'); nt.links.new(bsdf.outputs[0], outn.inputs[0])
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = 576; sc.render.resolution_percentage = 100
cam = bpy.data.objects.new('MC', bpy.data.cameras.new('MC')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
cam.data.ortho_scale = 576 / (2 * scale)
FLIGHT = [('sa', 0.), ('wa', .125), ('wb', .25), ('wc', .4375), ('wd', .625), ('we', .75), ('wf', .875)]
SHOTS = {'Standing': [(f, t * 22 / .9375) for f, t in FLIGHT], 'Walking': [(f, t * 22 / .9375) for f, t in FLIGHT],
         'Fidget': [(f, t * 22 / .9375) for f, t in FLIGHT],
         'Attack': [(f, t * 24) for f, t in [('sa', 0.), ('aa', .125), ('ab', .25), ('ac', .375), ('ad', .5), ('ae', .625), ('af', .75)]],
         'Hit': [(f, t * 24) for f, t in [('sa', 0.), ('na', .125), ('nb', .25), ('nc', .375), ('nd', .5), ('ne', .625), ('nf', .75)]],
         'Death': [(f, t * 24) for f, t in [('sa', 0.), ('na', .125), ('nb', .25), ('nc', .375), ('da', .5), ('db', .625), ('dc', .8125), ('xa', .9375), ('dd', 1.125)]]}
FRONT_ONLY = {'da', 'db', 'dc', 'xa', 'dd'}
index = []
for clip, shots in SHOTS.items():
    rig.animation_data.action = bpy.data.actions[clip]
    for frame, fr in shots:
        sc.frame_set(int(fr), subframe=fr % 1)
        dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); me = ev.to_mesh()
        pts = [body.matrix_world @ v.co for v in me.vertices]; ev.to_mesh_clear()
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        target = (lo + hi) / 2
        for view in ([0] if (clip == 'Death' and frame in FRONT_ONLY) else range(5)):
            th = math.radians(45 * view); d = Vector((-math.sin(th) * math.cos(elev), -math.cos(th) * math.cos(elev), math.sin(elev)))
            cam.location = target + d * 4; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
            for mode in ('sil', 'tex'):
                sc.display.shading.color_type = 'TEXTURE' if mode == 'tex' else 'SINGLE'
                sc.render.filepath = str(out / f'{clip}_{frame}{view}_{mode}.png'); bpy.ops.render.render(write_still=True)
            index.append({'clip': clip, 'frame': frame, 'view': view, 'clip_frame': fr})
(out / 'index.json').write_text(json.dumps(index, indent=1) + '\n'); print('MOTION_RENDER', len(index))
