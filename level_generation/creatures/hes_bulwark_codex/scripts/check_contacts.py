"""Sample rigid-part contacts on every clip; preserve measured rest interlocks as a baseline."""
import json,itertools
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/bulwark_rig.blend'))
rig=bpy.data.objects['BulwarkRig'];scene=bpy.context.scene
parts={o.name:o for o in scene.objects if o.type=='MESH'}
faces={n:[list(f.vertices) for f in o.data.polygons] for n,o in parts.items()}
source_ids={n:[x.value for x in o.data.attributes['source_component'].data] for n,o in parts.items()}
# Only the exposed barrel length; its breech intentionally nests inside the pitch yoke.
for n in ('B_Recoil_Upper','B_Recoil_Lower'):
    chosen=[f for f in parts[n].data.polygons if f.center.y<-.7]
    source_ids[n]=[source_ids[n][f.index] for f in chosen]
    faces[n]=[list(f.vertices) for f in chosen]
pairs=[]
for n in parts:
    if n.endswith(('_Upper','_Lower','_Foot')) and not n.startswith('B_Recoil'):
        pairs.append((n,'B_Chassis'))
for a,b in itertools.combinations(parts,2):
    if a.startswith(('B_LF','B_RF','B_LH','B_RH')) and b.startswith(('B_LF','B_RF','B_LH','B_RH')) and a.split('_')[1]!=b.split('_')[1]:pairs.append((a,b))
for n in ('B_Recoil_Upper','B_Recoil_Lower'):pairs.extend([(n,'B_Chassis'),(n,'B_Head')])
def measure():
    dg=bpy.context.evaluated_depsgraph_get();trees={};coords={}
    for n,o in parts.items():
        ev=o.evaluated_get(dg);me=ev.to_mesh();v=[x.co.copy() for x in me.vertices];coords[n]=v
        trees[n]=BVHTree.FromPolygons(v,faces[n]);ev.to_mesh_clear()
    result={}
    for a,b in pairs:
        overlap=trees[a].overlap(trees[b]);result[a+' / '+b]={(source_ids[a][i],source_ids[b][j]) for i,j in overlap}
    return result
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update();base=measure()
report={'sample_hz':60,'baseline_component_interlocks':{k:sorted(v) for k,v in base.items() if v},'clips':{}}
for action in bpy.data.actions:
    if not action.slots:continue
    rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];worst={};all_new={}
    for frame in np.arange(0,round(action.frame_range[1])+.01,.5):
        scene.frame_set(int(frame),subframe=float(frame%1));hits=measure()
        for pair,items in hits.items():
            new=items-base[pair]
            all_new.setdefault(pair,set()).update(new)
            if new and len(new)>worst.get(pair,{}).get('new_component_pairs',0):worst[pair]={'new_component_pairs':len(new),'total_component_pairs':len(items),'frame':frame,'pairs':sorted(new)}
    for pair,hit in worst.items():hit['pairs']=sorted(all_new[pair])
    report['clips'][action.name]=worst
# Component 38 is the LH hip collar beside bearing 145: it enters the same socket as the other hip caps.
allowed={'B_LH_Upper / B_Chassis':{(38,1)}}
report['allowed_moving_joint_interlocks']={k:sorted(v) for k,v in allowed.items()}
report['unexpected_contacts']=[]
for clip,pairs in report['clips'].items():
    for pair,hit in pairs.items():
        unexpected=set(map(tuple,hit['pairs']))-allowed.get(pair,set())
        if unexpected:report['unexpected_contacts'].append({'clip':clip,'pair':pair,'components':sorted(unexpected)})
assert not report['unexpected_contacts'],report['unexpected_contacts']
(P/'review/geometry/contact_components.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
