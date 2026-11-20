"""Check the saved UV master against revision 7, then inspect the actual static GLB."""
import hashlib
import json
import numpy as np
from pathlib import Path

import bpy
from mathutils import Vector

stage = Path(__file__).resolve().parent
baseline_path = stage.parent/'animations_native_v7_20261005'
bpy.ops.wm.open_mainfile(filepath=str(stage/'mm6_demon_uv_master.blend'))
source = bpy.data.scenes['MM6_Demon_Native_Animations']
mesh,rig = source.objects['Demon_Native_Mesh'],source.objects['Demon_Native_Rig']
with bpy.data.libraries.load(str(baseline_path/'mm6_demon_native_animations.blend')) as (available,loaded):
    loaded.scenes = ['MM6_Demon_Native_Animations']
baseline = loaded.scenes[0]
old_mesh = next(o for o in baseline.objects if o.name.startswith('Demon_Native_Mesh'))
old_rig = next(o for o in baseline.objects if o.type=='ARMATURE')


def vertices(obj):
    return np.array([v.co for v in obj.data.vertices])


def curves(action):
    return {(c.data_path,c.array_index):[(tuple(k.co),k.interpolation) for k in c.keyframe_points]
            for c in action.layers[0].strips[0].channelbag(action.slots[0]).fcurves}


def select(scene,clip,frame):
    bpy.context.window.scene = scene
    for obj in scene.objects:
        if obj.type=='ARMATURE':
            obj.hide_set(False)
        for owner in (obj,obj.data.shape_keys if obj.type=='MESH' else None):
            if owner is not None and owner.animation_data:
                matching = [t.strips[0] for t in owner.animation_data.nla_tracks if t.name==clip]
                for track in owner.animation_data.nla_tracks:
                    track.mute = True
                owner.animation_data.action = matching[0].action if matching else None
                if matching:
                    owner.animation_data.action_slot = matching[0].action_slot
    scene.frame_set(frame)
    bpy.context.view_layer.update()


def evaluated(scene,obj):
    bpy.context.window.scene = scene
    result = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    temporary = result.to_mesh()
    points = np.array([v.co for v in temporary.vertices])
    matrix = np.array(result.matrix_world)
    result.to_mesh_clear()
    return points @ matrix[:3,:3].T + matrix[:3,3]


assert np.array_equal(vertices(mesh),vertices(old_mesh))
faces = np.array([tuple(p.vertices) for p in mesh.data.polygons])
assert np.array_equal(faces,np.array([tuple(p.vertices) for p in old_mesh.data.polygons]))
assert [g.name for g in mesh.vertex_groups] == [g.name for g in old_mesh.vertex_groups]
for a,b in zip(mesh.data.vertices,old_mesh.data.vertices):
    assert [(g.group,g.weight) for g in a.groups] == [(g.group,g.weight) for g in b.groups]
normal_error = float(np.abs(np.array([n.vector for n in mesh.data.corner_normals])-
                           np.array([n.vector for n in old_mesh.data.corner_normals])).max())
assert normal_error < 1e-6, normal_error
for bone in rig.data.bones:
    assert np.array_equal(np.array(bone.matrix_local),np.array(old_rig.data.bones[bone.name].matrix_local))
clips = {t.name:t.strips[0] for t in rig.animation_data.nla_tracks}
old_clips = {t.name:t.strips[0] for t in old_rig.animation_data.nla_tracks}
assert len(clips)==9 and clips.keys()==old_clips.keys()
for clip in clips:
    assert curves(clips[clip].action)==curves(old_clips[clip].action),clip
    assert clips[clip].frame_start==old_clips[clip].frame_start
    assert clips[clip].frame_end==old_clips[clip].frame_end
pose_errors = {}
for clip,frame in [('Standing',0),('Walk_Native',15),('Attack',12),('Hit',18),('Fidget',18),
                   ('Walking',25),('Running',16),('Death',12),('Ash_Remains',0)]:
    select(source,clip,frame)
    expected = evaluated(source,mesh)
    select(baseline,clip,frame)
    actual = evaluated(baseline,old_mesh)
    error = float(np.abs(expected-actual).max())
    assert error < 1e-7,(clip,error)
    pose_errors[clip] = error
uv = np.array([loop.uv for loop in mesh.data.uv_layers['Meshy_Atlas'].data])
tri_uv = uv.reshape(-1,3,2)
a,b = tri_uv[:,1]-tri_uv[:,0],tri_uv[:,2]-tri_uv[:,0]
area = np.abs(a[:,0]*b[:,1]-a[:,1]*b[:,0])/2
assert np.isfinite(uv).all() and uv.min()>=0 and uv.max()<=1
assert area.min()>1e-12
assert json.loads((stage/'uv_regions.json').read_text())['uv_overlap_selected_corners']==0

target = bpy.data.scenes.new('Actual_Meshy_Upload_Check')
bpy.context.window.scene = target
bpy.ops.import_scene.gltf(filepath=str(stage/'mm6_demon_meshy_upload.glb'))
assert len(target.objects)==1 and next(iter(target.objects)).type=='MESH'
static = next(iter(target.objects))
assert not static.modifiers and not static.animation_data and not static.data.shape_keys
assert len(static.data.polygons)==16474
assert len(static.data.uv_layers)==1


def canonical(points,indices,coords):
    rows = np.concatenate([points[indices],coords.reshape(-1,3,2)],axis=2)
    order = np.lexsort(rows.transpose(2,0,1)[::-1],axis=1)
    rows = np.take_along_axis(rows,order[:,:,None],axis=1).reshape(-1,15)
    return rows[np.lexsort(rows.T[::-1])]


imported_faces = np.array([tuple(p.vertices) for p in static.data.polygons])
imported_uv = np.array([loop.uv for loop in static.data.uv_layers[0].data])
assert np.allclose(canonical(vertices(mesh),faces,uv),
                   canonical(vertices(static),imported_faces,imported_uv),atol=1e-6,rtol=0), 'Exported per-corner UV/geometry correspondence'
report = dict(passed=True,vertices=8323,triangles=16474,joints=85,all_nine_animation_curves_identical=True,
              geometry_weights_bind_identical=True,maximum_normal_error=normal_error,
              sampled_pose_errors=pose_errors,uv_layers=1,uv_bounds=[uv.min(0).tolist(),uv.max(0).tolist()],
              minimum_uv_triangle_area=float(area.min()),uv_occupied_area=float(area.sum()),
              uv_overlap_selected_corners=0,actual_glb_reimport=True,exported_triangle_uv_mapping_identical=True,
              static_objects=1,static_armatures=0,static_animations=0,static_effect_meshes=0,
              baseline_hashes={n:hashlib.sha256((baseline_path/n).read_bytes()).hexdigest()
                               for n in ('mm6_demon_native_animations.blend','mm6_demon_native_animations.glb')})
(stage/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('UV master and static GLB checks passed.',flush=True)

target.world = source.world
target.render.engine = 'BLENDER_WORKBENCH'
target.render.resolution_x,target.render.resolution_y = 1000,1100
target.render.resolution_percentage = 100
target.render.image_settings.file_format = 'PNG'
target.view_settings.view_transform = source.view_settings.view_transform
shading = target.display.shading
shading.light = 'STUDIO'
shading.show_shadows = False
shading.show_cavity = True
shading.cavity_type = 'BOTH'
shading.background_type = 'WORLD'
camera = bpy.data.objects.new('UV_Review_Camera',bpy.data.cameras.new('UV_Review_Camera'))
target.collection.objects.link(camera)
target.camera = camera
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 2.1
output = stage/'review_frames'
output.mkdir(exist_ok=True)


def render(scene,name,center,direction,scale=2.1):
    bpy.context.window.scene = scene
    scene.camera = camera
    if camera.name not in scene.objects:
        scene.collection.objects.link(camera)
    center,direction = Vector(center),Vector(direction)
    camera.location = center+direction
    camera.rotation_euler = (-direction).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale = scale
    scene.render.filepath = str(output/(name+'.png'))
    bpy.ops.render.render(write_still=True)


views = [('front',(0,-6,0)),('profile',(-6,0,0)),('oblique',(-3,-6,.2)),('back',(0,6,0))]
shading.color_type = 'MATERIAL'
for view,direction in views:
    render(target,'upload_'+view,(0,0,.85),direction)
checker = bpy.data.images.load(str(stage/'uv_checker.png'),check_existing=True)
for slot in static.material_slots:
    mat = slot.material.copy()
    mat.use_nodes = True
    tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = checker
    mat.node_tree.nodes.active = tex
    bsdf = next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
    slot.material = mat
shading.color_type = 'TEXTURE'
for view,direction in views:
    render(target,'checker_'+view,(0,0,.85),direction)
transfer = np.load(stage/'uv_transfer.npz')
for region in ('head','right_hand','left_hand','skull_clasp'):
    points = vertices(mesh)[faces[transfer['face_regions']==region]].reshape(-1,3)
    lo,hi = points.min(0),points.max(0)
    scale = max((hi[0]-lo[0])*1.1,hi[2]-lo[2])*1.2
    render(target,'checker_'+region,(lo+hi)/2,(0,-6,0),scale)
print('Rendered actual GLB upload and UV checker views.',flush=True)
