"""Render the authored canyon den and staged Gloamlings against native terrain, in an isolated scene."""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

P=Path(__file__).resolve().parents[1]
PROJECT = P.parents[1]/'projects/hesper_out1'
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file  # noqa: E402

RECIPE = json.loads((ROOT / 'level_generation/minimaps/approved_recipe.json').read_text())
SCALE = 1 / 128.0
ART = ROOT / 'design/kreegan_world/art'
native = parse_odm_file(PROJECT / 'runtime/worlds/hesper/maps/hes_out1.odm')['payload']

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# The terrain: 128 x 128 samples, cells split along the anti-diagonal as the game does, plus one more row and column
# repeating the last ones, so the map's whole square is covered (the native grid ends one cell short of it).
heights = native['height_map']
vertices, faces = [], []
for gy in range(129):
    for gx in range(129):
        z = heights[min(gy, 127) * 128 + min(gx, 127)] * 32
        vertices.append(((gx - 64) * 512 * SCALE, (64 - gy) * 512 * SCALE, z * SCALE))
for gy in range(128):
    for gx in range(128):
        a, b, c, d = gy * 129 + gx, gy * 129 + gx + 1, (gy + 1) * 129 + gx, (gy + 1) * 129 + gx + 1
        faces += [(a, c, b), (b, c, d)]
mesh = bpy.data.meshes.new('terrain')
mesh.from_pydata(vertices, [], faces)
uv_layer = mesh.uv_layers.new()
for polygon in mesh.polygons:
    for loop in polygon.loop_indices:
        x, y, _ = vertices[mesh.loops[loop].vertex_index]
        uv_layer.data[loop].uv = (x / SCALE / 65536 + 0.5, y / SCALE / 65536 + 0.5)
mesh.shade_smooth()
terrain = bpy.data.objects.new('terrain', mesh)
scene.collection.objects.link(terrain)


def image_material(name, path, repeat=False):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    bsdf = nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = 1.0
    texture = nodes.new('ShaderNodeTexImage')
    texture.image = bpy.data.images.load(str(path), check_existing=True)
    texture.extension = 'REPEAT' if repeat else 'EXTEND'
    material.node_tree.links.new(texture.outputs['Color'], bsdf.inputs['Base Color'])
    return material


terrain.data.materials.append(image_material('ground', PROJECT / 'work/ground_colour.png'))

# The BModels, with their textures (UV 1.0 = the texture's native size, as written).
textures = {}
for folder in ['textures_d0/blv', 'textures_out1/masters', 'textures_interiors/masters']:
    for png in (ART / folder).glob('*.png'):
        textures[png.stem] = png
for obj_path in [PROJECT/'source/models/gloamling_den.obj',PROJECT/'source/models/pumping_station.obj']:
    if obj_path.stem == 'colliders':
        continue
    before = set(scene.objects)
    bpy.ops.wm.obj_import(filepath=str(obj_path), forward_axis='Y', up_axis='Z')
    for obj in set(scene.objects) - before:
        for slot in obj.material_slots:
            name = slot.material.name.split('.')[0]
            if name in textures:
                slot.material = image_material('bm_' + name, textures[name], repeat=True)


actors=json.loads((PROJECT/'source/hes_out1.scene.yml').read_text())['initial_state']['actors']
for a in [a for a in actors if a['monster_id']==10320]:
 before=set(scene.objects);bpy.ops.import_scene.gltf(filepath=str(P/'review/viewer/gloamer_a.glb'))
 objects=set(scene.objects)-before;root=bpy.data.objects.new('DenGloamling',None);scene.collection.objects.link(root)
 for obj in objects:
  if obj.parent not in objects:obj.parent=root
 rig=next(o for o in objects if o.type=='ARMATURE');act=next(ac for ac in bpy.data.actions if ac.name.split('.')[0].startswith('Standing'))
 rig.animation_data.action=act
 if len(act.slots):rig.animation_data.action_slot=act.slots[0]
 root.scale=(85.737256843*SCALE,)*3;root.location=Vector(tuple(a['position'][v] for v in ('x','y','z')))*SCALE
 root.rotation_euler.z=a['initial_yaw_units']*math.tau/2048+math.pi/2
scene.frame_set(0)
sun=bpy.data.objects.new('Sun',bpy.data.lights.new('Sun','SUN'));sun.data.energy=2;sun.rotation_euler=(.6,-.4,-.5);scene.collection.objects.link(sun)
scene.world=bpy.data.worlds.new('Overcast');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.45,.45,.5,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.4
camera=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));scene.collection.objects.link(camera);scene.camera=camera;camera.data.clip_end=1000;camera.data.lens=24
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.resolution_percentage=100
out=P/'review/canyon_den';out.mkdir(exist_ok=True)
for name,position,target in [('mouth',(15100,-10080,1010),(16416,-10080,1500)),('inside',(15800,-10080,1480),(16500,-10080,1520)),('oblique',(14300,-12400,2100),(16350,-10080,1450))]:
 camera.location=Vector(position)*SCALE;camera.rotation_euler=(Vector(target)*SCALE-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
import os
sys.stdout.flush();sys.stderr.flush();os._exit(0)
