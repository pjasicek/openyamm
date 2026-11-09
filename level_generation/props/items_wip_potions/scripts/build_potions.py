"""Owned potion vessels: reusable Blender profiles, separate fittings and padded painted UV tiles.
Run with Blender --background --python this.py -- [--render] [icon ...].
"""
import argparse
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parents[1]
OWNERSHIP = json.loads((PROJECT / 'ownership.json').read_text())
DESIGNS = json.loads((PROJECT / 'designs.json').read_text())
TAU = math.tau
SEGMENTS = 24


def uv(tile, u, v):
    return ((tile % 8 + 0.025 + 0.95 * u) / 8, 1 - (tile // 8 + 0.025 + 0.95 * (1 - v)) / 4)


def material(name, glass=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    if glass:
        empty = name.endswith('_empty')
        jar = name.endswith('_jar')
        bsdf.inputs['Base Color'].default_value = (0.25, 0.40, 0.45, 1) if empty or jar else (0.08, 0.10, 0.10, 1)
        bsdf.inputs['Roughness'].default_value = 0.13
        bsdf.inputs['Alpha'].default_value = 0.45 if empty else 0.30 if jar else 0.12
        mat.surface_render_method = 'DITHERED'
        return mat
    images = {}
    for suffix in ('basecolor', 'orm', 'normal'):
        node = nodes.new('ShaderNodeTexImage')
        node.image = bpy.data.images.load(str(PROJECT / f'textures/potions_{suffix}.png'), check_existing=True)
        if suffix != 'basecolor':
            node.image.colorspace_settings.name = 'Non-Color'
        images[suffix] = node
    links.new(images['basecolor'].outputs['Color'], bsdf.inputs['Base Color'])
    separate = nodes.new('ShaderNodeSeparateColor')
    links.new(images['orm'].outputs['Color'], separate.inputs['Color'])
    links.new(separate.outputs['Green'], bsdf.inputs['Roughness'])
    links.new(separate.outputs['Blue'], bsdf.inputs['Metallic'])
    normal = nodes.new('ShaderNodeNormalMap')
    links.new(images['normal'].outputs['Color'], normal.inputs['Color'])
    links.new(normal.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


def mesh(name, vertices, faces, face_uvs, tile, glass=False, smooth=True):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    name = ('potions_glass_' + glass if isinstance(glass, str)
            else 'potions_glass' if glass else 'potions_painted')
    data.materials.append(bpy.data.materials[name])
    layer = data.uv_layers.new(name='UVMap')
    for face, coords in zip(data.polygons, face_uvs):
        face.use_smooth = smooth
        for index, coord in zip(face.loop_indices, coords):
            layer.data[index].uv = uv(tile, *coord)
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.0000001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='SHORT_EDGE', ngon_method='BEAUTY')
    bm.to_mesh(data)
    bm.free()
    return obj


def cap(ring):
    # Alternating ears close the disc without a high-valence centre pole.
    ring = list(ring)
    result = []
    while len(ring) > 2:
        result.append((ring[-1], ring[0], ring[1]))
        ring.pop(0)
        if len(ring) > 2:
            result.append((ring[0], ring[-2], ring[-1]))
            ring.pop()
    return result


def lathe(name, profile, tile, glass=False, segments=SEGMENTS, origin=(0, 0, 0), flatten=1,
          closed_profile=False):
    if closed_profile:
        profile = profile + [profile[0]]
    vertices = [(origin[0] + radius * math.cos(TAU * k / segments),
                 origin[1] + radius * math.sin(TAU * k / segments) * flatten, origin[2] + z)
                for z, radius in profile for k in range(segments)]
    lengths = [0.0]
    for (z0, r0), (z1, r1) in zip(profile, profile[1:]):
        lengths.append(lengths[-1] + math.hypot(z1 - z0, r1 - r0))
    circumference = TAU * max(radius for z, radius in profile)
    uv_extent = max(circumference, lengths[-1])
    faces, coords = [], []
    for row in range(len(profile) - 1):
        for k in range(segments):
            a, b = row * segments + k, row * segments + (k + 1) % segments
            faces.append((a, b, b + segments, a + segments))
            coords.append([(k / segments * circumference / uv_extent, lengths[row] / uv_extent),
                           ((k + 1) / segments * circumference / uv_extent, lengths[row] / uv_extent),
                           ((k + 1) / segments * circumference / uv_extent, lengths[row + 1] / uv_extent),
                           (k / segments * circumference / uv_extent, lengths[row + 1] / uv_extent)])
    for row in (() if closed_profile else (0, len(profile) - 1)):
        for triangle in cap(range(row * segments, (row + 1) * segments)):
            faces.append(triangle)
            coords.append([(0.5 + profile[row][1] / uv_extent * math.cos(TAU * (i % segments) / segments),
                            0.5 + profile[row][1] / uv_extent * math.sin(TAU * (i % segments) / segments))
                           for i in triangle])
    return mesh(name, vertices, faces, coords, tile, glass)


def band(name, z, radius, height, tile=0, width=0.025):
    return lathe(name, [(z, radius - width), (z, radius), (z + height, radius),
                        (z + height, radius - width)], tile, closed_profile=True)


def tube(name, points, radius, tile, sides=6, closed=False):
    points = [Vector(p) for p in points]
    lengths = [0.0]
    for a, b in zip(points, points[1:]):
        lengths.append(lengths[-1] + (b - a).length)
    total = lengths[-1] + ((points[0] - points[-1]).length if closed else 0)
    uv_extent = max(TAU * radius, total)
    vertices = []
    for i, point in enumerate(points):
        tangent = points[(i + 1) % len(points)] - points[i - 1]
        if not closed and i in (0, len(points) - 1):
            tangent = points[1] - points[0] if i == 0 else points[-1] - points[-2]
        tangent.normalize()
        axis = tangent.cross(Vector((0, 1, 0)))
        if axis.length < 0.1:
            axis = tangent.cross(Vector((1, 0, 0)))
        axis.normalize()
        other = tangent.cross(axis).normalized()
        vertices.extend(point + radius * (axis * math.cos(TAU * k / sides)
                                          + other * math.sin(TAU * k / sides)) for k in range(sides))
    faces, coords = [], []
    for i in range(len(points) if closed else len(points) - 1):
        n = (i + 1) % len(points)
        for k in range(sides):
            faces.append((i * sides + k, i * sides + (k + 1) % sides,
                          n * sides + (k + 1) % sides, n * sides + k))
            a, b = lengths[i] / uv_extent, (lengths[n] if n else total) / uv_extent
            u0, u1 = k / sides * TAU * radius / uv_extent, (k + 1) / sides * TAU * radius / uv_extent
            coords.append([(u0, a), (u1, a), (u1, b), (u0, b)])
    if not closed:
        for row in (0, len(points) - 1):
            for face in cap(range(row * sides, (row + 1) * sides)):
                faces.append(face)
                coords.append([(0.5 + 0.45 * math.cos(TAU * (k % sides) / sides),
                                0.5 + 0.45 * math.sin(TAU * (k % sides) / sides)) for k in face])
    return mesh(name, vertices, faces, coords, tile)


def hoop(name, centre, radius, thickness, tile, plane='XY', segments=16):
    x, y, z = centre
    points = []
    for k in range(segments):
        a, b = radius * math.cos(TAU * k / segments), radius * math.sin(TAU * k / segments)
        points.append((x + a, y + b, z) if plane == 'XY' else (x + a, y, z + b))
    return tube(name, points, thickness, tile, closed=True)


def solid_contents(profile, fill, tile, name='liquid', flatten=1):
    selected = [(z + 0.015, r * 0.935) for z, r in profile if z < fill]
    for (z0, r0), (z1, r1) in zip(profile, profile[1:]):
        if z0 < fill <= z1:
            selected.append((fill, (r0 + (r1 - r0) * (fill - z0) / (z1 - z0)) * 0.935))
            break
    return lathe(name, selected, tile, flatten=flatten)


def mm6(icon):
    colors = [10, 5, 6, 7, 4, 9, 24, 8, None]
    tile = colors[int(icon[6:]) - 22]
    profile = [(0.055, 0.27), (0.10, 0.31), (0.29, 0.40), (0.60, 0.43),
               (0.86, 0.35), (1.10, 0.22), (1.41, 0.10), (1.57, 0.075), (1.64, 0.08)]
    if tile is None:
        lathe('glass_vessel', profile, 2, glass='empty')
    else:
        lathe('glass_vessel', profile[:6], 2, glass=True)
        lathe('smoked_glass_neck', profile[5:], 10)
    if tile is not None:
        solid_contents(profile, 0.98, tile)
    lathe('pewter_base', [(0, .30), (.025, .46), (.065, .46), (.085, .34)], 2)
    for k in range(4):
        angle = TAU * (k + 0.5) / 4
        tube('cradle_prong', [(r * math.cos(angle), r * math.sin(angle), z)
                             for z, r in [(0.035, .31), (.18, .37), (.56, .44), (.93, .48)]], .040, 2)
    band('neck_collar', 1.57, .115, .055, 2)
    lathe('stopper', [(1.62, .075), (1.72, .075), (1.73, .14), (1.78, .12), (1.80, .055)], 2)
    return 'potions_mm6_cradle'


def mm78(icon, tile=None, short=False):
    index = int(icon[4:])
    palette = [5, 4, 24, 9, 25, 10, 8, 6, 7, 4, 8, 6, 5, 8, 6, 7, 8, 6, 8, 6, 6, None]
    if tile is None:
        tile = palette[index - 177] if 177 <= index <= 198 else 4
    profile = [(0.04, .23), (.08, .35), (.22, .45), (.43, .49), (.66, .45), (.83, .32),
               (.95, .17), (1.10, .09), (1.29, .085), (1.35, .10)]
    if short:
        profile = [(z * .83, r) for z, r in profile]
    if tile is None:
        lathe('glass_vessel', profile, 2, glass='empty')
    else:
        lathe('glass_vessel', profile[:7], 2, glass=True)
        lathe('smoked_glass_neck', profile[6:], 10)
    ornate = 186 <= index <= 197
    if tile is not None:
        decorated = {187: 16, 188: 27, 191: 31, 193: 28, 195: 16, 196: 30}
        solid_contents(profile, .79 * (.83 if short else 1),
                       decorated.get(index, 16 + tile - 4 if ornate else tile))
    band('foot', 0.015, .27, .07, 0)
    band('equator_brass_band', .34 * (.83 if short else 1), .50, .14, 0)
    for k in range(4):
        a = TAU * (k + .5) / 4
        tube('lower_support', [(r * math.cos(a), r * math.sin(a), z * (.83 if short else 1))
                               for z, r in [(.08, .30), (.19, .43), (.36, .49)]], .021, 0)
    scale = .83 if short else 1
    lathe('shoulder_cap', [(z * scale, r) for z, r in [(.86, .29), (.89, .28), (.94, .19),
                                                                     (.99, .13), (1.02, .12)]], 0)
    band('neck_band', 1.13 * scale, .105, .055 * scale, tile if tile is not None else 0)
    lathe('stopper', [(z * scale, r) for z, r in [(1.28, .10), (1.32, .14), (1.43, .14),
                                                               (1.47, .10), (1.49, .10)]], 0)
    hoop('stopper_loop', (0, 0, 1.57 * scale), .072 * scale, .012, 0, 'XZ', 12)
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            for vertex in obj.data.vertices:
                vertex.co.z *= 1.20
    return 'potions_mm78_banded'


def quest(icon):
    if icon == 'item162':
        mm78(icon, 4, True)
        return 'potions_gog_short'
    if icon == '7item145':
        p = [(.045,.20),(.09,.29),(.18,.38),(.30,.43),(.43,.35),(.56,.20),(.65,.10),(1.79,.10)]
        lathe('long_glass_phial',p,2,True)
        solid_contents(p,1.72,4)
        lathe('gold_foot',[(0,.22),(.03,.28),(.065,.27),(.085,.20)],1)
        for z in (1.67,1.74,1.83):
            band('gold_neck_rings',z,.15,.035,1)
        lathe('stopper',[(1.83,.11),(1.91,.13),(1.94,.17),(1.97,.17)],1)
        return 'potions_troll_long_phial'
    if icon == '7item155':
        p=[(0,.25),(.06,.36),(.22,.44),(.48,.47),(.65,.37),(.77,.36),(.96,.40),
           (1.15,.35),(1.26,.20),(1.49,.13)]
        lathe('double_bulb_pewter',p,0)
        for z,r in [(.03,.36),(.73,.37),(1.29,.20),(1.46,.18)]:
            band('gold_collar',z,r,.05,1)
        for k in range(4):
            a=TAU*(k+.5)/4
            tube('pewter_rib',[(r*math.cos(a),r*math.sin(a),z) for z,r in
                              [(.10,.37),(.36,.48),(.68,.38),(.84,.40),(1.09,.36),(1.25,.21)]],.025,2)
        lathe('cork',[(1.46,.12),(1.61,.14),(1.64,.19),(1.68,.19)],3)
        return 'potions_devil_double_bulb'
    if icon == '7item157':
        p=[(0,.23),(.05,.34),(.20,.42),(.45,.46),(.67,.42),(.82,.28),(.94,.14),
           (1.13,.12),(1.20,.11),(1.28,.07),(1.60,.07)]
        lathe('pewter_vial',p,2)
        for z,r in [(.04,.34),(.96,.15),(1.18,.14),(1.57,.10)]:
            band('rim',z,r,.04,2)
        for flip in (-1,1):
            points=[]
            for k in range(25):
                a=TAU*k/24
                points.append((.455*math.cos(a),.455*math.sin(a),.46+flip*.25*math.cos(a)))
            tube('diagonal_brace',points,.034,14,closed=True)
        return 'potions_ooze_metal_vial'
    if icon in ('7item259','7item294'):
        p=[(.02,.33),(.07,.43),(.17,.48),(1.11,.48),(1.23,.43),(1.31,.32),(1.40,.32)]
        lathe('clear_jar',p,2,'empty' if icon=='7item294' else 'jar',flatten=.78)
        if icon=='7item259':
            band('thick_glass_base',.035,.40,.035,25)
            band('thick_glass_lip',1.27,.34,.035,25)
        lathe('wooden_lid',[(1.33,.31),(1.40,.36),(1.46,.36),(1.48,.32)],29,flatten=.78)
        if icon=='7item259':
            for n,(x,y,z,sx,sy,sz) in enumerate([(-.12,0,.86,.23,.21,.28),(.11,0,.86,.22,.22,.24),
                                               (0,0,.53,.28,.22,.19),(0,0,.30,.23,.18,.15)]):
                profile=[(sz*math.sin(-math.pi/2+math.pi*k/8)+z,
                          max(.008,sx*math.cos(-math.pi/2+math.pi*k/8))) for k in range(9)]
                lathe('preserved_tissue',profile,26,origin=(x,y,0),flatten=sy/sx,segments=16)
            points=[(.24*math.sin(TAU*k/12),-.18,.25+.49*k/36) for k in range(37)]
            tube('preserved_coils',points,.038,26,sides=6)
        return 'potions_lich_preserved_jar' if icon=='7item259' else 'potions_lich_empty_jar'
    if icon=='7item273':
        p=[(0,.14),(.10,.27),(.31,.37),(.66,.40),(.97,.32),(1.17,.20),(1.28,.09),(1.51,.07)]
        lathe('peacock_elixir',p,13,flatten=.64)
        for k in range(6):
            a=TAU*k/6
            tube('silver_cage',[(r*math.cos(a),r*.64*math.sin(a),z) for z,r in
                               [(.05,.20),(.28,.36),(.66,.405),(.96,.33),(1.20,.17),(1.28,.10)]],.017,2)
        for z,r in [(0,.18),(1.30,.11),(1.46,.11)]:
            band('silver_collar',z,r,.04,2)
        lathe('crystal_stopper',[(1.48,.06),(1.55,.13),(1.65,.14),(1.73,.09),(1.76,.02)],2,segments=12)
        return 'potions_peacock_elixir'
    if icon in ('item278','item280'):
        p=[(.02,.21),(.07,.33),(.20,.46),(.40,.50),(.57,.43),(.76,.26),(.96,.15),
           (1.19,.10),(1.52,.09)]
        lathe('glass_flask',p[:7],2,True)
        lathe('smoked_glass_neck',p[6:],10)
        solid_contents(p,.38 if icon=='item278' else .72,15 if icon=='item278' else 13,
                       name='grave_earth' if icon=='item278' else 'herbal_liquid')
        for z,r in [(.02,.25),(1.47,.13)]:
            band('foot_and_neck',z,r,.04,2 if icon=='item278' else 1)
        lathe('cork',[(1.49,.085),(1.68,.115),(1.71,.13),(1.74,.13)],3)
        if icon=='item280':
            band('gold_shoulder_band',.71,.29,.045,1)
        return 'potions_grave_earth' if icon=='item278' else 'potions_anointed_herb'
    if icon=='item294':
        p=[(0,.24),(.06,.37),(.16,.34),(.30,.28),(.45,.39),(.69,.44),(.93,.38),
           (1.15,.27),(1.37,.24),(1.56,.29),(1.69,.38)]
        # Open mouth and a real inner wall, rather than a painted black disc.
        p += [(1.69,.34),(1.55,.25),(1.36,.20),(1.16,.23),(.94,.34),(.70,.40),(.47,.35),(.36,.25)]
        urn = lathe('bronze_urn',p,14)
        for face in urn.data.polygons:
            centre = face.center
            if face.normal.x * centre.x + face.normal.y * centre.y < -0.03:
                for loop in face.loop_indices:
                    coord = urn.data.uv_layers.active.data[loop].uv
                    coord.x -= 4 / 8
        for z,r in [(0,.35),(.38,.35),(1.67,.39)]:
            band('urn_rim',z,r,.045,1)
        for sign in (-1,1):
            points=[(sign*x,0,z) for x,z in [(.33,.40),(.55,.42),(.73,.57),(.80,.80),
                                            (.76,1.01),(.66,1.20),(.55,1.32),(.48,1.16),(.35,1.08)]]
            tube('swept_handle',points,.043,1,sides=8)
        return 'potions_bronze_handled_urn'
    raise ValueError(icon)


def finish(icon):
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    # One opaque draw and a separate glass mesh; no transmission extension or refraction assumption.
    for transparent in (False,True):
        group=[o for o in bpy.context.scene.objects if o.type=='MESH'
               and o.data.materials[0].name.startswith('potions_glass')==transparent]
        if group:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in group:
                obj.select_set(True)
            bpy.context.view_layer.objects.active=group[0]
            bpy.ops.object.join()
            group[0].name=icon+('_glass' if transparent else '_solid')
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    points=[o.matrix_world@v.co for o in objects for v in o.data.vertices]
    minimum=Vector(tuple(min(p[i] for p in points) for i in range(3)))
    maximum=Vector(tuple(max(p[i] for p in points) for i in range(3)))
    centre=Vector(((minimum.x+maximum.x)/2,(minimum.y+maximum.y)/2,minimum.z))
    scale=max(maximum.x-minimum.x,maximum.y-minimum.y)
    rotate = maximum.x - minimum.x > maximum.y - minimum.y + 0.001
    for obj in objects:
        for vertex in obj.data.vertices:
            vertex.co=(vertex.co-centre)/scale
            if rotate:
                vertex.co.x, vertex.co.y = -vertex.co.y, vertex.co.x
    for obj in objects:
        obj.data.calc_loop_triangles()
        assert all(len(face.vertices)==3 for face in obj.data.polygons)
        assert all(math.isfinite(c) for v in obj.data.vertices for c in v.co)
        assert all(-1e-5 <= c <= 1.00001 for t in obj.data.uv_layers.active.data for c in t.uv)
    triangles=sum(len(o.data.polygons) for o in objects)
    assert triangles<6000, (icon,triangles)
    out=PROJECT/'work/vessels'
    out.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/f'{icon}.blend'))
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(out/f'{icon}_export.glb'),export_format='GLB',
                             use_selection=True,export_extras=True,export_yup=True,
                             export_texcoords=True,export_normals=True,export_animations=False)
    return triangles


def render(icon, baseline=False):
    scene=bpy.context.scene
    objects=[o for o in scene.objects if o.type=='MESH']
    points=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box]
    lo=Vector(tuple(min(p[i] for p in points) for i in range(3)))
    hi=Vector(tuple(max(p[i] for p in points) for i in range(3)))
    centre=(lo+hi)/2
    extent=max(hi-lo)
    scene.render.engine='CYCLES'
    scene.cycles.samples=12
    scene.cycles.use_denoising=True
    scene.render.threads_mode='FIXED'
    scene.render.threads=8
    scene.render.resolution_x=scene.render.resolution_y=320
    scene.render.resolution_percentage=100
    scene.render.film_transparent=True
    scene.view_settings.view_transform='Standard'
    world=bpy.data.worlds.new('Review world')
    world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(.58,.62,.70,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
    scene.world=world
    lamp=bpy.data.objects.new('Softbox',bpy.data.lights.new('Softbox','AREA'))
    scene.collection.objects.link(lamp)
    lamp.location=centre+Vector((-2,-3,4))*extent
    lamp.data.energy=100*extent*extent
    lamp.data.shape='DISK'
    lamp.data.size=extent*4
    lamp.rotation_euler=(centre-lamp.location).to_track_quat('-Z','Y').to_euler()
    camera=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'))
    camera.data.type='ORTHO'
    camera.data.ortho_scale=extent*1.35
    scene.collection.objects.link(camera)
    scene.camera=camera
    folder=PROJECT/('review/baseline' if baseline else 'review/vessels')
    folder.mkdir(parents=True,exist_ok=True)
    for name,direction in [('above',(2.8,-1,2.8)),('low',(2.8,-1.2,1.1))]:
        camera.location=centre+Vector(direction).normalized()*extent*4
        camera.rotation_euler=(centre-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(folder/f'{icon}_{name}.png')
        bpy.ops.render.render(write_still=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--render',action='store_true')
    parser.add_argument('--baseline',action='store_true')
    parser.add_argument('--review-existing',action='store_true')
    parser.add_argument('icons',nargs='*')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    only=set(args.icons)
    reports={}
    designs={}
    for row in OWNERSHIP:
        icon=row['icon']
        if only and icon not in only:
            continue
        if icon=='7item182' and not args.baseline:
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        if args.baseline:
            bpy.ops.import_scene.gltf(filepath=str(PROJECT/f'references/baseline/item_{icon}.glb'))
            render(icon,True)
            continue
        if args.review_existing:
            bpy.ops.import_scene.gltf(filepath=str(PROJECT/f'work/vessels/{icon}_export.glb'))
            render(icon)
            continue
        material('potions_painted')
        material('potions_glass',True)
        material('potions_glass_empty',True)
        material('potions_glass_jar',True)
        if icon.startswith('bottle'):
            shape=mm6(icon)
        elif icon.startswith('item') and 177<=int(icon[4:])<=198:
            shape=mm78(icon)
        else:
            shape=quest(icon)
        triangles=finish(icon)
        length=DESIGNS.get('potions_'+icon,{}).get('length',row['length'])
        reports[icon]={'triangles':triangles,'shape':shape,'length':length}
        designs['potions_'+icon]={'title':row['names'][0],'icons':[icon],'master_icon':icon,
                                 'shape':shape,'route':'blender_uv_imagegen','tris':triangles,
                                 'length':length,'export':f'work/vessels/{icon}_export.glb'}
        if args.render:
            render(icon)
        print('POTION',icon,shape,triangles,flush=True)
    if not args.baseline and not args.review_existing:
        for path,updates in [(PROJECT/'work/build_report.json',reports),(PROJECT/'designs.json',designs)]:
            previous=json.loads(path.read_text()) if path.exists() else {}
            previous.update(updates)
            path.write_text(json.dumps(previous,indent=2)+'\n')


if __name__=='__main__':
    main()
