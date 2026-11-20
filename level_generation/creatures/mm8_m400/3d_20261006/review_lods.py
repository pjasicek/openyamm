import bpy,sys,json,copy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT.parents[3]/'tools'))
from build_actor_lods import read_glb,write_glb
source=ROOT/'delivery/mm8_lizardman_villager_a.glb';doc,binary=read_glb(source)
review=ROOT/'lod_review';review.mkdir(exist_ok=True)
levels=[0]+doc['meshes'][0]['extras']['openyamm_lods']
for level,index in enumerate(levels):
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'delivery/mm8_lizardman_villager_a.blend'))
    for o in list(bpy.data.objects):
        if o.type in ('MESH','ARMATURE'):bpy.data.objects.remove(o,do_unlink=True)
    temp=review/f'level{level}.glb';changed=copy.deepcopy(doc)
    next(n for n in changed['nodes'] if n.get('name')=='Lizardman_Body')['mesh']=index
    write_glb(temp,changed,binary);bpy.ops.import_scene.gltf(filepath=str(temp));temp.unlink()
    body=next(o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    action=next(s.action for t in rig.animation_data.nla_tracks for s in t.strips if s.action.name.startswith('Standing'))
    rig.animation_data.action=action;rig.animation_data.action_slot=next(s.action_slot for t in rig.animation_data.nla_tracks for s in t.strips if s.action==action)
    for t in rig.animation_data.nla_tracks:t.mute=True
    scene=bpy.context.scene;scene.frame_set(0);scene.render.resolution_x=720;scene.render.resolution_y=720;camera=scene.camera;camera.data.ortho_scale=2.15
    for view,direction in [('front',(0,-5,0)),('profile',(-5,0,0)),('rear',(-3.5,3.5,0))]:
        center=Vector((0,.1,.83));camera.location=center+Vector(direction);camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(review/f'LOD{level}_{view}.png');bpy.ops.render.render(write_still=True)
print('All four LODs rendered in isolated imports',flush=True)
