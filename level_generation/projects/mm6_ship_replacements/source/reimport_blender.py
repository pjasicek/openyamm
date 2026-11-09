"""Import the built native ship and existing pier into a separate, packed Blender scene."""
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT / "util"))
from map_export import parse_odm_file

config = json.loads((PROJECT / "source/ships.json").read_text())
report = json.loads((PROJECT / "build/report.json").read_text())
assets = PROJECT / "playtest/assets_dev/worlds/mm6"
scenes = set()

def import_berth(map_config, ship, first_model):
    data = parse_odm_file(PROJECT / "build" / map_config["map"])["payload"]
    previous = bpy.context.window.scene
    scene = bpy.data.scenes.new(map_config["location"] + " - " + ship["service"])
    bpy.context.window.scene = scene
    scene.render.engine = previous.render.engine
    scene["native_map"] = "mm6/" + map_config["map"]
    scene["native_origin"] = ship["position"]
    scene["native_units_per_blender_unit"] = 128
    scene["rebuild_source"] = "source/ships.json + source/port_ship.cpp; run build.py"
    scene["scope"] = "Reimport of final native ship and unchanged pier. Terrain and billboards omitted."
    scene.world = bpy.data.worlds.new("MM6 ships inspection world")
    scene.world.use_nodes = True
    background = next(node for node in scene.world.node_tree.nodes if node.type == "BACKGROUND")
    background.inputs[0].default_value = (0.22, 0.28, 0.34, 1)
    background.inputs[1].default_value = 0.8
    materials = {}
    sizes = {}

    indices = ([ship["pier_model"]] if ship["pier_model"] is not None else []) + list(range(first_model, first_model + 5))
    for index in indices:
        model = data["bmodels"][index]
        vertices = [tuple((vertex[axis] - ship["position"][i]) / 128 for i, axis in enumerate("xyz"))
                    for vertex in model["vertices"]]
        faces = [face for face in model["faces"] if len(face["vertex_indices"]) >= 3
                 and not face["attributes"] & 0x2000]
        mesh = bpy.data.meshes.new(model["name"])
        mesh.from_pydata(vertices, [], [face["vertex_indices"] for face in faces])
        mesh.update()
        obj = bpy.data.objects.new("BModel " + str(index) + " " + model["name"], mesh)
        scene.collection.objects.link(obj)
        obj["bmodel_index"] = index
        obj["service_event"] = ship["event"] if index == first_model + 2 else 0
        if index == first_model + 2:
            obj["service_face_index"] = 42
        slots = {}
        uv = mesh.uv_layers.new(name="Native ODM UV")
        attribute_parameters = mesh.attributes.bl_rna.functions["new"].parameters
        integer_type = next(item.identifier for item in attribute_parameters["type"].enum_items
                            if item.identifier.lower() == "int")
        face_domain = next(item.identifier for item in attribute_parameters["domain"].enum_items
                           if item.identifier.lower() == "face")
        face_ids = mesh.attributes.new(name="native_face_index", type=integer_type, domain=face_domain)
        for polygon, face in zip(mesh.polygons, faces):
            key = face["texture_name"].lower()
            if key not in materials:
                material = bpy.data.materials.new("MM6 ship " + key)
                material.use_nodes = True
                shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
                shader.inputs["Roughness"].default_value = 1
                texture = material.node_tree.nodes.new("ShaderNodeTexImage")
                enhanced = assets / "textures_x2" / (key + ".png")
                path = enhanced if enhanced.exists() else assets / "textures" / (key + ".bmp")
                texture.image = bpy.data.images.load(str(path), check_existing=False)
                texture.image.pack()
                divisor = 2 if enhanced.exists() else 1
                sizes[key] = [value / divisor for value in texture.image.size]
                texture.interpolation = next(item.identifier for item in texture.bl_rna.properties["interpolation"].enum_items
                                             if item.identifier.lower() == "closest")
                material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
                materials[key] = material
            if key not in slots:
                slots[key] = len(mesh.materials)
                mesh.materials.append(materials[key])
            polygon.material_index = slots[key]
            face_ids.data[polygon.index].value = face["index"]
            width, height = sizes[key]
            for loop, u, v in zip(polygon.loop_indices, face["texture_us"], face["texture_vs"]):
                uv.data[loop].uv = ((u + face["texture_delta_u"]) / width,
                                    1 - (v + face["texture_delta_v"]) / height)

    sun_type = next(item.identifier for item in bpy.types.Light.bl_rna.properties["type"].enum_items
                    if item.identifier.lower() == "sun")
    light_data = bpy.data.lights.new("Ship inspection sun", sun_type)
    light_data.energy = 2.0
    light = bpy.data.objects.new(light_data.name, light_data)
    scene.collection.objects.link(light)
    light.rotation_euler = (0.4, -0.6, -0.4)
    camera_data = bpy.data.cameras.new("Ship and pier camera")
    camera_data.type = next(item.identifier for item in camera_data.bl_rna.properties["type"].enum_items
                            if item.identifier.lower() == "ortho")
    camera_data.ortho_scale = 41
    camera_data.clip_end = 500
    camera = bpy.data.objects.new(camera_data.name, camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.location = (-35, -40, 26)
    camera.rotation_euler = (Vector((-10, 0, 3)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            space = area.spaces.active
            space.shading.type = next(item.identifier for item in space.shading.bl_rna.properties["type"].enum_items
                                      if item.identifier.lower() == "material")
            region = space.region_3d
            region.view_perspective = next(item.identifier for item in region.bl_rna.properties["view_perspective"].enum_items
                                           if item.identifier.lower() == "camera")
    scenes.add(scene)

for map_config, map_report in zip(config["maps"], report["maps"]):
    for i, ship in enumerate(map_config["ships"]):
        import_berth(map_config, ship, map_report["original_bmodels"] + i * 5)
bpy.data.libraries.write(str(PROJECT / "source/mm6_ships_and_piers.blend"), scenes, fake_user=True, compress=True)
print({"scenes": len(scenes), "objects": sum(len(scene.objects) for scene in scenes)})
