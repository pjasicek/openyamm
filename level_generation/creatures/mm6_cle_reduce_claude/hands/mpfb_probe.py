import addon_utils, bpy
addon_utils.enable("bl_ext.blender_org.mpfb", default_set=True)
from bl_ext.blender_org.mpfb.services.humanservice import HumanService
h = HumanService.create_human()
print('HUMAN', h.name, len(h.data.vertices), len(h.data.polygons))
rig = HumanService.add_builtin_rig(h, "default")
print('RIG', rig.name, len(rig.data.bones))
print('BONES', [b.name for b in rig.data.bones if 'hand' in b.name.lower() or 'finger' in b.name.lower() or 'wrist' in b.name.lower() or 'thumb' in b.name.lower() or 'metacarpal' in b.name.lower()][:60])
print('MODS', [(m.type, m.name) for m in h.modifiers])
print('MATS', [m.name for m in h.data.materials], 'UV', [u.name for u in h.data.uv_layers])
bpy.ops.wm.save_as_mainfile(filepath=bpy.path.abspath('//') or '/tmp/x.blend')
