"""Review-viewer GLB per tier (three.js has no region ramps or attachments): the tier's ramps baked into the base
colour (work/tier_<v>.png from tier_bake.py), only that tier's gear kept (B the twin emitter, C the shield ring).
Args: -- <variant hdr_a|hdr_b|hdr_c>; writes review/viewer/hes_drone_<a|b|c>.glb (review copy, not a runtime file)."""
import bpy, bmesh, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
v = sys.argv[sys.argv.index('--') + 1]
sys.argv = [sys.argv[0]]
exec(open(os.path.join(HERE, 'scripts', 'export.py')).read().split("rig.animation_data.action = bpy.data.actions['Standing']")[0])
img = bpy.data.images.load(os.path.join(HERE, 'work', f'tier_{v}.png'))
for m in (casing, glow):
    n = next(n for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image.name.startswith('hdr_basecolor'))
    n.image = img
keep = {'hdr_a': set(), 'hdr_b': {'GearEmitter', 'GearEmitterGlow'}, 'hdr_c': {'GearRing', 'GearRingGlow'}}[v]
gear = {'GearEmitter', 'GearEmitterGlow', 'GearRing', 'GearRingGlow'}
gi = {g.index: g.name for g in mesh.vertex_groups}
bm = bmesh.new(); bm.from_mesh(mesh.data); dl = bm.verts.layers.deform.active
drop = [x for x in bm.verts if any(gi[k] in gear - keep and w > 0.5 for k, w in x[dl].items())]
bmesh.ops.delete(bm, geom=drop, context='VERTS'); bm.to_mesh(mesh.data); bm.free()
rig.animation_data.action = bpy.data.actions['Standing']; bpy.context.scene.frame_set(1)
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig, thr))
bpy.context.view_layer.objects.active = rig
out = os.path.join(HERE, 'review', 'viewer', f'hes_drone_{v[-1]}.glb')
os.makedirs(os.path.dirname(out), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
print('VIEWERGLB', out, 'dropped', len(drop))
