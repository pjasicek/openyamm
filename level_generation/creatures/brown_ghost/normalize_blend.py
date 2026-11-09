"""Normalize an isolated library save into a normal Blender project, and check contents."""
import bpy
import json
from pathlib import Path
from mathutils import Quaternion, Vector
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/brown_ghost')
scene=bpy.data.scenes['Brown ghost sprite studio']
assert len(bpy.data.scenes)==1
bpy.context.window.scene=scene
rig=scene.objects['Ghost RIG'];obj=next(o for o in scene.objects if o.type=='MESH')
scene.frame_set(1)
for o in scene.objects:o.select_set(False)
rig.select_set(True);obj.select_set(True);bpy.context.view_layer.objects.active=rig
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active
            space.shading.type='MATERIAL'
            space.region_3d.view_perspective='PERSP'
            space.region_3d.view_location=(0,0,1.35)
            space.region_3d.view_distance=4.7
            space.region_3d.view_rotation=Quaternion((0.831,0.523,0.103,0.164)).normalized()
            space.clip_end=100
assert len(rig.data.bones)==32
assert len(obj.data.shape_keys.key_blocks)==1+len(json.loads((ROOT/'poses.json').read_text()))
assert len(rig.animation_data.nla_tracks)==7
assert len(obj.data.shape_keys.animation_data.nla_tracks)==7
assert all(v.groups for v in obj.data.vertices)
assert all(abs(sum(g.weight for g in v.groups)-1)<1e-5 for v in obj.data.vertices)
atlases={n.image for mat in obj.data.materials for n in mat.node_tree.nodes if n.name=='Portable albedo atlas'}
assert atlases and all(image.packed_file for image in atlases)
scene['model_units']='Blender units; roughly human sized. Choose game-world scale during integration.'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'brown_ghost.blend'),compress=True)
(ROOT/'review'/'blend_validation.json').write_text(json.dumps({'scenes':[s.name for s in bpy.data.scenes],
'bones':len(rig.data.bones),'weighted_vertices':len(obj.data.vertices),'weight_sums':'PASS',
'named_bone_clips':len(rig.animation_data.nla_tracks),'named_cloth_clips':len(obj.data.shape_keys.animation_data.nla_tracks),
'packed_albedo':all(bool(image.packed_file) for image in atlases)},indent=2)+'\n')
