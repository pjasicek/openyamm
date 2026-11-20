"""Intersect the actual exported weapons with the posed body/shell after death-drop processing."""
from pathlib import Path
import json
import sys
import numpy as np
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'claude_shared/floor'))
from glb_pose import Glb,Model

selected=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['hes_lancer']
report={}
for name,parts in [('hes_lancer',[('hes_ion_lance','Rifle'),('hes_ion_lance_twin','Rifle')]),
                   ('hes_forgemaster',[('hes_thunder_maul','Thunder_Maul')])]:
    if name not in selected:continue
    model=Model(Glb(P/f'export/{name}.glb'))
    nodes={n.get('name'):i for i,n in enumerate(model.glb.json['nodes'])}
    joint_names=np.array([model.glb.json['nodes'][i]['name'] for i in model.joints])
    body_faces=[]
    for primitive in model.primitives:
        faces=primitive['triangles']
        if primitive['skinned']:
            names=joint_names[primitive['joints']]
            hand=np.array([[any(t in n for t in ('Hand','Finger')) for n in row] for row in names])
            holding=(primitive['weights']*hand).sum(1)>.25
            faces=faces[~holding[faces].any(1)]
        body_faces.append(faces)
    equipment={}
    for part,node in parts:
        item=Model(Glb(P/f'export/{part}.glb'))
        posed=item.skinned_positions(item.world({}))
        points,faces,offset=[],[],0
        for vertices,triangles in posed:
            points.extend(vertices);faces.extend(triangles+offset);offset+=len(vertices)
        points=np.column_stack([np.array(points),np.ones(len(points))])
        equipment[part]=(nodes[node],points,faces)
    family='Forge' if name=='hes_forgemaster' else 'Carbine'
    clips=[family+'_'+r for r in ('Standing','Walking','Attack','Hit','Fidget','Death','Dead')]
    clips+=['Forge_Running','Forge_Cast'] if family=='Forge' else ['Lancer_Running']
    results={}
    for clip in clips:
        duration=model.clip_times(clip)[-1]
        times=np.arange(0,duration+.0001,1/60)
        contacts={part:[] for part in equipment}
        for time in times:
            world=model.world(model.sample(clip,float(time)))
            posed=model.skinned_positions(world)
            points,faces,offset=[],[],0
            for (vertices,_),triangles in zip(posed,body_faces):
                points.extend(vertices);faces.extend(triangles+offset);offset+=len(vertices)
            tree=BVHTree.FromPolygons(points,faces,all_triangles=True)
            for part,(node,vertices,triangles) in equipment.items():
                weapon=BVHTree.FromPolygons((vertices@world[node].T)[:,:3].tolist(),triangles,all_triangles=True)
                overlap=tree.overlap(weapon)
                if overlap:
                    contacts[part].append({'time':round(float(time),5),'triangle_pairs':len(overlap)})
        results[clip]=contacts
        print('RUNTIME_CONTACT',name,clip,{k:len(v) for k,v in contacts.items()},flush=True)
    report[name]=results
(P/'review/runtime_equipment_contacts.json').write_text(json.dumps(report,indent=2)+'\n')
assert not any(frames for clips in report.values() for parts in clips.values() for frames in parts.values()), 'Weapon/body intersections; see report'

import os
sys.stdout.flush();os._exit(0)
