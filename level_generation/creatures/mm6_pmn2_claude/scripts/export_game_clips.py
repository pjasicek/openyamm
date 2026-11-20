"""Export work/rig_v7.blend (env EXPORT_BLEND) with the game clip set only, renamed: Idle_9 -> Standing, Walking, Running, Attack, Hit,
Death, Dead (mesh + staff + Meshy skeleton, no texture); quaternion keys are made sign-continuous first (solved
frames can flip q -> -q, which interpolates the long way round). Args: out.glb."""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
out = os.path.abspath(sys.argv[sys.argv.index('--') + 1])
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, os.environ.get('EXPORT_BLEND', 'rig_v7.blend')))
KEEP = {'Idle_9': 'Standing', 'Walking': 'Walking', 'Running': 'Running', 'Attack': 'Attack', 'Hit': 'Hit',
        'Death': 'Death', 'Dead': 'Dead'}
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        bpy.data.actions.remove(a)
import staff_rig as sr
for a in list(bpy.data.actions):
    print('QUAT_SIGN_FIX', a.name, sr.fix_quaternion_signs(a))
    a.name = KEEP[a.name]
for o in bpy.data.objects:
    o.select_set(o.name in ('Mage', 'Mage_Rig', 'Staff'))
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animation_mode='ACTIONS', export_materials='EXPORT')
print('EXPORT', out, sorted((a.name, tuple(a.frame_range)) for a in bpy.data.actions))
