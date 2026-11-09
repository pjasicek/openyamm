"""Flat-textured (or lit) views of a runtime GLB's LOD0 at rest. Args: -- <glb> <out prefix> <cx,cy,cz> <ortho> <size> <views name=dx,dy,dz:...> [lit] [variant]"""
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
lit = 'lit' in a[6:]
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name): o.hide_render = True
pose = next((x[5:] for x in a[6:] if x.startswith('pose=')), None)
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        if pose:
            act = next(ac for ac in bpy.data.actions if ac.name.startswith(pose))
            o.animation_data_create(); o.animation_data.action = act
            if hasattr(o.animation_data, 'action_slot') and act.slots: o.animation_data.action_slot = act.slots[0]
            bpy.context.scene.frame_set(int(act.frame_range[0]))
        else:
            if o.animation_data: o.animation_data_clear()
            for b in o.pose.bones: b.matrix_basis.identity()
opts = set(a[6:])
for m in bpy.data.materials:
    if not m.use_nodes: continue
    nt = m.node_tree
    if 'nonormal' in opts:
        for n in nt.nodes:
            if n.type == 'NORMAL_MAP':
                for l in list(n.outputs[0].links): nt.links.remove(l)
    if 'clay' in opts:
        bs = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bs:
            for l in list(bs.inputs['Base Color'].links): nt.links.remove(l)
            bs.inputs['Base Color'].default_value = (0.6, 0.6, 0.6, 1)
if 'recalc' in opts:
    for o in bpy.data.objects:
        if o.type == 'MESH':
            bpy.context.view_layer.objects.active = o
            try: bpy.ops.mesh.customdata_custom_splitnormals_clear()
            except Exception as e: print('recalc fail', e)
if 'wire' in opts:
    wm = bpy.data.materials.new('wire'); wm.use_nodes = True; wm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.02, 0.02, 0.6, 1)
    for o in list(bpy.data.objects):
        if o.type == 'MESH' and not o.hide_render:
            d = o.copy(); d.data = o.data.copy(); bpy.context.scene.collection.objects.link(d)
            d.data.materials.clear(); d.data.materials.append(wm)
            md = d.modifiers.new('w', 'WIREFRAME'); md.thickness = 0.00012; md.use_replace = True
sc = bpy.context.scene
if lit:
    try: sc.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError: sc.render.engine = 'BLENDER_EEVEE'
    sc.world = bpy.data.worlds.new('W'); sc.world.use_nodes = True
    bg = next(n for n in sc.world.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs['Color'].default_value = (0.35, 0.37, 0.4, 1)
    for nm, rot, en in (('key', (60, 0, -25), 3.0), ('fill', (70, 0, 150), 1.0)):
        ld = bpy.data.lights.new(nm, 'SUN'); ld.energy = en; lo = bpy.data.objects.new(nm, ld); sc.collection.objects.link(lo)
        lo.rotation_euler = [math.radians(x) for x in rot]
else:
    sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'TEXTURE'
    sc.world = bpy.data.worlds.new('w'); sc.world.color = (0.4, 0.4, 0.4); sh.background_type = 'WORLD'
sc.render.resolution_x = sc.render.resolution_y = int(a[4])
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[3]); cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
dg = bpy.context.evaluated_depsgraph_get(); hb = None
for o in bpy.data.objects:
    if o.type == 'MESH' and not o.hide_render:
        e = o.evaluated_get(dg); me = e.to_mesh()
        for poly in me.polygons:
            if e.material_slots and 'Head' in e.material_slots[poly.material_index].name:
                for vi in poly.vertices:
                    w = e.matrix_world @ me.vertices[vi].co
                    hb = [w.copy(), w.copy()] if hb is None else [Vector(map(min, hb[0], w)), Vector(map(max, hb[1], w))]
print('HEAD BBOX', tuple(hb[0]), tuple(hb[1]))
# centre given relative to the head set's bbox: x from its middle, y from its front (min y), z from its top
off = Vector([float(x) for x in a[2].split(',')]); ce = Vector(((hb[0].x + hb[1].x) / 2 + off.x, hb[0].y + off.y, hb[1].z + off.z))
print('CENTRE', tuple(ce))
for v in a[5].split(':'):
    nm, d = v.split('='); d = Vector(tuple(float(x) for x in d.split(','))).normalized()
    cam.location = ce + d * 3; cam.rotation_euler = (ce - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{nm}.png'; bpy.ops.render.render(write_still=True)
