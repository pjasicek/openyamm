import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/'meshy/body_rig_v1/result_basic_animations_walking_glb_url.glb'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
scene=bpy.context.scene;scene.render.fps=48
rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.name='Lizardman_Rig'
body=next(o for o in scene.objects if o.type=='MESH');body.name='Lizardman_Body'
strip=rig.animation_data.nla_tracks[0].strips[0]
action=strip.action;action.name='Meshy_Walk_Source'
slot=strip.action_slot
for track in rig.animation_data.nla_tracks:track.mute=True
rig.animation_data.action=action;rig.animation_data.action_slot=slot
report={'source':str(SOURCE),'rig_matrix':[list(r) for r in rig.matrix_world],'body_matrix':[list(r) for r in body.matrix_world],
        'bones':{b.name:{'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(r) for r in b.matrix_local]} for b in rig.data.bones},
        'groups':[g.name for g in body.vertex_groups],'vertices':len(body.data.vertices),'triangles':sum(len(p.vertices)-2 for p in body.data.polygons),'action_frames':list(action.frame_range),'probes':[]}
out=ROOT/'rig_review_v1';out.mkdir(exist_ok=True)
scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=500;scene.render.resolution_y=640
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.world=bpy.data.worlds.new('Review_World');scene.world.color=(.18,.18,.18)
scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.6,.6,.6)
scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
scene.display.shading.background_type='WORLD'
bpy.ops.object.camera_add();camera=bpy.context.object;camera.data.type='ORTHO';camera.data.ortho_scale=1.95;scene.camera=camera
for i,phase in enumerate([0,.125,.25,.375,.5,.625,.75,.875,1]):
    frame=action.frame_range[0]+phase*(action.frame_range[1]-action.frame_range[0]);scene.frame_set(int(frame),subframe=frame%1)
    deps=bpy.context.evaluated_depsgraph_get();evaluated=body.evaluated_get(deps);mesh=evaluated.to_mesh()
    pts=[evaluated.matrix_world@v.co for v in mesh.vertices]
    report['probes'].append({'phase':phase,'minimum_z':min(p.z for p in pts),'maximum_z':max(p.z for p in pts)})
    evaluated.to_mesh_clear()
    for view,direction in [('front',(0,-5,0)),('profile',(-5,0,0))]:
        center=Vector((0,0,.85));camera.location=center+Vector(direction);camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(out/f'walk_{view}_{i:02d}.png');bpy.ops.render.render(write_still=True)
rig.animation_data.action=None
for bone in rig.pose.bones:bone.matrix_basis=Matrix.Identity(4)
scene.frame_set(0)
report['rest_bounds']=[[min((body.matrix_world@v.co)[i] for v in body.data.vertices) for i in range(3)],[max((body.matrix_world@v.co)[i] for v in body.data.vertices) for i in range(3)]]
(out/'inspection.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'rig_v1.blend'))
print(json.dumps({k:v for k,v in report.items() if k not in ('bones','groups')}),flush=True)
