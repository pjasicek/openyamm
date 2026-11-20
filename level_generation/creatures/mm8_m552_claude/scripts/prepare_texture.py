"""Reduce rigid feather surfaces, check every action, unwrap and export a neutral texture input."""
import json
import sys
from pathlib import Path
import bpy
import numpy as np

P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'))
mesh = bpy.data.objects['Thunderbird']
rig = bpy.data.objects['Thunderbird_Rig']
rig.animation_data.action = None
for bone in rig.pose.bones:
    bone.matrix_basis.identity()
bpy.context.view_layer.objects.active = mesh
for obj in bpy.context.scene.objects:
    obj.select_set(obj == mesh)
labels = mesh.data.attributes['anatomy_part']
# Simplify body and wing coverts after weighting; preserve head, talons and the thin flight feathers.
for vertex in mesh.data.vertices:
    part=labels.data[vertex.index].value
    vertex.select = part in (1,2) or (part==0 and vertex.co.y>-.12 and not (vertex.co.y>.06 and vertex.co.z<.06))
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.decimate(ratio=.72)
bpy.ops.object.mode_set(mode='OBJECT')
mesh.data.calc_loop_triangles()
assert len(mesh.data.loop_triangles) <= 15000, len(mesh.data.loop_triangles)
for vertex in mesh.data.vertices:
    assert 0 < len(vertex.groups) <= 4
    assert abs(sum(g.weight for g in vertex.groups)-1) < .001

scene = bpy.context.scene
depsgraph = bpy.context.evaluated_depsgraph_get()
report = {'triangles':len(mesh.data.loop_triangles), 'vertices':len(mesh.data.vertices), 'clips':{}}
death = None
for name, spec in json.loads((P/'work/clip_manifest.json').read_text()).items():
    rig.animation_data.action = bpy.data.actions[name]
    samples = []
    for frame in np.arange(0, spec['frames']+.01, .5):
        scene.frame_set(int(frame), subframe=float(frame%1))
        co = np.array([tuple(v.co) for v in mesh.evaluated_get(depsgraph).data.vertices])
        assert np.isfinite(co).all(), (name, frame)
        samples.append(co)
    samples = np.array(samples)
    seam = float(np.max(np.linalg.norm(samples[0]-samples[-1], axis=1)))
    if spec['loop']:
        assert seam < 1e-5, (name, seam)
    floor = float(samples[:,:,2].min())
    if name in ('Death','Dead'):assert floor > -.005, (name, floor)
    report['clips'][name] = {'floor_min':floor, 'endpoint_delta':seam,
        'half_frame_max_vertex_travel':float(np.linalg.norm(np.diff(samples,axis=0),axis=2).max())}
    if name == 'Death':
        death = samples[-1]
    if name == 'Dead':
        report['death_dead_delta'] = float(np.abs(death-samples[0]).max())
        assert report['death_dead_delta'] < .001
rig.animation_data.action = None
for bone in rig.pose.bones:
    bone.matrix_basis.identity()
bpy.context.view_layer.update()
for uv in list(mesh.data.uv_layers):
    mesh.data.uv_layers.remove(uv)
mesh.data.uv_layers.new(name='UVMap')
sys.path.insert(0, str(P.parent/'claude_shared'))
from uv_head_density import scale_head_islands
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=.004, area_weight=0., scale_to_bounds=False)
scale_head_islands(mesh, ('Head','Neck'), factor=2.5)
bpy.ops.uv.pack_islands(margin=.004, rotate=True)
bpy.ops.object.mode_set(mode='OBJECT')
uv = np.array([tuple(d.uv) for d in mesh.data.uv_layers.active.data])
assert np.isfinite(uv).all() and uv.min() >= -1e-5 and uv.max() <= 1.00001
(P/'review/viewer').mkdir(parents=True,exist_ok=True)
(P/'texturing').mkdir(exist_ok=True)
(P/'review/deformation_audit.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/uv_master.blend'))
for obj in scene.objects:
    obj.select_set(obj in (mesh,rig))
bpy.ops.export_scene.gltf(filepath=str(P/'review/viewer/pilot.glb'),use_selection=True,
    export_format='GLB',export_yup=True,export_skins=True,export_animations=True,
    export_animation_mode='ACTIONS',export_frame_range=False,export_materials='NONE')
dup = mesh.copy()
dup.data = mesh.data.copy()
dup.modifiers.clear()
dup.parent = None
scene.collection.objects.link(dup)
for obj in scene.objects:
    obj.select_set(obj == dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=str(P/'texturing/thunderbird_neutral.glb'),use_selection=True,
    export_format='GLB', export_yup=True,export_skins=False,export_animations=False,export_materials='NONE')
print('AUDIT',json.dumps(report))
