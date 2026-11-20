import bpy,sys,json,hashlib,shutil,math
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[3]
sys.path.insert(0,str(REPO/'tools'))
from build_actor_lods import generate,read_glb,accessor_bytes
from test_build_actor_lod_seams import main as check_seams
check_seams()
delivery=ROOT/'delivery';runtime=delivery/'mm8_lizardman_villager_a.glb';lod0=delivery/'mm8_lizardman_villager_a_lod0.glb'
import subprocess
subprocess.run(['/usr/bin/python3',str(REPO/'tools/prepare_actor_glb.py'),str(ROOT/'textured_export_v1.glb'),str(lod0)],check=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(lod0,runtime,'Lizardman_Body',ratios=(.75,.6,.5))
before,payload=read_glb(lod0);after,binary=read_glb(runtime)
assert before['animations']==after['animations'] and before['skins']==after['skins']
for i,a in enumerate(before['accessors']):
    assert accessor_bytes(before,payload,i)==accessor_bytes(after,binary,i),'LOD changed level-zero or motion accessor'
levels=[0]+after['meshes'][0]['extras']['openyamm_lods']
counts=[sum(after['accessors'][p['indices']]['count']//3 for p in after['meshes'][i]['primitives']) for i in levels]
assert counts[0]==15287 and all(a>b>0 for a,b in zip(counts,counts[1:]))

bpy.ops.wm.open_mainfile(filepath=str(delivery/'mm8_lizardman_villager_a.blend'))
reference_body=bpy.data.objects['Lizardman_Body'];reference_rig=bpy.data.objects['Lizardman_Rig'];scene=bpy.context.scene
previous=set(bpy.data.objects);old_actions=set(bpy.data.actions)
bpy.ops.import_scene.gltf(filepath=str(runtime))
imported=[o for o in bpy.data.objects if o not in previous]
body=next(o for o in imported if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers));rig=next(o for o in imported if o.type=='ARMATURE')
actions=[a for a in bpy.data.actions if a not in old_actions]
def action_for(name):return next(a for a in actions if a.name==name or a.name.startswith(name+'.'))
def activate(obj,action):
    obj.animation_data.action=action
    obj.animation_data.action_slot=next(s.action_slot for t in obj.animation_data.nla_tracks for s in t.strips if s.action==action)
    for t in obj.animation_data.nla_tracks:t.mute=True
def points(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();out=[ev.matrix_world@v.co for v in mesh.vertices];ev.to_mesh_clear();return out
ends={'Standing':6,'Walk':42,'Fidget':24,'Hit':24,'Death':36,'Corpse':6}
report={};review=ROOT/'reimport_review';review.mkdir(exist_ok=True)
reference_body.hide_render=True
for name,end in ends.items():
    activate(reference_rig,bpy.data.actions[name]);activate(rig,action_for(name));errors=[]
    frames=[0,end/2,end] if name in ('Standing','Corpse') else [i/2 for i in range(end*2+1)]
    for f in frames:
        scene.frame_set(int(f),subframe=f%1);source=points(reference_body);target=points(body)
        tree=KDTree(len(source))
        for i,p in enumerate(source):tree.insert(p,i)
        tree.balance();error=max(tree.find(p)[2] for p in target)
        assert error<.0001,(name,f,error)
        assert min(p.z for p in target)>-.006,(name,f,'ground penetration')
        errors.append({'frame':f,'max_surface_error_m':error})
    report[name]=errors
    scene.frame_set(end//2);camera=scene.camera;camera.data.ortho_scale=2.15
    center=Vector((0,.23,.83));camera.location=center+Vector((-3,-5,0));camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(review/f'{name}_exported.png');bpy.ops.render.render(write_still=True)
(ROOT/'export_validation.json').write_text(json.dumps({'status':'pass','master_surface_parity':report,'lod_triangles':counts,'level_zero_accessors_and_animation_unchanged':True,'skin_joints':40,'clips':{name:end/48 for name,end in ends.items()},'images_all_png':all(i['mimeType']=='image/png' for i in after['images']),'runtime_sha256':hashlib.sha256(runtime.read_bytes()).hexdigest()},indent=2))
assert all(i['mimeType']=='image/png' for i in after['images'])
print('Actual export reimport surface parity, all clips and unchanged LOD0 pass:',counts,flush=True)
