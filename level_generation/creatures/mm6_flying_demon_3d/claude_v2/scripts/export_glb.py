"""Export the flying demon for the runtime. Args: tier (a|b|c). Joins body, horns and wings into one skinned mesh
(on a temporary copy; the blend is not saved), swaps the tier materials, downsizes body maps for the runtime
(colour/normal 2048, roughness 1024) and writes export/mm6_wdm_<tier>.glb. Tier a carries skin and all clips;
b and c carry only materials for merge_variants.py. Sockets (Socket_*) are exported as bone-parented nodes."""
import bpy, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
argv = sys.argv[sys.argv.index('--') + 1:]
tier = argv[0]
viewer = len(argv) > 1 and argv[1] == 'viewer'       # full skinned+animated tier GLB for the review viewer
rig = bpy.data.objects['Flying_Demon_Rig']
parts = [bpy.data.objects[n] for n in ('Flying_Demon_Body', 'Flying_Horn_Left', 'Flying_Horn_Right',
                                      'Flying_Wing_Left', 'Flying_Wing_Right')]
for o in parts:                                  # one shared UV layer name, or the join keeps two layers
    layers = o.data.uv_layers
    keep = layers.active
    for layer in [l for l in layers if l != keep]:
        layers.remove(layer)
    layers.active.name = 'UVMap'
    print('UV', o.name, [l.name for l in o.data.uv_layers])
for o in bpy.data.objects:
    o.select_set(o in parts)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
print('JOINED UV', [l.name for l in bpy.context.view_layer.objects.active.data.uv_layers])
mesh = bpy.context.view_layer.objects.active
mesh.name = 'Flying_Demon'
T = tier.upper()
for slot in mesh.material_slots:
    m = slot.material
    if m and m.name.startswith('Flying_A_'):
        slot.material = bpy.data.materials[m.name.replace('Flying_A_', f'Flying_{T}_')]
    if slot.material and slot.material.name.endswith('_Wing'):
        # the mesh follows the native outline; merged shadow LODs need opaque materials
        nt = slot.material.node_tree
        for link in [l for l in nt.links if l.to_socket.name == 'Alpha']:
            nt.links.remove(link)
done = set()
for slot in mesh.material_slots:
    m = slot.material
    if not (m and m.use_nodes):
        continue
    for n in m.node_tree.nodes:
        if n.type == 'TEX_IMAGE' and n.image and n.image.name not in done:
            size = 1024 if 'rough' in n.image.name.lower() else 2048
            if max(n.image.size) > size:
                n.image.scale(size, size)
            done.add(n.image.name)
for o in bpy.data.objects:
    o.select_set(o is mesh or o is rig or (o.type == 'EMPTY' and o.name.startswith('Socket_')))
bpy.context.view_layer.objects.active = rig
if tier == 'a' or viewer:
    rig.animation_data.action = bpy.data.actions['Flight']; bpy.context.scene.frame_set(0)
out = os.path.join(HERE, 'review', 'viewer', f'mm6_wdm_{tier}.glb') if viewer else \
    os.path.join(HERE, 'export', f'mm6_wdm_{tier}.glb')
full = tier == 'a' or viewer
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=full, export_animation_mode='ACTIONS',
                          export_force_sampling=True, export_frame_step=1, export_skins=full,
                          export_all_influences=True, export_attributes=False, export_morph=False,
                          export_image_format='AUTO', export_reset_pose_bones=True,
                          export_anim_slide_to_zero=True)
print('EXPORTED', out, [s.material.name for s in mesh.material_slots])
