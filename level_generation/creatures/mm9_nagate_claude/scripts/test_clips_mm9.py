"""Clip pipeline check on the ORIGINAL MM9 mesh: build the role clips, drop the MM9 clips and the two dummy pieces,
export work/mm9_roles_test.glb and print a JSON report (seams before/after, join jumps, durations).

Args: <mm9 tier glb> <out glb> <report json>
"""
import bpy, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clips_mm9 as C

argv = sys.argv[sys.argv.index('--') + 1:]
src, out, rep = argv
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
fps_import = sc.render.fps / sc.render.fps_base
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
originals = list(bpy.data.actions)
report = C.build_role_clips(arm, fps_import)
for a in originals:
    bpy.data.actions.remove(a)
sc.render.fps = C.FPS
for act in bpy.data.actions:
    if report['clips'].get(act.name, {}).get('loop'):
        report['clips'][act.name]['seam_after_deg'] = round(C.seam_after(arm, act, C.FPS), 3)
for o in list(sc.objects):
    if o.type == 'MESH' and (o.name.startswith(('tailnode', 'headnode', 'Icosphere'))):
        bpy.data.objects.remove(o)
arm.animation_data.action = bpy.data.actions['Standing']
for o in bpy.data.objects:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
json.dump(report, open(rep, 'w'), indent=1)
print('REPORT', json.dumps(report))
