"""Inspect evaluated delivery geometry, skin weights and action endpoints without engine scenario runs."""
import argparse
import bpy
import json
import sys
import numpy as np
from pathlib import Path

ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from review_motion import bounds,frame_at

def build(scene_name,output,manifest_override=None):
    scene=bpy.data.scenes[scene_name];bpy.context.window.scene=scene
    rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.data.pose_position='POSE'
    manifest=manifest_override or json.loads((ROOT/'animations/manifest.json').read_text())
    report={'scene':scene_name,'meshes':[],'clips':{}}
    for obj in scene.objects:
        if obj.type!='MESH' or obj.get('review_only'):continue
        groups={g.index for g in obj.vertex_groups if g.name in rig.data.bones}
        sums=[sum(g.weight for g in v.groups if g.group in groups) for v in obj.data.vertices]
        if not groups:continue
        report['meshes'].append({'name':obj.name,'vertices':len(sums),
            'unweighted':sum(s<.000001 for s in sums),'max_weight_error':max(abs(s-1) for s in sums),
            'max_influences':max(sum(g.group in groups and g.weight>1e-7 for g in v.groups) for v in obj.data.vertices)})
    for name,clip in manifest['clips'].items():
        rig.animation_data.action=bpy.data.actions[clip['action']];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
        count=121 if name in {'Death','Walk'} else 19
        samples=[];first=None;last=None
        for i in range(count):
            phase=i/(count-1);frame_at(scene,clip,phase)
            sample={'phase':phase,**bounds(scene)};samples.append(sample)
            matrices=np.array([np.array(b.matrix) for b in rig.pose.bones])
            if i==0:first=matrices
            if i==count-1:last=matrices
        entry={'sample_count':count,'minimum_ground_z':min(s['min'][2] for s in samples),'bounds':samples}
        if clip['loop']:entry['loop_matrix_error']=float(np.abs(first-last).max())
        if name=='Death':death_end=last.copy()
        if name=='Corpse':report['death_corpse_matrix_error']=float(np.abs(death_end-first).max())
        report['clips'][name]=entry
    report['passes']={
        'normalized_weights':all(m['unweighted']==0 and m['max_weight_error']<1e-5 for m in report['meshes']),
        'ground':all(c['minimum_ground_z']>=-.0005 for c in report['clips'].values()),
        'loops':all(c.get('loop_matrix_error',0)<1e-5 for c in report['clips'].values()),
        'death_endpoint':report['death_corpse_matrix_error']<1e-5,
    }
    output.parent.mkdir(exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passes':report['passes'],'ground':{k:v['minimum_ground_z'] for k,v in report['clips'].items()}}))
    assert all(report['passes'].values()),'Evaluated asset checks failed; inspect the written report'

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--scene',required=True);parser.add_argument('--output',type=Path,required=True)
    options=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);build(options.scene,options.output)
