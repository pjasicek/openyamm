import bpy
from pathlib import Path
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/before_scales_v9/export/mm6_drg1.blend'))
for mat in bpy.data.objects['Body'].data.materials:
    for node in mat.node_tree.nodes:
        if node.type != 'TEX_IMAGE' or not node.image:
            continue
        source = P/'textures'/Path(node.image.filepath).name
        if source.is_file():
            colorspace = node.image.colorspace_settings.name
            node.image = bpy.data.images.load(str(source), check_existing=False)
            node.image.colorspace_settings.name = colorspace
            node.image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_drg1.blend'))
