"""Run in a dedicated background Blender process; preserve the approved recipe and exact map coordinates."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

HERE = Path(__file__).resolve().parent
DEFAULT_HERE = HERE
ROOT = HERE.parents[1]
STUDY = ROOT/'level_generation/ui/hud_inventory/minimap_study_20260927'
PILOT = STUDY/'new_sorpigal'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2)+'\n')
    temporary.replace(path)


def render(entry, recipe):
    out = HERE/entry['directory']
    data = read(out/'scene.json')
    provenance = dict(recipe_sha256=sha(HERE/'approved_recipe.json'), scene_sha256=sha(out/'scene.json'),
                      template_sha256=sha(PILOT/'new_sorpigal_vinevi.blend'))
    if (out/'capture.json').exists():
        current = read(out/'capture.json')
        assert current['provenance'] == provenance, 'Existing render inputs changed; create a new revision'
        assert all(sha(out/name) == expected for name, expected in current['renders'].items())
        return current
    assert read(STUDY/'vinevi_recipe.json') == recipe
    if HERE == DEFAULT_HERE and entry['world'] == 'mm6' and entry['map'] == 'oute3.odm':
        for src, dst in [('vinevi_terrain_master.png', 'terrain_master.png'),
                         ('vinevi_objects_master.png', 'objects_master.png'),
                         ('new_sorpigal_vinevi.blend', 'scene.blend')]:
            shutil.copy2(PILOT/src, out/dst)
        # The copied scene's texture references are relative to the pilot's directory; remap when saving below.
        with bpy.data.libraries.load(str(PILOT/'new_sorpigal_vinevi.blend'), link=False) as (source, target):
            target.scenes = list(source.scenes)
        bpy.data.libraries.write(str(out/'scene.blend'), {target.scenes[0]}, path_remap='RELATIVE_ALL')
        report = read(PILOT/'vinevi_capture.json')
        report['reuse'] = 'Exact user-approved New Sorpigal renders; postprocessing must match the approved PNG'
    else:
        assert bpy.app.background, 'Batch rendering owns only its dedicated background process'
        bpy.ops.wm.read_factory_settings(use_empty=True)
        with bpy.data.libraries.load(str(PILOT/'new_sorpigal_vinevi.blend'), link=False) as (source, target):
            target.scenes = list(source.scenes)
        assert len(target.scenes) == 1
        scene = target.scenes[0]
        scene.name = entry['world']+' '+entry['map']+' approved minimap'
        bpy.context.window.scene = scene
        for obj in list(scene.objects):
            if obj.type == 'MESH':
                bpy.data.objects.remove(obj, do_unlink=True)
        terrain_collection = next(c for c in scene.collection.children if c.name.startswith('Vinevi terrain'))
        models_collection = next(c for c in scene.collection.children if c.name.startswith('Vinevi buildings'))
        template_capture = read(PILOT/'vinevi_capture.json')
        assert template_capture['recipe'] == recipe
        assert scene.cycles.samples == recipe['render']['samples']
        assert scene.cycles.use_denoising == recipe['render']['denoising']

        def material(name, path):
            mat = bpy.data.materials.new(entry['world']+' '+name)
            mat.use_nodes = True
            bsdf = next(node for node in mat.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
            bsdf.inputs['Roughness'].default_value = 1
            bsdf.inputs['Specular IOR Level'].default_value = 0
            texture = mat.node_tree.nodes.new('ShaderNodeTexImage')
            texture.image = bpy.data.images.load(str(path), check_existing=True)
            assert 'Linear' in [i.identifier for i in texture.bl_rna.properties['interpolation'].enum_items]
            texture.interpolation = 'Linear'
            mat.node_tree.links.new(texture.outputs['Color'], bsdf.inputs['Base Color'])
            return mat

        def mesh_object(name, vertices, faces, uvs, materials, indices, collection):
            mesh = bpy.data.meshes.new(name)
            mesh.from_pydata(vertices, [], faces)
            mesh.update()
            obj = bpy.data.objects.new(name, mesh)
            collection.objects.link(obj)
            obj.visible_shadow = False
            for mat in materials:
                mesh.materials.append(mat)
            for polygon, index in zip(mesh.polygons, indices):
                polygon.material_index = index
            layer = mesh.uv_layers.new(name='Map UV')
            assert len(layer.data) == len(uvs)
            for loop, uv in zip(layer.data, uvs):
                loop.uv = uv
            return obj

        mat = material('Terrain', out/'terrain.png')
        vertices = [((x-64)*4, (64-y)*4, data['height_map'][y*128+x]/4) for y in range(128) for x in range(128)]
        faces = []
        for y in range(127):
            for x in range(127):
                nw = y*128+x
                faces.extend([(nw, nw+128, nw+1), (nw+1, nw+128, nw+129)])
        uvs = [(index % 128/128, 1-(index//128)/128) for face in faces for index in face]
        terrain = mesh_object('Exact terrain', vertices, faces, uvs, [mat], [0]*len(faces), terrain_collection)
        for polygon in terrain.data.polygons:
            polygon.use_smooth = True
        terrain.data.update()
        normals = [n.vector.copy() for n in terrain.data.corner_normals]
        for polygon in terrain.data.polygons:
            for index in polygon.loop_indices:
                normals[index] = normals[index].lerp(polygon.normal, recipe['terrain_flat_normal_blend']).normalized()
        terrain.data.normals_split_custom_set(normals)
        # The final unsampled strip uses its actual last-row/column tiles, never a universal blue water border.
        mesh_object('Final sampled boundary tiles', [(-256,-256,-.01),(256,-256,-.01),(256,256,-.01),(-256,256,-.01)],
                    [(0,1,2,3)], [(0,0),(1,0),(1,1),(0,1)], [mat], [0], terrain_collection)
        materials = {name: material(name, row['path']) for name, row in data['materials'].items()}
        models = []
        for model in data['bmodels']:
            vertices = [tuple(v[axis]/128 for axis in 'xyz') for v in model['vertices']]
            faces, uvs, indices, slots = [], [], [], []
            for face in model['faces']:
                if face['attributes'] & 0x2000 or len(face['vertex_indices']) < 3:
                    continue
                name = face['texture_name'].lower()
                if name not in slots:
                    slots.append(name)
                width, height = data['materials'][name]['logical_size']
                faces.append(tuple(face['vertex_indices']))
                uvs.extend(((u+face['texture_delta_u'])/width, 1-(v+face['texture_delta_v'])/height)
                           for u,v in zip(face['texture_us'],face['texture_vs']))
                indices.append(slots.index(name))
            models.append(mesh_object('BModel '+str(model['index']), vertices, faces, uvs,
                                      [materials[n] for n in slots], indices, models_collection))
        bpy.context.view_layer.update()
        errors = []
        for obj, model in zip(models, data['bmodels']):
            for vertex, expected in zip(obj.data.vertices, model['vertices']):
                xyz = Vector(tuple(expected[a]/128 for a in 'xyz'))
                assert (obj.matrix_world @ vertex.co - xyz).length == 0
                uv = world_to_camera_view(scene, scene.camera, xyz)
                errors.append(max(abs(uv.x-(expected['x']+32768)/65536),
                                  abs(uv.y-(expected['y']+32768)/65536))*1024)
        assert max(errors, default=0) < .001
        for index, vertex in enumerate(terrain.data.vertices):
            y, x = divmod(index, 128)
            assert tuple(vertex.co) == ((x-64)*4, (64-y)*4, data['height_map'][index]/4)
        report = dict(blender=bpy.app.version_string, scene=scene.name, recipe=recipe, model_count=len(models),
                      vertex_controls=len(errors), max_projection_error_x2_pixels=max(errors, default=0),
                      terrain_vertices_unchanged=True, geometry_moved=False,
                      camera=dict(location=list(scene.camera.location), ortho_scale=scene.camera.data.ortho_scale),
                      margin='Native tile-map last row/column on a background plane; world bounds unchanged')
        for layer_name, filename in [('Terrain', 'terrain_master.png'), ('Objects', 'objects_master.png')]:
            for layer in scene.view_layers:
                layer.use = layer.name == layer_name
            bpy.context.window.view_layer = scene.view_layers[layer_name]
            scene.render.filepath = str(out/filename)
            bpy.ops.render.render(write_still=True)
        for layer in scene.view_layers:
            layer.use = True
        bpy.data.libraries.write(str(out/'scene.blend'), {scene}, path_remap='RELATIVE_ALL')
    report['provenance'] = provenance
    report['renders'] = {name: sha(out/name) for name in ['terrain_master.png', 'objects_master.png']}
    save(out/'capture.json', report)
    return report


def main():
    global HERE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--world', choices=['mm6','mm7','mm8'])
    parser.add_argument('--map')
    parser.add_argument('--workspace', type=Path, default=DEFAULT_HERE, help='Prepared revision directory')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    HERE = args.workspace.resolve()
    recipe = read(HERE/'approved_recipe.json')
    available = read(HERE/'scope.json')['records'] if (HERE/'scope.json').exists() else [
        read(HERE/'maps'/args.world/args.map/'scene.json')]
    entries = [r for r in available if (not args.world or args.world == r['world']) and
               (not args.map or args.map == Path(r['map']).stem)]
    start = time.time()
    for index, entry in enumerate(entries):
        save(HERE/'render_progress.json', dict(status='rendering', current=entry, completed=index, total=len(entries)))
        try:
            render(entry, recipe)
        except Exception as error:
            save(HERE/'render_progress.json',dict(status='failed',current=entry,completed=index,error=str(error)))
            raise
        print('MINIMAP_COMPLETE', entry['world'], entry['map'], index+1, '/', len(entries), flush=True)
    save(HERE/'render_progress.json', dict(status='complete', completed=len(entries), total=len(entries), seconds=time.time()-start))


if __name__ == '__main__':
    main()
