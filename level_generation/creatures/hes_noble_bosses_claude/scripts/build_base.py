"""Base scene for the Noble bosses from the published winged Kreegan body (hes_overseer_codex, copied to source/).

Keeps the LOD0 body mesh (renamed Body), its rig, materials, UVs and skin; drops the far LODs, the shadow meshes and
the Overseer equipment joints (no weights); keeps the seven Overseer clips as source actions renamed Src_<role>.
Saves work/base.blend. Usage (Blender): build_base.py"""
import bpy, json
from pathlib import Path

P = Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P / 'source/hes_kreegan_winged.glb'))
sc = bpy.context.scene
rig = bpy.data.objects['Rig']
body = bpy.data.objects['OV_Assembled']
body.name = 'Body'; body.data.name = 'Body'
for o in list(sc.objects):
    if o.type == 'MESH' and o != body:
        bpy.data.objects.remove(o, do_unlink=True)
equipment = ['PulsePistol', 'Socket_Muzzle', 'ArcMaul', 'Socket_Maul', 'CollarRod', 'Socket_Rod', 'CollarKey',
             'HipSaber', 'HolsterPistol']
weighted = {g.name for g in body.vertex_groups}
assert not [b for b in equipment if b in weighted and any(
    g.group == body.vertex_groups[b].index and g.weight > 0 for v in body.data.vertices for g in v.groups)]
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for name in equipment:
    eb = rig.data.edit_bones.get(name)
    if eb:
        rig.data.edit_bones.remove(eb)
bpy.ops.object.mode_set(mode='OBJECT')
for name in equipment:
    g = body.vertex_groups.get(name)
    if g:
        body.vertex_groups.remove(g)
for a, old in [(a, a.name) for a in bpy.data.actions]:
    a.name = 'Src_' + old.replace('Overseer_', '')
    a.use_fake_user = True
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
info = {'bones': len(rig.data.bones), 'actions': sorted(a.name for a in bpy.data.actions),
        'body_tris': sum(len(p.vertices) - 2 for p in body.data.polygons),
        'materials': [m.name for m in body.data.materials]}
(P / 'work/base_info.json').write_text(json.dumps(info, indent=1))
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/base.blend'))
print('BASE', info)
