"""Import each Meshy return (meshy/<job>/model_urls_glb.glb) and print its triangle count, bounds, pieces; render a
contact sheet (front/side/top, workbench) per job into review/meshy_<job>.png tiles. Args: -- <job> [<job> ...]"""
import bpy, sys, os, math, json
from mathutils import Vector
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
jobs = sys.argv[sys.argv.index('--') + 1:]
tiles = []
for job in jobs:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(P, 'meshy', job, 'model_urls_glb.glb'))
    obs = [o for o in bpy.data.objects if o.type == 'MESH']
    co = [o.matrix_world @ v.co for o in obs for v in o.data.vertices]
    lo = Vector([min(c[i] for c in co) for i in range(3)]); hi = Vector([max(c[i] for c in co) for i in range(3)])
    tris = sum(len(p.vertices) - 2 for o in obs for p in o.data.polygons)
    print('MESHY', job, 'tris', tris, 'objects', len(obs), 'size', [round(x, 3) for x in hi - lo])
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.show_cavity = True
    sc.render.resolution_x = sc.render.resolution_y = 400
    cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = max(hi - lo) * 1.1; c = (lo + hi) / 2
    for k, d in enumerate([Vector((0, -1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1))]):
        cam.location = c + d * 5; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        f = os.path.join(P, 'review', f'meshy_{job}.{k}.png'); sc.render.filepath = f; bpy.ops.render.render(write_still=True)
        tiles.append(f)
json.dump(tiles, open(os.path.join(P, 'review', 'meshy_tiles.json'), 'w'))
sys.stdout.flush(); os._exit(0)
