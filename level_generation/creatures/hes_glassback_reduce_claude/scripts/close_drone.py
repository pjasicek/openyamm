"""Close-ups straight from GLBs (each file's own normals): textured (Eevee), clay and clay + wireframe (workbench),
same cameras for every label. Spots: lens front, casing three-quarter, top ribs (side), right flank overgrowth,
tail, belly vents, left flank; ortho, Standing frame 0.
Usage: blender -b -P close_drone.py -- <label=glb,...>  -> review/close/<label>_<spot>_<mode>.png (env SPOTS, MODES)"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'close'); os.makedirs(out, exist_ok=True)
# spot: (centre offset from the bounds centre in m, view direction, ortho size)
SPOTS = {'lens': ((0, -0.3, 0), (0.15, -1, 0.1), 0.36), 'q34': ((0, 0, 0), (0.8, -0.8, 0.4), 0.9),
         'ribs': ((0, 0.05, 0.12), (1, 0, 0.15), 0.62), 'flank_r': ((-0.05, 0.12, 0.05), (-1, 0.3, 0.35), 0.55),
         'tail': ((0, 0.3, -0.02), (0.4, 1, 0.25), 0.42), 'belly': ((0, 0.05, -0.15), (0.2, -0.3, -1), 0.6),
         'flank_l': ((0.05, 0, 0), (1, -0.25, 0.1), 0.7)}
if os.environ.get('SPOTS'):
    SPOTS = {k: SPOTS[k] for k in os.environ['SPOTS'].split(',')}
MODES = os.environ.get('MODES', 'tex,clay,wire').split(',')
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.fps = 24
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    act = next((a for a in bpy.data.actions if a.name.startswith('Standing')), None)
    if act:
        rig.animation_data.action = act
        if act.slots:
            rig.animation_data.action_slot = act.slots[0]
    sc.frame_set(0)
    body = next(o for o in meshes if o.name == 'HDR')
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    pts = [body.matrix_world @ v.co for v in m.vertices]; ev.to_mesh_clear()
    lo = Vector([min(p[k] for p in pts) for k in range(3)]); hi = Vector([max(p[k] for p in pts) for k in range(3)])
    ctr = (lo + hi) / 2
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; sc.render.resolution_x = sc.render.resolution_y = 480
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'
    wires = []
    for o in meshes:
        wo = o.copy(); wo.data = o.data; sc.collection.objects.link(wo)
        mod = wo.modifiers.new('Wire', 'WIREFRAME'); mod.thickness = 0.0007; mod.use_replace = True
        mat = bpy.data.materials.new('WireBlack'); mat.diffuse_color = (0.02, 0.02, 0.02, 1)
        wo.data = o.data.copy(); wo.data.materials.clear(); wo.data.materials.append(mat)
        wo.hide_render = True; wires.append(wo)
    for spot, (off, d, size) in SPOTS.items():
        c = ctr + Vector(off)
        cam.location = c + Vector(d).normalized() * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size
        for mode in MODES:
            for wo in wires:
                wo.hide_render = mode != 'wire'
            if mode == 'tex':
                sc.render.engine = 'BLENDER_EEVEE'
            else:
                sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
                sc.display.shading.color_type = 'MATERIAL' if mode == 'wire' else 'SINGLE'
                sc.display.shading.single_color = (.8, .78, .74)
                for o in meshes:
                    pass
            if mode == 'wire':   # clay body, black wire
                sc.display.shading.color_type = 'OBJECT'
                for o in meshes:
                    o.color = (.8, .78, .74, 1)
                for wo in wires:
                    wo.color = (0.03, 0.03, 0.03, 1)
            sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('CLOSE done')
