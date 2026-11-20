"""Refresh packed material images without touching UVs, normals or animation."""
import bpy, sys, runpy
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P/'scripts'))
import reduction_common as C
for level in range(4):
    file = P/f'work/runtime_lod{level}.blend'
    bpy.ops.wm.open_mainfile(filepath=str(file)); C.reset()
    for material in bpy.data.objects['Body'].data.materials:
        for node in material.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image and node.image.filepath.endswith(('_basecolor.png','_normal.png')):
                image = bpy.data.images.load(node.image.filepath, check_existing=False)
                if node.image.filepath.endswith('_normal.png'):image.colorspace_settings.name='Non-Color'
                image.pack(); node.image = image
    bpy.ops.wm.save_as_mainfile(filepath=str(file))
    if level == 0: bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_natm.blend'))
runpy.run_path(str(P/'scripts/quick_export.py'), run_name='__main__')
