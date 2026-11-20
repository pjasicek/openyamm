import bpy,sys,json,math
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];D=P/'delivery';sc=bpy.context.scene
bpy.ops.wm.open_mainfile(filepath=str(D/'mm8_lizardman_peasant.blend'))
source_body=bpy.data.objects['Lizardman_Body'];source_rig=bpy.data.objects['Lizardman_Rig'];sc=bpy.context.scene
old=set(bpy.data.objects);old_actions=set(bpy.data.actions)
bpy.ops.import_scene.gltf(filepath=str(D/'mm8_lizardman_peasant.glb'))
new=[o for o in bpy.data.objects if o not in old]
body=next(o for o in new if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers));rig=next(o for o in new if o.type=='ARMATURE')
actions=[a for a in bpy.data.actions if a not in old_actions]
for r in [rig,source_rig]:
    for t in r.animation_data.nla_tracks:t.mute=True

def activate(rig,action):
    rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]

def points(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    xyz=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();return xyz
report={};endpoints={}
for name in ['Standing','Walk','Hit','Fidget','Death','Corpse']:
    src=bpy.data.actions[name];dst=next(a for a in actions if a.name.split('.')[0]==name)
    activate(source_rig,src);activate(rig,dst);end=src.frame_range[1];worst=0;minimum=10
    for f in np.linspace(0,end,97):
        sc.frame_set(int(f),subframe=float(f%1));reference=points(source_body);actual=points(body)
        tree=KDTree(len(reference))
        for i,v in enumerate(reference):tree.insert(v,i)
        tree.balance();error=max(tree.find(v)[2] for v in actual);worst=max(worst,error)
        minimum=min(minimum,min(v.z for v in actual))
        assert all(math.isfinite(c) for v in actual for c in v)
    report[name]={'surface_parity_max_m':worst,'min_z_m':minimum,'samples':97}
    assert worst<.008,(name,'export surface differs',worst)
    assert minimum>-.012,(name,'floor penetration',minimum)
    endpoints[name]=[]
    for f in [0,end]:
        sc.frame_set(int(f),subframe=float(f%1));endpoints[name].append(np.array([v[:] for v in points(body)]))
    print('VERIFIED',name,report[name],flush=True)
for name in ['Hit','Fidget']:
    for endpoint in endpoints[name]:assert np.max(np.linalg.norm(endpoint-endpoints['Standing'][0],axis=1))<.0001,name
assert np.max(np.linalg.norm(endpoints['Death'][1]-endpoints['Corpse'][0],axis=1))<.0001
assert np.max(np.linalg.norm(endpoints['Walk'][0]-endpoints['Walk'][1],axis=1))<.0001
(P/'review/export_validation.json').write_text(json.dumps(report,indent=2)+'\n')
source_body.hide_render=True;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=720;sc.render.resolution_y=720
for name,phase in [('Standing',0),('Walk',.5),('Hit',.5),('Fidget',.5),('Death',.5),('Corpse',0)]:
    a=next(a for a in actions if a.name.split('.')[0]==name);activate(rig,a);f=a.frame_range[1]*phase;sc.frame_set(int(f),subframe=float(f%1))
    for view,direction in [('front',(0,-5,0)),('quarter',(-3,-5,0)),('side',(-5,0,0))]:
        target=Vector((0,.2,.85));sc.camera.location=target+Vector(direction);sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=2.25
        sc.render.filepath=str(P/f'review/final_{name}_{view}.png');bpy.ops.render.render(write_still=True)
a=next(a for a in actions if a.name.split('.')[0]=='Standing');activate(rig,a);sc.frame_set(0)
for name,target,scale in [('head',(0,-.07,1.48),.65),('hands',(0,-.1,.98),1.1),('feet',(0,0,.2),.7)]:
    target=Vector(target);sc.camera.location=target+Vector((-2,-5,0));sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=scale
    sc.render.filepath=str(P/f'review/final_detail_{name}.png');bpy.ops.render.render(write_still=True)
