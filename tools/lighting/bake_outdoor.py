"""Bake native ODM diffuse lighting with Cycles. Run using Blender's background Python.

Profiles are JSON (a YAML subset). Geometry and base textures remain unchanged.
Output is version-4 OpenYAMM lighting plus a dependency/quality report.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import sys
import time

import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bake_geometry import face_basis, pack_lightmap_charts, rle_bgra
from bake_assets import bake_texture_paths

sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file


def fnv(data):
    h = 14695981039346656037
    for b in data:
        h = ((h ^ b) * 1099511628211) & 0xffffffffffffffff
    return h


def rgbm(pixels):
    rgb = np.maximum(pixels[:, :, :3], 0)
    if not np.isfinite(rgb).all() or float(rgb.max()) > 4:
        raise ValueError('Lighting exceeds RGBM4 range or contains nonfinite samples')
    m = np.maximum(np.ceil(rgb.max(axis=2) * 255 / 4), 1)
    rgba = np.empty(pixels.shape, dtype=np.uint8)
    rgba[:, :, :3] = np.rint(np.clip(rgb / (m[:, :, None] * 4 / 255), 0, 1) * 255)
    rgba[:, :, 3] = m.astype(np.uint8)
    # Blender bottom-up data is kept: runtime lighting UVs use the same coordinates.
    return rgba[:, :, [2, 1, 0, 3]].tobytes()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--azimuth', type=float)
    parser.add_argument('--samples', type=int)
    parser.add_argument('--decoration-shadows', action=argparse.BooleanOptionalAction, default=None,
                        help='Bake static decoration alpha silhouettes into the sun term only')
    parser.add_argument('--preview-only', action='store_true')
    migration = parser.add_mutually_exclusive_group()
    migration.add_argument('--model-probes-only', type=Path,
                        help='Extend an installed v3 bake with model lighting; retain every surface and sprite sample')
    migration.add_argument('--sun-direct-only', type=Path,
                           help='Extend an installed v4 bake with direct-only surface pages for moving mesh shadows')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    profile = json.loads(args.profile.read_text())
    retained = None
    retained_path = args.model_probes_only or args.sun_direct_only
    if retained_path:
        installed_recipe = json.loads(retained_path.with_suffix('.bake.json').read_text())
        if profile != installed_recipe['profile']:
            raise ValueError('Probe migration must use the exact installed bake profile')
        retained = retained_path.read_bytes()
        expected_version = 4 if args.sun_direct_only else 3
        if retained[:8] != b'OYMLIT1\0' or struct.unpack_from('<I', retained, 8)[0] != expected_version:
            raise ValueError(f'Lighting migration expects a version-{expected_version} bake')
        if any(value is not None for value in (args.azimuth, args.samples, args.decoration_shadows)):
            raise ValueError('Lighting migration cannot override an installed profile')
    if args.azimuth is not None:
        profile['azimuth'] = args.azimuth
    if args.samples is not None:
        profile['samples'] = args.samples
    if args.decoration_shadows is not None:
        profile['decoration_shadows'] = args.decoration_shadows
    if not isinstance(profile.get('decoration_shadows', False), bool):
        raise ValueError('decoration_shadows must be a boolean')
    world, map_name = profile['world'], profile['map']
    source = ROOT / 'assets_dev/worlds' / world / 'maps' / map_name
    native = parse_odm_file(source)['payload']
    # Read the same scene metadata as runtime; Blender does not bundle PyYAML.
    metadata = json.loads(subprocess.check_output([
        '/usr/bin/python3', '-c',
        'import json,sys,yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1]))))',
        str(source.with_suffix('.scene.yml'))], text=True))
    if metadata.get('mechanisms') or metadata.get('scene_profile', 'classic_odm') != 'classic_odm':
        raise ValueError('This producer supports static ClassicOdm scenes; exclude moving mechanisms explicitly first')
    if metadata.get('terrain', {}).get('attribute_overrides'):
        raise ValueError('Terrain attribute overrides require an explicit bake export implementation')
    native['tile_set_lookup_indices'] = metadata['environment']['tile_set_lookup_indices']
    for override in metadata.get('bmodel_faces', {}).get('interactive_faces', []):
        native['bmodels'][override['bmodel_index']]['faces'][override['face_index']]['attributes'] = override['legacy_attributes']
    for key in ['building_page_size', 'terrain_size']:
        if not 64 <= profile[key] <= 4096 or profile[key] & (profile[key]-1):
            raise ValueError(key+' must be a power of two between 64 and 4096')
    if profile['samples'] < 1 or profile['units_per_texel'] <= 0:
        raise ValueError('Samples and texel spacing must be positive')
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    deps = {}
    def dependency(path):
        rel = str(path.relative_to(ROOT / 'assets_dev'))
        deps[rel] = fnv(path.read_bytes())
    dependency(source)
    dependency(source.with_suffix('.scene.yml'))
    recipe = source.with_suffix('.bake.json')
    recipe_data = {'profile': profile, 'backend': bpy.app.version_string,
                   'producer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   'geometry_helper_sha256': hashlib.sha256(
                       Path(__file__).with_name('bake_geometry.py').read_bytes()).hexdigest(),
                   'asset_helper_sha256': hashlib.sha256(
                       Path(__file__).with_name('bake_assets.py').read_bytes()).hexdigest()}
    if profile.get('decoration_shadows', False):
        recipe_data['decoration_helper_sha256'] = hashlib.sha256(
            Path(__file__).with_name('bake_decorations.py').read_bytes()).hexdigest()
    if retained is not None:
        recipe_data = dict(installed_recipe)
        stage = 'sun_direct' if args.sun_direct_only else 'model_probe'
        recipe_data[stage+'_producer_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        recipe_data[stage+'_backend'] = bpy.app.version_string
    (out / recipe.name).write_text(json.dumps(recipe_data, sort_keys=True, indent=2)+'\n')
    deps[str(recipe.relative_to(ROOT / 'assets_dev'))] = fnv((out / recipe.name).read_bytes())
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = profile['samples']
    scene.cycles.seed = 17
    scene.cycles.max_bounces = 3
    scene.cycles.diffuse_bounces = 2
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 16
    scene.world.use_nodes = True
    sky = scene.world.node_tree.nodes['Background']
    sky.inputs[0].default_value = (1, 1, 1, 1)
    sun_data = bpy.data.lights.new('baked sun', 'SUN')
    sun_data.angle = math.radians(2)
    sun = bpy.data.objects.new('baked sun', sun_data)
    scene.collection.objects.link(sun)
    a, e = math.radians(profile['azimuth']), math.radians(profile['elevation'])
    toward_sun = Vector((math.cos(e)*math.cos(a), math.cos(e)*math.sin(a), math.sin(e)))
    sun.rotation_euler = (-toward_sun).to_track_quat('-Z', 'Y').to_euler()
    materials = {}
    texture_paths, terrain_paths = bake_texture_paths(ROOT / 'assets_dev', world)
    def material(name, terrain=False):
        key = name.lower() + ('_terrain' if terrain else '')
        if key in materials:
            return materials[key]
        mat = bpy.data.materials.new(key)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes['Principled BSDF']
        bsdf.inputs['Roughness'].default_value = 1
        bsdf.inputs['Specular IOR Level'].default_value = 0
        path = (terrain_paths if terrain else texture_paths).get(name.lower())
        if path is None:
            raise ValueError('Missing authoritative bake material: '+key)
        dependency(path)
        original = bpy.data.images.load(str(path), check_existing=True)
        image = original.copy()
        pixels = np.array(image.pixels[:], dtype=np.float32).reshape(-1,4)
        # Native non-sprite magenta color key, as in ImageAssetLoader. Terrain shore cutouts
        # expose animated water at runtime; use a low-reflectance static water color for bounce.
        transparent = (pixels[:,0] >= 248/255) & (pixels[:,1] <= 8/255) & (pixels[:,2] >= 248/255)
        if terrain:
            pixels[transparent] = (.035,.07,.1,1)
            if name.lower().startswith('wtr'):
                pixels[:] = (.035,.07,.1,1)
        else:
            pixels[transparent,3] = 0
        image.pixels.foreach_set(pixels.ravel())
        image.update()
        tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex.image = image
        tex.interpolation = 'Closest'
        tex.extension = 'REPEAT'
        uv = mat.node_tree.nodes.new('ShaderNodeUVMap')
        uv.uv_map = 'material'
        mat.node_tree.links.new(uv.outputs['UV'], tex.inputs['Vector'])
        mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        mat.node_tree.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
        materials[key] = (mat, tuple(image.size))
        return materials[key]

    page_size = profile['building_page_size']
    pages = []
    direct_pages = []
    records = []
    charts = []
    groups = {}
    for bi, model in enumerate(native['bmodels']):
        for fi, face in enumerate(model['faces']):
            points = [Vector(tuple(model['vertices'][i][k] for k in 'xyz'))
                      for i in face['vertex_indices']]
            record = {'model': bi, 'face': fi, 'page': 65535, 'uvs': [(0,0)]*len(points)}
            records.append(record)
            if len(points) < 3 or face['attributes'] & 0x2000 or not face['texture_name']:
                continue
            basis = face_basis(points)
            if basis is None:
                continue
            axis_u, axis_v = (Vector(axis) for axis in basis)
            coords = [(p.dot(axis_u), p.dot(axis_v)) for p in points]
            lo = np.min(coords, axis=0)
            hi = np.max(coords, axis=0)
            span = np.maximum(hi-lo, 1)
            # UV bounds lie on texel centers, leaving size-1 raster intervals. Tiny
            # oblique faces need interior samples: a 2x2 chart can miss every sample
            # and bake completely black even when the face is exposed to the sky.
            w, h = [max(4, math.ceil(v/profile['units_per_texel']) + 1) for v in span]
            mat, (tw, th) = material(face['texture_name'])
            tex_uv = [((u+face['texture_delta_u'])/tw, 1-(v+face['texture_delta_v'])/th)
                      for u,v in zip(face['texture_us'],face['texture_vs'])]
            charts.append({'record': record, 'points': points, 'coords': coords, 'lo': lo, 'span': span,
                           'size': (w, h), 'material_uvs': tex_uv, 'material': mat})

    placements, building_dimensions = pack_lightmap_charts(
        [chart['size'] for chart in charts], page_size)
    for chart, (pi, x, y, w, h) in zip(charts, placements):
        page_width, page_height = building_dimensions[pi]
        light_uv = [((x+.5+(u-chart['lo'][0])/chart['span'][0]*(w-1))/page_width,
                     (y+.5+(v-chart['lo'][1])/chart['span'][1]*(h-1))/page_height)
                    for u,v in chart['coords']]
        chart['record'].update(page=2+pi*2, uvs=light_uv)
        groups.setdefault(pi, []).append(
            (chart['points'], chart['material_uvs'], light_uv, chart['material']))

    # Each page is a mesh with split face vertices, retaining native triangle fans.
    def make_mesh(name, entries, dimensions):
        verts, triangles, uvs, light_uvs, mats = [], [], [], [], []
        for points, texcoords, lighting, mat in entries:
            offset = len(verts)
            verts.extend([tuple(p/128) for p in points])
            uvs.extend(texcoords)
            light_uvs.extend(lighting)
            for i in range(1,len(points)-1):
                triangles.append((offset,offset+i,offset+i+1))
                mats.append(mat)
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(verts, [], triangles)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        scene.collection.objects.link(obj)
        uv = mesh.uv_layers.new(name='material')
        lm = mesh.uv_layers.new(name='lighting')
        slots = {}
        for poly, mat in zip(mesh.polygons,mats):
            if mat.name not in slots:
                slots[mat.name] = len(mesh.materials)
                mesh.materials.append(mat)
            poly.material_index = slots[mat.name]
            for li in poly.loop_indices:
                vi = mesh.loops[li].vertex_index
                uv.data[li].uv = uvs[vi]
                lm.data[li].uv = light_uvs[vi]
        mesh.uv_layers.active = lm
        lm.active_render = True
        return obj, dimensions

    # Exact native diagonal and world coordinates. One world-space terrain atlas in the first proof.
    table_name = {'mm6': 'terrain_tile_data_3.txt', 'mm7': 'terrain_tile_data_2.txt',
                  'mm8': 'terrain_tile_data.txt'}[world]
    table = ROOT / 'assets_dev/engine/data_tables' / table_name
    dependency(table)
    descriptors = list(csv.DictReader(table.open(), delimiter='\t'))
    entries = []
    heights = native['height_map']
    terrain_size = profile['terrain_size']
    for gy in range(127):
        for gx in range(127):
            corners = [(gx,gy),(gx,gy+1),(gx+1,gy),(gx+1,gy+1)]
            points = [Vector(((x-64)*512,(64-y)*512,heights[y*128+x]*32)) for x,y in corners]
            raw = native['tile_map'][gy*128+gx]
            ti = raw if raw < 90 else native['tile_set_lookup_indices'][(raw-90)//36]+(raw-90)%36
            mat, _ = material(descriptors[ti]['texture_name'], terrain=True)
            texcoords = [(0,1),(0,0),(1,1),(1,0)]
            light = [((x/127*(terrain_size-1)+.5)/terrain_size,
                      (y/127*(terrain_size-1)+.5)/terrain_size) for x,y in corners]
            for indices in [(0,3,2),(0,1,3)]:
                entries.append(([points[i] for i in indices], [texcoords[i] for i in indices],
                                [light[i] for i in indices], mat))
    objects = [make_mesh('terrain', entries, (terrain_size, terrain_size))]
    objects.extend(make_mesh('buildings_'+str(pi), groups[pi], building_dimensions[pi])
                   for pi in range(len(building_dimensions)))
    decoration_objects = []
    decoration_report = None
    if profile.get('decoration_shadows', False):
        effective_profile = out / 'effective_profile.json'
        effective_profile.write_text(json.dumps(profile, indent=2) + '\n')
        decoration_report = json.loads(subprocess.check_output([
            '/usr/bin/python3', str(Path(__file__).with_name('bake_decorations.py')),
            '--profile', str(effective_profile), '--output', str(out / 'decoration_masks')], text=True))
        for path in decoration_report['dependencies']:
            dependency(ROOT / 'assets_dev' / path)
        card_materials = {}
        right = Vector((-math.sin(a), math.cos(a), 0))
        for card in decoration_report['cards']:
            if card['mask'] not in card_materials:
                mat = bpy.data.materials.new('decoration_' + Path(card['mask']).stem)
                mat.use_nodes = True
                nodes, links = mat.node_tree.nodes, mat.node_tree.links
                nodes.clear()
                output_node = nodes.new('ShaderNodeOutputMaterial')
                transparent = nodes.new('ShaderNodeBsdfTransparent')
                opaque = nodes.new('ShaderNodeBsdfDiffuse')
                opaque.inputs['Color'].default_value = (0, 0, 0, 1)
                mix = nodes.new('ShaderNodeMixShader')
                mask = nodes.new('ShaderNodeTexImage')
                mask.image = bpy.data.images.load(card['mask'], check_existing=True)
                mask.image.colorspace_settings.name = 'Non-Color'
                mask.extension = 'CLIP'
                mask.interpolation = 'Linear'
                uv = nodes.new('ShaderNodeUVMap')
                uv.uv_map = 'material'
                links.new(uv.outputs['UV'], mask.inputs['Vector'])
                links.new(mask.outputs['Color'], mix.inputs[0])
                links.new(transparent.outputs[0], mix.inputs[1])
                links.new(opaque.outputs[0], mix.inputs[2])
                links.new(mix.outputs[0], output_node.inputs['Surface'])
                card_materials[card['mask']] = mat
            base = Vector(tuple(card['position'][k] for k in 'xyz'))
            half = right * (card['width'] / 2)
            up = Vector((0, 0, card['height']))
            points = [base - half, base + half, base + half + up, base - half + up]
            u0, u1 = (1, 0) if card['mirrored'] else (0, 1)
            uv = [(u0, 0), (u1, 0), (u1, 1), (u0, 1)]
            obj, _ = make_mesh('decoration_' + str(card['index']),
                               [(points, uv, uv, card_materials[card['mask']])], (0, 0))
            obj.visible_camera = False
            obj.visible_diffuse = False
            obj.visible_glossy = False
            obj.visible_transmission = False
            decoration_objects.append(obj)
        # Dense foliage can require many transparent intersections along a sun ray.
        scene.cycles.transparent_max_bounces = max(64, scene.cycles.transparent_max_bounces)
        print('DECORATION SHADOWS', decoration_report['counts'], decoration_report['skip_reasons'], flush=True)
    if args.preview_only:
        camera_data = bpy.data.cameras.new('review camera')
        camera = bpy.data.objects.new('review camera',camera_data)
        scene.collection.objects.link(camera)
        scene.camera = camera
        camera.location = Vector(profile['preview_position'])/128
        target = Vector(profile['preview_target'])/128
        camera.rotation_euler = (target-camera.location).to_track_quat('-Z','Y').to_euler()
        camera_data.clip_end = 10000
        camera_data.lens = 32
        scene.render.resolution_x, scene.render.resolution_y = 800,600
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = 'PNG'
        scene.view_settings.view_transform = 'Standard'
        scene.cycles.samples = 8
        sun_data.energy = profile['sun_energy']
        sky.inputs[1].default_value = profile['sky_energy']
        for angle in [45,135,225,315]:
            azimuth = math.radians(angle)
            direction = Vector((math.cos(e)*math.cos(azimuth),math.cos(e)*math.sin(azimuth),math.sin(e)))
            sun.rotation_euler = (-direction).to_track_quat('-Z','Y').to_euler()
            # Rotate the bake-only cards around their own ground anchors for each preview sun.
            for obj, card in zip(decoration_objects, decoration_report['cards'] if decoration_report else []):
                base = Vector(tuple(card['position'][k] for k in 'xyz')) / 128
                rotation = Matrix.Rotation(azimuth - a, 4, 'Z')
                obj.matrix_world = Matrix.Translation(base) @ rotation @ Matrix.Translation(-base)
            scene.render.filepath = str(out / ('sun_'+str(angle)+'.png'))
            bpy.ops.render.render(write_still=True)
        return
    # Probe receivers do not cast shadows or contribute bounce. They sample diffuse light facing upward,
    # matching the native billboard's ground-facing illumination convention.
    locations = set()
    for gy in range(1,127):
        for gx in range(1,127):
            locations.add(((gx-64)*512, (64-gy)*512))
    for model in native['bmodels']:
        if not model['vertices']:
            continue
        for x in range(math.floor(min(v['x'] for v in model['vertices'])/128)*128-128,
                       math.ceil(max(v['x'] for v in model['vertices'])/128)*128+129,128):
            for y in range(math.floor(min(v['y'] for v in model['vertices'])/128)*128-128,
                           math.ceil(max(v['y'] for v in model['vertices'])/128)*128+129,128):
                if -32256 <= x <= 31744 and -31744 <= y <= 32256:
                    locations.add((x,y))
    probe_positions = []
    for x,y in sorted(locations):
        gx, gy = x/512+64, 64-y/512
        ix, iy = int(gx),int(gy)
        fx, fy = gx-ix,gy-iy
        tl,tr,bl,br = [heights[j*128+i]*32 for i,j in [(ix,iy),(ix+1,iy),(ix,iy+1),(ix+1,iy+1)]]
        z = tl+(tr-tl)*fx+(bl-tl)*fy if fx+fy <= 1 else br+(bl-br)*(1-fx)+(tr-br)*(1-fy)
        for dz in [96,384,1152]:
            probe_positions.append((x,y,z+dz))
    probe_size = 2**math.ceil(math.log2(math.ceil(math.sqrt(len(probe_positions)))*3))
    columns = probe_size//3
    probe_mat = bpy.data.materials.new('probe receiver')
    probe_mat.use_nodes = True
    probe_mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (1,1,1,1)
    probe_entries = []
    probe_texels = []
    for index,(x,y,z) in enumerate(probe_positions):
        px,py = (index%columns)*3, (index//columns)*3
        coords = [((px+.25)/probe_size,(py+.25)/probe_size),
                  ((px+2.75)/probe_size,(py+.25)/probe_size),
                  ((px+2.75)/probe_size,(py+2.75)/probe_size),
                  ((px+.25)/probe_size,(py+2.75)/probe_size)]
        points = [Vector((x+dx,y+dy,z)) for dx,dy in [(-.5,-.5),(.5,-.5),(.5,.5),(-.5,.5)]]
        probe_entries.append((points,[(0,0)]*4,coords,probe_mat))
        probe_texels.append((py+1,px+1))
    probe_object = make_mesh('probes',probe_entries,(probe_size,probe_size))
    probe_object[0].visible_shadow = False
    probe_object[0].visible_diffuse = False
    probe_object[0].visible_glossy = False
    objects.append(probe_object)
    probe_values = {}
    stats = {'profile': profile, 'blender': bpy.app.version_string, 'device': scene.cycles.device,
             'sun_direction': list(toward_sun), 'bakes': [], 'dependencies': deps,
             'probe_count': len(probe_positions), 'atlas_pages': 2*(len(objects)-1),
             'atlas_bytes': sum(width*height*8 for obj,(width,height) in objects[:-1])}
    if decoration_report is not None:
        stats['decoration_shadows'] = decoration_report
    for obj, (width, height) in objects:
        if args.model_probes_only and obj.name != 'probes':
            continue
        if args.sun_direct_only and obj.name == 'probes':
            continue
        target = bpy.data.images.new(obj.name, width=width, height=height, float_buffer=True)
        for mat in obj.data.materials:
            node = mat.node_tree.nodes.get('BakeTarget') or mat.node_tree.nodes.new('ShaderNodeTexImage')
            node.name = 'BakeTarget'
            node.image = target
            mat.node_tree.nodes.active = node
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        scene.render.bake.use_pass_color = False
        scene.render.bake.use_pass_direct = True
        scene.render.bake.use_pass_indirect = True
        scene.render.bake.margin = 0 if obj.name == 'probes' else 3
        terms = ['sun', 'sky'] if retained is None else []
        if obj.name == 'probes':
            terms += ['sun_direct', 'sun_indirect']
        elif not args.model_probes_only:
            terms += ['sun_direct']
        for term in terms:
            for caster in decoration_objects:
                caster.hide_render = not term.startswith('sun')
            scene.render.bake.use_pass_direct = term != 'sun_indirect'
            scene.render.bake.use_pass_indirect = term != 'sun_direct'
            sun_data.energy = profile['sun_energy'] if term.startswith('sun') else 0
            sky.inputs[1].default_value = profile['sky_energy'] if term == 'sky' else 0
            start = time.monotonic()
            bpy.ops.object.bake(type='DIFFUSE')
            pixels = np.array(target.pixels[:], dtype=np.float32).reshape(height,width,4)
            np.save(out / (obj.name+'_'+term+'.npy'), pixels)
            payload = rgbm(pixels)
            if obj.name == 'probes':
                probe_values[term] = np.array([pixels[y,x,:3] for y,x in probe_texels])
            elif term == 'sun_direct':
                direct_pages.append((width,height,rle_bgra(payload)))
            else:
                pages.append((width,height,rle_bgra(payload)))
            stats['bakes'].append({'object':obj.name,'term':term,'seconds':time.monotonic()-start,
                                   'max':float(pixels[:,:,:3].max())})
            print('BAKED', stats['bakes'][-1], flush=True)
        bpy.data.images.remove(target)
    if retained is not None:
        page_count = struct.unpack_from('<I', retained, 32)[0]
        page_offset = struct.unpack_from('<I', retained, 48)[0]
        offset, length = struct.unpack_from('<II', retained, page_offset + (page_count-1)*16 + 8)
        retained_end = offset + length
        metadata_bytes = 24 if args.sun_direct_only else 0
        stride = 13 if args.sun_direct_only else 9
        count, dependency_count = struct.unpack_from('<II', retained, retained_end+metadata_bytes)
        cursor = retained_end + metadata_bytes + 8
        old_probes = np.frombuffer(retained, dtype='<f4', count=count*stride, offset=cursor).reshape(count, stride)
        if count != len(probe_positions) or not np.allclose(old_probes[:, :3], probe_positions, atol=.01):
            raise ValueError('Probe migration changed receiver positions')
        probe_values['sun'] = old_probes[:, 3:6]
        probe_values['sky'] = old_probes[:, 6:9]
        if args.sun_direct_only:
            probe_values['sun_indirect'] = old_probes[:, 9:12]
        cursor += count * stride * 4
        old_dependencies = {}
        for _ in range(dependency_count):
            length, digest = struct.unpack_from('<IQ', retained, cursor)
            cursor += 12
            name = retained[cursor:cursor+length].decode()
            cursor += length
            path = ROOT / 'assets_dev' / name
            if fnv(path.read_bytes()) != digest:
                raise ValueError('Stale installed bake dependency: ' + name)
            old_dependencies[name] = digest
        if cursor != len(retained):
            raise ValueError('Invalid installed extension length')
        # The atlas bake keeps its provenance. Only the recipe hash and model probes change.
        old_dependencies[str(recipe.relative_to(ROOT / 'assets_dev'))] = deps[
            str(recipe.relative_to(ROOT / 'assets_dev'))]
        deps = old_dependencies
    faces = b''.join(struct.pack('<QIIHHI', (r['model']<<32)|r['face'], r['model'],r['face'],r['page'],
                                int(r['page'] != 65535), sum(len(q['uvs']) for q in records[:i]))
                     for i,r in enumerate(records))
    vertices = b''.join(struct.pack('<ffI',u,v,0xffffffff) for r in records for u,v in r['uvs'])
    if args.sun_direct_only:
        old_face_offset, old_vertex_offset, old_light_offset = struct.unpack_from('<3I', retained, 52)
        if faces != retained[old_face_offset:old_vertex_offset] or vertices != retained[old_vertex_offset:old_light_offset]:
            raise ValueError('Direct-sun migration changed installed atlas placement; reproduce its geometry recipe')
        if len(direct_pages) * 2 != page_count:
            raise ValueError('Direct-sun migration changed installed atlas count')
        for index,(width,height,_) in enumerate(direct_pages):
            if (width,height) != struct.unpack_from('<II', retained, page_offset+index*2*16):
                raise ValueError('Direct-sun migration changed installed atlas dimensions')
    page_offset = 96
    face_offset = page_offset + len(pages)*16
    vertex_offset = face_offset + len(faces)
    light_offset = vertex_offset + len(vertices)
    pixel_offset = light_offset
    payloads, page_records = bytearray(), bytearray()
    for w,h,data in pages:
        page_records += struct.pack('<IIII',w,h,pixel_offset+len(payloads),len(data))
        payloads += data
    # Cycles DIFFUSE light-only is Lambertian outgoing radiance: a unit white receiver has E / pi.
    # Direct visibility is measured in a direct-only bake, never inferred from total sun+bounce RGB.
    direct_response = profile['sun_energy'] / math.pi
    horizontal_response = direct_response * toward_sun.z
    if horizontal_response <= 0:
        raise ValueError('Model sunlight probe bake requires positive sun elevation and energy')
    visibility = old_probes[:, 12] if args.sun_direct_only else np.clip(
        probe_values['sun_direct'].mean(axis=1) / horizontal_response, 0, 1)
    extension = bytearray(struct.pack('<6fII', *toward_sun, *([direct_response]*3), len(probe_positions), len(deps)))
    if args.sun_direct_only:
        extension[:24] = retained[retained_end:retained_end+24]
    for position,sun_value,sky_value,indirect,visible in zip(
            probe_positions, probe_values['sun'], probe_values['sky'], probe_values['sun_indirect'], visibility):
        extension += struct.pack('<13f', *position, *sun_value, *sky_value, *indirect, visible)
    for name, digest in sorted(deps.items()):
        encoded = name.encode()
        extension += struct.pack('<IQ',len(encoded),digest)+encoded
    if not args.model_probes_only:
        extension += struct.pack('<I',len(direct_pages))
        for width,height,data in direct_pages:
            extension += struct.pack('<III',width,height,len(data))+data
    total = pixel_offset + len(payloads) + len(extension)
    header = bytearray(96)
    header[:8] = b'OYMLIT1\0'
    struct.pack_into('<IIQ',header,8,3,96,fnv(source.read_bytes()))
    struct.pack_into('<12I',header,24,len(native['bmodels']),len(records),len(pages),len(records),
                     len(vertices)//12,0,page_offset,face_offset,vertex_offset,light_offset,pixel_offset,total)
    struct.pack_into('<II4f',header,72,0,1,-32768,32768,65024,-65024)
    output = out / (source.stem+'.lighting')
    if retained is not None:
        prefix = bytearray(retained[:retained_end])
        assert prefix[96:] == retained[96:retained_end]
        probe_bytes = stride * 4
        old_start = retained_end + metadata_bytes + 8
        old_probe_bytes = retained[old_start:old_start+count*probe_bytes]
        new_probe_bytes = b''.join(extension[32+i*52:32+i*52+probe_bytes] for i in range(count))
        assert old_probe_bytes == new_probe_bytes, 'Migration changed existing sprite samples'
        stats['retained_surface_sha256'] = hashlib.sha256(prefix[96:]).hexdigest()
        stats['retained_sprite_probe_sha256'] = hashlib.sha256(old_probe_bytes).hexdigest()
        struct.pack_into('<II', prefix, 8, 5 if args.sun_direct_only else 4, 96)
        struct.pack_into('<I', prefix, 68, len(prefix) + len(extension))
    else:
        struct.pack_into('<I', header, 8, 5)
        prefix = header+page_records+faces+vertices+payloads
    output.write_bytes(prefix+extension)
    stats['model_sun_direction'] = list(toward_sun)
    stats['model_direct_response'] = direct_response
    stats['model_visibility_range'] = [float(visibility.min()), float(visibility.max())]
    stats['retained_surface_and_sprite_lighting'] = retained is not None
    stats['direct_sun_pages'] = len(direct_pages)
    stats['direct_sun_compressed_bytes'] = sum(len(data) for _,_,data in direct_pages)
    stats['output_bytes'] = output.stat().st_size
    stats['output_sha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
    (out / 'report.json').write_text(json.dumps(stats,indent=2)+'\n')
    print('OUTPUT',output,flush=True)


if __name__ == '__main__':
    main()
