"""Render and measure the original Meshy return without changing it."""
import bpy
import json
import os
from pathlib import Path
import sys

import numpy as np
from mathutils import Vector

try:
    project = Path(__file__).resolve().parents[1]
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    source, destination = args or ["meshy/body_geometry_v1/model_urls_glb.glb", "review/geometry_v1"]
    review = project / destination
    review.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(project / source))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    assert meshes, "No mesh in the service return"
    vertices = np.array([tuple(obj.matrix_world @ v.co) for obj in meshes for v in obj.data.vertices])
    assert np.isfinite(vertices).all(), "Non-finite vertex positions"
    low, high = vertices.min(axis=0), vertices.max(axis=0)
    center = Vector((low + high) / 2)
    span = float((high - low).max())
    assert span > 0
    report = {"source": source, "space": "Blender import, before normalization",
              "bounds": [low.tolist(), high.tolist()], "dimensions": (high - low).tolist(), "objects": []}
    material = bpy.data.materials.new("Inspection clay")
    material.diffuse_color = (0.35, 0.39, 0.43, 1)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (0.35, 0.39, 0.43, 1)
    shader.inputs["Roughness"].default_value = 0.72
    for obj in meshes:
        obj.data.calc_loop_triangles()
        report["objects"].append({"name": obj.name, "vertices": len(obj.data.vertices),
                                  "triangles": len(obj.data.loop_triangles)})
        obj.data.materials.clear()
        obj.data.materials.append(material)
        for polygon in obj.data.polygons:
            polygon.material_index = 0
    report["triangles"] = sum(obj["triangles"] for obj in report["objects"])
    (review / "geometry.json").write_text(json.dumps(report, indent=2) + "\n")
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 960
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world = bpy.data.worlds.new("Inspection world")
    scene.world.color = (0.16, 0.16, 0.16)
    scene.view_settings.view_transform = "AgX"
    for index, offset in enumerate([(1, -2, 3), (-2, -1, 1), (0, 2, 2)]):
        data = bpy.data.lights.new("Review light " + str(index), "AREA")
        data.energy = 40 * span * span
        data.shape = "DISK"
        data.size = span * 2
        obj = bpy.data.objects.new(data.name, data)
        scene.collection.objects.link(obj)
        obj.location = center + Vector(offset) * span
        obj.rotation_euler = (center - obj.location).to_track_quat("-Z", "Y").to_euler()
    camera_data = bpy.data.cameras.new("Review camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = span * 1.4
    camera = bpy.data.objects.new("Review camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    for name, offset in [("front", (0, -3, 0)), ("side", (3, 0, 0)), ("top", (0, 0, 3)),
                         ("quarter", (2, -3, 2))]:
        camera.location = center + Vector(offset) * span
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(review / (name + ".png"))
        bpy.ops.render.render(write_still=True)
        assert (review / (name + ".png")).is_file()
    print(json.dumps(report), flush=True)
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)
except BaseException:
    import traceback
    traceback.print_exc()
    sys.stderr.flush()
    os._exit(1)
