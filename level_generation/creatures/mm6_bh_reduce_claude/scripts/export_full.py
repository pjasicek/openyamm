"""Pre-cut eye mesh (../mm6_bh_claude/work/anim_v1_full.blend, 15,823 tris, the UVs the texture was composed on) +
rig -> work/full_export.glb: skinned geometry only, material named like the installed one (Eye_A) for swap_lod0.py.
Usage: blender -b ../mm6_bh_claude/work/anim_v1_full.blend -P scripts/export_full.py"""
import os, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mesh = bpy.data.objects['Eye']; rig = bpy.data.objects['Eye_Rig']
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
mesh.data.materials.clear(); mesh.data.materials.append(bpy.data.materials.new('Eye_A'))
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work', 'full_export.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='NONE')
print('EXPORTED', sum(len(p.vertices) - 2 for p in mesh.data.polygons))
