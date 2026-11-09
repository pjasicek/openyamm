"""Worst sleeve-poke frames with the flagged vertices marked (review of sleeve_poke_gate.py flags, 2026-11-02): the GLB posed
at each flagged clip's worst time, red 5 mm spheres at the gate's posed vertex positions (glTF -> Blender: x, -z, y),
textured Workbench, orthographic close-ups round the hand joint from four sides. Spheres hidden by cloth = no visible
poke. Args: <glb> <sleeve_poke.json> <out png>"""
import bpy, sys, json, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, js, out = a
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
rig = next(o for o in sc.objects if o.type == 'ARMATURE')
for o in list(sc.objects):
    if o.type == 'MESH' and ('LOD1' in o.name or 'LOD2' in o.name or 'LOD3' in o.name or 'Shadow' in o.name):
        o.hide_render = True
d = json.load(open(js))
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'
sc.render.resolution_x = sc.render.resolution_y = 360
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.5, 0.5, 0.55)
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.3
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
red = bpy.data.materials.new('red'); red.diffuse_color = (1, 0, 0, 1)
tiles = []
fps = sc.render.fps / sc.render.fps_base
for clip, e in d['clips'].items():
    for s, v in e.items():
        if not v.get('worst_points'):
            continue
        act = bpy.data.actions.get(clip)
        rig.animation_data.action = act
        try:
            rig.animation_data.action_slot = act.slots[0]
        except Exception:
            pass
        f = v['time_s'] * fps
        sc.frame_set(int(f), subframe=f - int(f))
        marks = []
        for q in v['worst_points']:
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.005, location=(q[0], -q[2], q[1]))
            o = bpy.context.object; o.data.materials.append(red); marks.append(o)
        sh.color_type = 'MATERIAL'
        h = v['hand_joint']; c = Vector((h[0], -h[2], h[1]))
        for vn, dv in (('front', (0, -1, 0.2)), ('back', (0, 1, 0.2)), ('out', (1 if h[0] > 0 else -1, 0, 0.2)), ('below', (0, -0.3, -1))):
            dvv = Vector(dv).normalized()
            cam.location = c + dvv * 2
            cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
            p = f'/tmp/render_poke_{os.getpid()}_{len(tiles)}.png'
            sh.color_type = 'TEXTURE'
            for m in marks:
                m.color = (1, 0, 0, 1)
            sc.render.filepath = p; bpy.ops.render.render(write_still=True)
            tiles.append((f'{clip} {s} {v["worst_mm"]}mm', vn, p))
        for m in marks:
            bpy.data.objects.remove(m)
open(out + '.list', 'w').write('\n'.join('\t'.join(t) for t in tiles))
print('POKE_RENDERS', len(tiles))
