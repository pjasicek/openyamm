"""G6 closed-skin contacts at half frames; own arm and the tail root are excluded."""
import bpy, json, sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work'/__import__('os').environ.get('CONTACT_BLEND','animated_v1.blend')))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
names=[g.name for g in body.vertex_groups]
w=np.zeros((len(me.vertices),len(names)))
for v in me.vertices:
    for e in v.groups:w[v.index,e.group]=e.weight
co=np.array([tuple(v.co) for v in me.vertices])
piece=np.zeros(len(co),np.int32);me.attributes['piece'].data.foreach_get('value',piece)
def weight(terms,side=''):
    return w[:,[i for i,n in enumerate(names) if (not side or n.startswith(f'B_{side}_')) and any(t in n for t in terms)]].sum(1)
parts={}
for side in 'LR':
    exclude=weight(('Clavicle','UpperArm','Forearm','Hand','Finger'),side)>.15
    for part in ('Forearm','Hand'):
        sample=weight((part,'Finger') if part=='Hand' else (part,),side)>.5
        parts[side+'_'+part]=(sample,exclude)
tail=weight(('Tail',))>.1
parts['tail']=(tail&(co[:,1]>.4),tail)
faces=[tuple(f.vertices) for f in me.polygons if piece[f.vertices[0]]==0]
trees={key:[f for f in faces if all(not exclude[i] for i in f)] for key,(_,exclude) in parts.items()}
# A nearest normal alone marks exterior points behind a nearby curved face as inside.
# Confirm enclosure with exit-facing ray hits; the omitted arm openings may miss two axes.
directions=[Vector(v) for v in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1))]
def inside(tree,p):
    hit_count=exits=0
    for direction in directions:
        loc,n,_,_=tree.ray_cast(p+direction*.0001,direction,3)
        if loc is not None:
            hit_count+=1;exits+=int(n.dot(direction)>0)
    return hit_count>=4 and exits==hit_count
report={}
for a in bpy.data.actions:
    if not a.use_fake_user:continue
    if __import__('os').environ.get('GOG_CHECK_CLIP',a.name)!=a.name:continue
    rig.animation_data.action=a
    if a.slots:rig.animation_data.action_slot=a.slots[0]
    worst={}
    for frame in np.arange(0,a.frame_range[1]+.01,.5):
        bpy.context.scene.frame_set(int(frame),subframe=float(frame-int(frame)))
        ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
        pts=np.array([tuple(v.co) for v in m.vertices]);ev.to_mesh_clear()
        for key,(sample,_) in parts.items():
            tree=BVHTree.FromPolygons(pts.tolist(),trees[key])
            for i in np.where(sample)[0]:
                p=Vector(pts[i]);hit,normal,face,d=tree.find_nearest(p,.15)
                if hit is not None and d>.002 and (p-hit).dot(normal)<-.7*d and inside(tree,p):
                    if d>worst.get(key,{}).get('depth_m',0):
                        worst[key]={'depth_m':float(d),'frame':float(frame),'vertex':int(i),'face':list(trees[key][face])}
    report[a.name]=worst
    print('CONTACT',a.name,worst,flush=True)
(P/'work'/__import__('os').environ.get('CONTACT_REPORT','contacts.json')).write_text(json.dumps(report,indent=2,allow_nan=False))
