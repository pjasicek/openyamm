"""D4-only eye-height lever poses; retain the accepted 336-high post."""
import sys
from pathlib import Path
import bpy

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / 'hesper_stage'))
import blv_kit as kit
kit.FOLDERS += [kit.ART / 'textures_k5_grafted/masters']

b = kit.Builder('d04_cell_lever', {'body':'hkfloor','bone':'hobone'}, PROJECT / 'standins',
                decoration_ids={'unused':0})
for state in ('idle','pulled'):
    for obj in list(bpy.data.objects): bpy.data.objects.remove(obj, do_unlink=True)
    panels = kit.box((-60,-60,0),(60,60,336),'body',top='bone',bottom='body')
    end = (0,-144,192) if state=='idle' else (0,-208,128)
    panels += kit.beam((0,-64,208),end,24,'bone')
    panels += kit.box((end[0]-42,end[1]-16,end[2]-16),(end[0]+42,end[1]+16,end[2]+16),
                     'bone',top='bone',bottom='bone')
    obj = b.mesh('lever',panels,'decoration')
    obj.scale=(1.28,1.28,1.28)  # kit units /128 -> metres, 100 world units per metre
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True); bpy.context.view_layer.objects.active=obj
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.modifiers.new('Triangles','TRIANGULATE')
    bpy.ops.export_scene.gltf(filepath=str(PROJECT/'standins'/f'd04_cell_lever_{state}.glb'),
                              export_format='GLB',export_yup=True,export_apply=True)
