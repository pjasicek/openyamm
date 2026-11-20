"""Preview export of a rig blend (default work/rig_v1.blend): mesh (+ staff when present) + Meshy skeleton + corrected
clips, no '_src' copies, no texture. Args: [blend out.glb]."""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args[0]) if args else os.path.join(common.WORK, 'rig_v1.blend'))
for a in list(bpy.data.actions):
    if a.name.endswith('_src'):
        bpy.data.actions.remove(a)
arm = bpy.data.objects['Mage_Rig']
for o in bpy.data.objects:
    o.select_set(o.name in ('Mage', 'Mage_Rig', 'Staff'))
out = os.path.abspath(args[1]) if len(args) > 1 else os.path.join(common.PROJECT, 'export', 'pmn2_rig_v1_preview.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animation_mode='ACTIONS', export_materials='NONE')
print('EXPORT', out, sorted(a.name for a in bpy.data.actions))
