"""Dense deformed-surface and exported animation checks for the six revised dragon clips."""
import bpy
import json
import math
import numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_v6.blend'))
sc=bpy.context.scene;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
CHANGED=('Standing','Walking','Running','Fidget','Attack','Cast')
actions={a.name:a for a in bpy.data.actions}
def at(name,t):
    rig.animation_data.action=actions[name]
    sc.frame_set(int(t*sc.render.fps),subframe=(t*sc.render.fps)%1)
def vertices():
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
    vs=[ev.matrix_world@v.co for v in mesh.vertices];ev.to_mesh_clear();return vs
ids=[v.value for v in me.attributes['tooth_id'].data]
rows={t['id']:t['row'] for t in json.loads((P/'review/teeth_v2/geometry.json').read_text())['teeth']}
faces={row:[list(f.vertices) for f in me.polygons if rows.get(ids[f.index])==row] for row in ('upper','lower')}
edges={tuple(sorted((a,b))) for fs in faces.values() for f in fs for a,b in zip(f,f[1:]+f[:1])}
lengths={e:(me.vertices[e[0]].co-me.vertices[e[1]].co).length for e in edges}
report={};refs={};loops={}
for name in actions:
    duration=float(actions[name].frame_range[1])/48
    sample_times=np.linspace(0,duration,round(duration*96)+1) if name in CHANGED else np.linspace(0,duration,5)
    min_z=1e9;roots=[];hind=[];mouth=[];max_step=0;prev=None;tooth_error=0
    for t in sample_times:
        at(name,float(t));v=vertices();a=np.array([p[:] for p in v]);min_z=min(min_z,float(a[:,2].min()))
        if name in CHANGED:
            for bone in rig.pose.bones:
                assert max(abs(s-1) for s in bone.scale)<1e-6
                if bone.name!='Root':assert bone.location.length<1e-6
            q=[b.rotation_quaternion.copy() for b in rig.pose.bones]
            if prev:
                max_step=max(max_step,max(2*math.acos(min(1,abs(x.dot(y)))) for x,y in zip(prev,q)))
            prev=q; roots.append(rig.pose.bones['Root'].head.z); hind.append(rig.pose.bones['LHindFoot'].head.z); mouth.append(rig.pose.bones['Socket_Mouth'].head.z)
            trees={row:BVHTree.FromPolygons(v,fs,all_triangles=False,epsilon=0) for row,fs in faces.items()}
            assert not trees['upper'].overlap(trees['lower']), (name,float(t),'teeth')
            tooth_error=max(tooth_error,max(abs((v[x]-v[y]).length-length) for (x,y),length in lengths.items()))
    for t in np.linspace(0,duration,9):
        at(name,float(t));refs[name,float(t)]=vertices()
    if name in CHANGED:
        assert min_z>-.0001,(name,min_z)
        assert tooth_error<2e-6,(name,tooth_error)
        assert max_step<math.radians(15),(name,max_step)
        if name in ('Standing','Walking','Running','Fidget'):
            first=np.array([p[:] for p in refs[name,0.]])
            last=np.array([p[:] for p in refs[name,duration]])
            loops[name]=float(np.max(np.linalg.norm(first-last,axis=1)));assert loops[name]<1e-5
    report[name]={'duration':duration,'samples':len(sample_times),'min_z':min_z,'root_z_range':max(roots)-min(roots) if roots else None,'hind_foot_z_range':max(hind)-min(hind) if hind else None,'mouth_z_min':min(mouth) if mouth else None,'max_step_degrees':math.degrees(max_step),'tooth_edge_error_m':tooth_error}
for t in np.linspace(0,.75,25):
    at('Standing',float(t));a=np.array([v[:] for v in vertices()]);at('Walking',float(t));b=np.array([v[:] for v in vertices()]);assert np.max(np.abs(a-b))<1e-7
assert report['Attack']['root_z_range']<.03
assert report['Attack']['hind_foot_z_range']<.03
for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
for action in list(bpy.data.actions):bpy.data.actions.remove(action)
bpy.ops.import_scene.gltf(filepath=str(P/'export/mm6_cdr1_selected.glb'))
rig=next(o for o in sc.objects if o.type=='ARMATURE');body=next(o for o in sc.objects if o.type=='MESH');actions={a.name.split('|')[-1]:a for a in bpy.data.actions}
for track in rig.animation_data.nla_tracks:track.mute=True
parity={}
def distance(a,b):
    tree=KDTree(len(b))
    for i,v in enumerate(b):tree.insert(v,i)
    tree.balance();return max(tree.find(v)[2] for v in a)
for (name,t),expected in refs.items():
    at(name,t);actual=vertices();error=max(distance(expected,actual),distance(actual,expected))
    parity[name]=max(parity.get(name,0),error);assert error<.0001,(name,t,error)
(P/'review/motion_v6/checks.json').write_text(json.dumps({'clips':report,'loop_endpoint_error_m':loops,'standing_walking_identical':True,'export_parity_m':parity,'teeth_intersections':0},indent=2)+'\n')
print('MOTION CHECK',report,'PARITY',parity)
