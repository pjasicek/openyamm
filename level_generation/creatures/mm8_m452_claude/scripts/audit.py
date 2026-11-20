"""Check final GLB skinning, half-frame ground contact, loop seams and editable-master parity."""
from pathlib import Path
import bpy,json,math,hashlib
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];FPS=24
meta=json.loads((P/'work/anim_info.json').read_text())['clips']
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rat_final.blend'))
rig=bpy.data.objects['Rat_Rig'];body=bpy.data.objects['Rat'];scene=bpy.context.scene

def coordinates(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    points=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();return points
reference={}
for clip,info in meta.items():
    rig.animation_data.action=bpy.data.actions[clip];reference[clip]=[]
    for t in [0,info['seconds']*.25,info['seconds']*.5,info['seconds']*.75,info['seconds']]:
        f=1+t*FPS;scene.frame_set(math.floor(f),subframe=f%1);reference[clip].append((t,coordinates(body)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_m452.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=bpy.data.objects['Rat'];scene=bpy.context.scene;scene.render.fps=FPS
names={g.index:g.name for g in body.vertex_groups};owners=[]
for v in body.data.vertices:
    used=[g for g in v.groups if g.weight>1e-6]
    assert 0<len(used)<=4 and abs(sum(g.weight for g in used)-1)<1e-4
    owners.append(names[max(used,key=lambda g:g.weight).group])
actions={a.name:a for a in bpy.data.actions};report={};endposes={}
for clip,info in meta.items():
    action=actions.get(clip) or next(a for a in actions.values() if a.name.endswith('|'+clip))
    rig.animation_data.action=action
    if action.slots:rig.animation_data.action_slot=action.slots[0]
    error=0;minimum=100;feet=[]
    for t,expected in reference[clip]:
        f=t*FPS;scene.frame_set(math.floor(f),subframe=f%1);actual=coordinates(body)
        tree=KDTree(len(expected))
        for i,point in enumerate(expected):tree.insert(point,i)
        tree.balance();error=max(error,max(tree.find(point)[2] for point in actual))
    for sample in range(round(info['seconds']*FPS*2)+1):
        scene.frame_set(sample//2,subframe=(sample%2)/2);points=coordinates(body)
        assert all(math.isfinite(c) for point in points for c in point)
        minimum=min(minimum,min(point.z for point in points))
        feet.append({name:min(points[i].z for i,owner in enumerate(owners) if owner==name)
                     for name in ['FrontPaw_L','FrontPaw_R','HindPaw_L','HindPaw_R']})
    assert error<.0001,(clip,'export parity',error)
    assert minimum>-.015,(clip,'floor',minimum)
    scene.frame_set(0);first=coordinates(body)
    scene.frame_set(round(info['seconds']*FPS));last=coordinates(body);endposes[clip]=(first,last)
    gap=max((a-b).length for a,b in zip(first,last))
    if info['loop'] or clip in ('Dead','Fidget'):assert gap<.0001,(clip,'loop gap',gap)
    report[clip]={'export_surface_error_m':error,'minimum_z_m':minimum,'endpoint_gap_m':gap,
                  'worst_lowest_paw_m':max(min(f.values()) for f in feet),'half_frame_samples':len(feet)}
    print(clip,report[clip],flush=True)
corpse=max((a-b).length for a,b in zip(endposes['Death'][1],endposes['Dead'][0]));assert corpse<.0001,corpse
report['geometry']={'vertices':len(body.data.vertices),'triangles':len(body.data.polygons),'bones':len(rig.data.bones),
    'max_influences':4,'death_dead_gap_m':corpse,'glb_sha256':hashlib.sha256((P/'export/mm8_m452.glb').read_bytes()).hexdigest()}
(P/'work/export_audit.json').write_text(json.dumps(report,indent=2)+'\n')
