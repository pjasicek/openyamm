"""The S10 nest's dark mound (BROOD_SPIRES.md section 14: "one model, a dark texture"): the baked hes_nest_mound with
its base colour darkened and desaturated and its glow removed, written beside it in the decorations workspace as
hes_nest_mound_dead_export.glb (its design entry copies the live mound's length, so the stage sizes them alike).

    blender --background --factory-startup --python level_generation/projects/hesper_out3/make_dead_nest_blender.py
"""
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'level_generation/props/hesper_decorations/work/codex_tex'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(WORK / 'hes_nest_mound_export.glb'))
done = set()
for material in bpy.data.materials:
    if not material.use_nodes:
        continue
    for node in material.node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            node.inputs['Emission Strength'].default_value = 0.0
            for link in list(node.inputs['Emission Color'].links):
                material.node_tree.links.remove(link)
        if node.type == 'TEX_IMAGE' and node.image and node.image.name not in done:
            if any(link.to_socket.name == 'Base Color' for link in node.outputs['Color'].links):
                image = node.image
                pixels = np.array(image.pixels[:], dtype=np.float32).reshape(-1, 4)
                grey = pixels[:, :3].mean(axis=1, keepdims=True)
                pixels[:, :3] = (pixels[:, :3] * 0.4 + grey * 0.6) * 0.32
                image.pixels.foreach_set(pixels.ravel())
                image.pack()
                done.add(image.name)
bpy.ops.export_scene.gltf(filepath=str(WORK / 'hes_nest_mound_dead_export.glb'), export_format='GLB')
print('DEAD_NEST', WORK / 'hes_nest_mound_dead_export.glb', sorted(done))
