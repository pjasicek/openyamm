"""Portable native-inspired disintegration and ash, using standard mesh morph/TRS animation."""
import bpy
import json
import math
import numpy as np
from pathlib import Path
from mathutils import Matrix

STAGE = Path(__file__).resolve().parent
NATIVE = STAGE.parent.parent / 'mm6_dmn/native'
PIXELS = np.load(STAGE / 'native_effect_pixels.npz')
CLIPS = {'Attack': 36, 'Walking': 50, 'Running': 32, 'Standing': 6, 'Walk_Native': 54,
         'Hit': 36, 'Fidget': 30, 'Death': 60, 'Ash_Remains': 6}


def material(name, rgb, emission=False):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*[v**2.2 for v in rgb], 1)
    mat.use_nodes = True
    node = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    node.inputs['Base Color'].default_value = mat.diffuse_color
    node.inputs['Roughness'].default_value = .95
    if emission:
        node.inputs['Emission Color'].default_value = mat.diffuse_color
        node.inputs['Emission Strength'].default_value = .45
    return mat


def scale_tracks(obj, mode):
    for clip, end in CLIPS.items():
        action = bpy.data.actions.new(obj.name + '_' + clip)
        slot = action.slots.new(id_type='OBJECT', name=obj.name)
        bag = action.layers.new('Presentation only').strips.new(type='KEYFRAME').channelbag(slot, ensure=True)
        for component in range(3):
            curve = bag.fcurves.new('scale', index=component)
            if mode == 'body':
                keys = [(0, 0), (end, 0)] if clip == 'Ash_Remains' else (
                    [(0, 1), (18, 0), (end, 0)] if clip == 'Death' else [(0, 1), (end, 1)])
            else:
                value = 1 if clip == 'Ash_Remains' else 0
                keys = [(0, value), (end, value)]
            for frame, value in keys:
                curve.keyframe_points.insert(frame, value).interpolation = 'CONSTANT'
        action.use_fake_user = True
        if obj.animation_data is None:
            obj.animation_data_create()
        track = obj.animation_data.nla_tracks.new()
        track.name = clip
        strip = track.strips.new(clip, 0, action)
        strip.action_slot = slot
        track.mute = True


def build():
    scene = bpy.data.scenes['MM6_Demon_Native_Animations']
    bpy.context.window.scene = scene
    rig = scene.objects['Demon_Native_Rig']
    mesh = scene.objects['Demon_Native_Mesh']
    assert 'Demon_Death_Plume' not in scene.objects, 'Effects already exist; inspect before replacing'
    body = bpy.data.objects.new('Demon_Body_Visibility', None)
    scene.collection.objects.link(body)
    rig.parent = body
    rig.matrix_parent_inverse = Matrix.Identity(4)
    scale_tracks(body, 'body')
    body['purpose'] = 'STEP visibility only; all bones retain unit scale. Body disappears inside plume at 375 ms.'
    body_mat = material('Demon_Untextured_Clay', (.62, .66, .70))
    mesh.data.materials.clear()
    mesh.data.materials.append(body_mat)

    rng = np.random.default_rng(61005)
    warm_count, dark_count = 450, 180
    count = warm_count + dark_count
    # Independent tetrahedral fragments; base is subpixel and hidden inside ash/background.
    tetra = np.array([[0, 0, 1], [-.7, -.5, -.5], [.7, -.5, -.5], [0, .8, -.5]])
    directions = rng.uniform(-math.pi, math.pi, count)
    sizes = rng.uniform(.025, .050, count)
    vertices = np.tile(tetra * .000001, (count, 1))
    faces = [[4*i+a, 4*i+b, 4*i+c] for i in range(count) for a, b, c in
             [(0, 1, 2), (0, 2, 3), (0, 3, 1), (1, 3, 2)]]
    data = bpy.data.meshes.new('Native_Plume_Fragment_Geometry')
    data.from_pydata(vertices, [], faces)
    data.update()
    fx = bpy.data.objects.new('Demon_Death_Plume', data)
    scene.collection.objects.link(fx)
    palettes = [(.88, .56, .55), (.76, .40, .40), (.93, .65, .62), (.68, .32, .32), (.97, .72, .67)]
    for i, rgb in enumerate(palettes):
        data.materials.append(material('Native_Warm_Fragment_' + str(i), rgb, True))
    data.materials.append(material('Native_Dark_Fragment', (.11, .075, .065)))
    for face in data.polygons:
        particle = face.index // 4
        face.material_index = particle % 5 if particle < warm_count else 5
    fx.shape_key_add(name='Basis')
    references = []
    depths = rng.uniform(-.62, .36, count)
    for index, letter in enumerate('abcdefghi'):
        rgba = PIXELS[f'dmndth{letter}0'].astype(np.int16)
        warm = ((rgba[:, :, 0] > rgba[:, :, 1] + 25) & (rgba[:, :, 0] > rgba[:, :, 2] + 15)
                & (rgba[:, :, 0] > 120) & (rgba[:, :, 3] > 0))
        if index < 3:
            warm[:100] = False
        if index == 2:
            warm[90:130, 150:205] = False
        yy, xx = np.where(warm)
        # Sorting by source height keeps the same fragments moving through the rising/falling envelope.
        order = np.lexsort((xx, yy))
        select = np.linspace(0, len(order)-1, warm_count).astype(int)
        warm_points = np.column_stack((xx[order[select]], yy[order[select]]))
        dark = (rgba[:, :, :3].max(2) < 100) & (rgba[:, :, 3] > 0)
        if index < 2:
            dark[:] = False
        elif index == 2:
            dark[:200] = False
        dy, dx = np.where(dark)
        if len(dx):
            order = np.lexsort((dx, dy))
            select = np.linspace(0, len(order)-1, dark_count).astype(int)
            dark_points = np.column_stack((dx[order[select]], dy[order[select]]))
        else:
            dark_points = np.tile([177, 330], (dark_count, 1))
        points = np.vstack([warm_points, dark_points])
        centres = np.column_stack(((points[:, 0]-177)*.0065, depths,
                                   (330-points[:, 1])*.0065))
        # Emission remains near the body initially; later particles have a genuine 3D distribution.
        centres[:, 1] *= .55 if index < 2 else 1
        coords = []
        for i in range(count):
            angle = directions[i] + index*.4
            rotation = np.array([[math.cos(angle), -math.sin(angle), 0],
                                 [math.sin(angle), math.cos(angle), 0], [0, 0, 1]])
            size = sizes[i]
            if i >= warm_count and index < 2:
                size = .000001
            v = (tetra * size) @ rotation.T + centres[i]
            v[:, 2] = np.maximum(v[:, 2], .002)
            coords.extend(v)
        key = fx.shape_key_add(name='Native_Death_' + letter.upper())
        key.data.foreach_set('co', np.array(coords, dtype=np.float32).ravel())
        references.append(dict(source=f'dmndth{letter}0', warm_pixels=int(warm.sum()),
                               dark_pixels=int(dark.sum()), source_envelope=[int(xx.min()), int(yy.min()),
                                                                         int(xx.max()+1), int(yy.max()+1)]))
    keys = data.shape_keys
    for clip, end in CLIPS.items():
        action = bpy.data.actions.new('Demon_Plume_' + clip)
        slot = action.slots.new(id_type='KEY', name=keys.name)
        bag = action.layers.new('Portable morph envelope').strips.new(type='KEYFRAME').channelbag(slot, ensure=True)
        times = [0, 6, 12, 18, 24, 30, 36, 42, 51]
        for i, key in enumerate(list(keys.key_blocks)[1:]):
            curve = bag.fcurves.new('key_blocks[' + json.dumps(key.name) + '].value')
            for frame in range(end+1):
                value = 0
                if clip == 'Death':
                    segment = max(j for j, t in enumerate(times) if t <= frame)
                    following = min(segment+1, 8)
                    length = (times[following]-times[segment]) if following != segment else 9
                    u = min(1, (frame-times[segment])/length)
                    u = u*u*(3-2*u)
                    if i == segment:
                        value += 1-u
                    if i == following:
                        value += u
                point = curve.keyframe_points.insert(frame, value)
                point.interpolation = 'LINEAR'
        action.use_fake_user = True
        keys.animation_data_create()
        track = keys.animation_data.nla_tracks.new()
        track.name = clip
        strip = track.strips.new(clip, 0, action)
        strip.action_slot = slot
        track.mute = True
    # Separate low irregular ash mound. Scale derives from its native 1.75/.699997 ratio.
    bbox = PIXELS['ash_bbox']
    width = (bbox[2]-bbox[0])*.0065*1.75/.699997
    rings, segments = 7, 48
    ash_vertices, ash_faces = [(0, 0, .18)], []
    for ring in range(1, rings+1):
        radius = ring/rings
        for j in range(segments):
            angle = 2*math.pi*j/segments
            irregular = 1+rng.uniform(-.08, .08)
            ash_vertices.append((math.cos(angle)*width*.5*radius*irregular,
                                 math.sin(angle)*width*.22*radius*irregular,
                                 max(.003, .18*(1-radius**1.4)+rng.uniform(-.015, .015))))
    for j in range(segments):
        ash_faces.append((0, 1+j, 1+(j+1)%segments))
    for ring in range(rings-1):
        for j in range(segments):
            a, b = 1+ring*segments+j, 1+ring*segments+(j+1)%segments
            c, d = a+segments, b+segments
            ash_faces.extend([(a, c, b), (b, c, d)])
    ash_data = bpy.data.meshes.new('Native_Ash_Mound')
    ash_data.from_pydata(ash_vertices, [], ash_faces)
    ash_data.update()
    ash = bpy.data.objects.new('Demon_Ash_Remains', ash_data)
    scene.collection.objects.link(ash)
    for i in range(5):
        ash_data.materials.append(material('Native_Ash_' + str(i), (.035+i*.012, .027+i*.010, .020+i*.008)))
    for polygon in ash_data.polygons:
        polygon.material_index = int(rng.integers(0, 5))
    scale_tracks(ash, 'ash')
    ash.scale = (0, 0, 0)
    scene.display.shading.color_type = 'MATERIAL'
    fx['source'] = 'Native death warm/dark pixel envelopes; 3D depth and fragment shape are authored interpretations'
    ash['source'] = 'm498x / m496xa; separate held remains with native scale ratio'
    (STAGE / 'effects_manifest.json').write_text(json.dumps(dict(
        representation='glTF 2.0 standard mesh morph weights and STEP presentation-node scale',
        fragments=count, warm_fragments=warm_count, dark_fragments=dark_count, morph_targets=9,
        body_disappearance_frame=18, body_bone_scales='All unit; presentation parent controls binary visibility only',
        ash_width=width, native_body_scale=.699997, native_ash_scale=1.75,
        source_references=references, limitations='Native-inspired faceted 3D effect, not an exact recovered flame simulation'),
        indent=2)+'\n')
    print('Built portable plume morphs, binary body presentation and separate ash mound.', flush=True)
