"""Route B, step 2 (inside Blender): smooth a grafted arms mesh for first-person distance and give it even UVs.

    blender -b --factory-startup --python smooth_unwrap.py -- <grafted.glb> <out_dir> [--levels 1]

Imports the grafted GLB (graft_arms.py: our mesh bound to the first-person skeleton), subdivides the arm mesh once
(Catmull-Clark; vertex weights are interpolated), triangulates, unwraps it with uv_atlas (PartUV + sparrow, hands 1.4x
denser) and writes:
  out_dir/smoothed.glb  the skinned mesh and its armature, no clips (graft_arms.py then re-binds it by name);
  out_dir/upload.glb    the static mesh with the new UVs for a Meshy retexture (enable_original_uv: true).
"""
import os
import sys

import bpy

REPO = '/home/pjasicek/github/OpenYAMM'
sys.path.insert(0, os.path.join(REPO, 'level_generation/creatures/claude_shared'))
import uv_atlas  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:]
src, out = argv[0], argv[1]
levels = int(argv[argv.index('--levels') + 1]) if '--levels' in argv else 1
os.makedirs(out, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
arm.data.pose_position = 'REST'
if arm.animation_data:
    arm.animation_data.action = None
    for track in list(arm.animation_data.nla_tracks):
        arm.animation_data.nla_tracks.remove(track)
for o in list(bpy.data.objects):
    if o.type == 'MESH' and (o.data.name != 'Hand' or not o.vertex_groups):
        bpy.data.objects.remove(o, do_unlink=True)
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
bpy.context.view_layer.objects.active = mesh
mod = mesh.modifiers.new('sub', 'SUBSURF')
mod.levels = mod.render_levels = levels
mod.subdivision_type = 'CATMULL_CLARK'
mod.uv_smooth = 'PRESERVE_BOUNDARIES'
# The armature modifier must not deform while applying: move the subdivision first and apply it alone.
bpy.ops.object.modifier_move_to_index(modifier='sub', index=0)
bpy.ops.object.modifier_apply(modifier='sub')
tri = mesh.modifiers.new('tri', 'TRIANGULATE')
bpy.ops.object.modifier_move_to_index(modifier='tri', index=0)
bpy.ops.object.modifier_apply(modifier='tri')
print('faces after smoothing', len(mesh.data.polygons))
uv_from = argv[argv.index('--uv-from') + 1] if '--uv-from' in argv else None
if uv_from:
    # Same source topology smoothed the same way: copy an earlier unwrap loop by loop (its paint stays valid).
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=uv_from)
    donor = next(o for o in set(bpy.data.objects) - before if o.type == 'MESH')
    if len(donor.data.loops) != len(mesh.data.loops):
        raise SystemExit('topology differs from the UV donor')
    source = donor.data.uv_layers.active.data
    while len(mesh.data.uv_layers) > 1:
        mesh.data.uv_layers.remove(mesh.data.uv_layers[-1])
    target = mesh.data.uv_layers[0].data
    for i in range(len(target)):
        target[i].uv = source[i].uv
    keep_material = donor.data.materials[0]
    mesh.data.materials.clear()
    mesh.data.materials.append(keep_material)
    for o in set(bpy.data.objects) - before:
        bpy.data.objects.remove(o, do_unlink=True)
    print('UV copied from', uv_from)
else:
    hand_groups = tuple(g.name for g in mesh.vertex_groups if 'Hand' in g.name or 'Finger' in g.name)
    report = uv_atlas.unwrap(mesh, head_groups=hand_groups, head_factor=1.4, size=4096, margin_px=4)
    print('UNWRAP', {k: report.get(k) for k in ('charts_used', 'packer_used', 'fallbacks')})
bpy.ops.export_scene.gltf(filepath=os.path.join(out, 'smoothed.glb'), export_format='GLB', export_animations=False,
                          export_skins=True)
# Static upload: no armature, no groups.
bpy.data.objects.remove(arm, do_unlink=True)
mesh.vertex_groups.clear()
for m in list(mesh.modifiers):
    mesh.modifiers.remove(m)
bpy.ops.export_scene.gltf(filepath=os.path.join(out, 'upload.glb'), export_format='GLB', export_animations=False,
                          export_skins=False)
print('SMOOTH UNWRAP DONE')
