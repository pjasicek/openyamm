"""Numeric source-frame and finger-chain review on the fitted rig, with portable joint data for X-rays."""
import bpy,json,math,sys,os
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_fingers.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
src=json.loads((P/'work/source_rest.json').read_text());off=json.loads(bpy.context.scene['rig_offsets']);fj=json.loads((P/'work/finger_joints.json').read_text())
co=np.array([v.co[:] for v in me.vertices]);pieces=np.array([x.value for x in me.attributes['piece'].data]);faces=[tuple(f.vertices) for f in me.polygons if pieces[f.vertices[0]]==0]
tree=BVHTree.FromPolygons(co.tolist(),faces,all_triangles=True)
report={'frame_error_degrees':{},'fingers':{},'joints':{},'head_weights':{}}
for n in src:
    expected=Quaternion(off[n]['q']).to_matrix()@Matrix(src[n]['rot'])
    actual=rig.data.bones[n].matrix_local.to_quaternion();angle=actual.rotation_difference(expected.to_quaternion()).angle
    report['frame_error_degrees'][n]=math.degrees(min(angle,2*math.pi-angle))
    report['joints'][n]=list(rig.data.bones[n].head_local)
for side in ['L','R']:
    report['fingers'][side]={}
    for i in range(5):
        n=f'B_{side}_Finger{i}';chain=[n]
        while src[chain[-1]]['child']:chain.append(src[chain[-1]]['child'])
        pts=[Vector(fj[side][b]) for b in chain]+[Vector(fj[side][chain[-1]+'_tip'])]
        gaps=[]
        for a,b in zip(pts,pts[1:]):
            for t in np.linspace(0,0.98,11):
                pt=a.lerp(b,float(t));loc,normal,face,dist=tree.find_nearest(pt);gaps.append(max(0,float((pt-loc).dot(normal))))
        report['fingers'][side][str(i)]={'points':[list(v) for v in pts],'outside_max_m':max(gaps)}
vg={g.index:g.name for g in body.vertex_groups}
for n in ['B_Head','B_Neck','B_Spine2']:
    ids=[v.index for v in me.vertices if sum(g.weight for g in v.groups if vg[g.group]==n)>.5]
    report['head_weights'][n]={'count':len(ids),'min':co[ids].min(0).tolist(),'max':co[ids].max(0).tolist()} if ids else {'count':0}
assert max(report['frame_error_degrees'].values())<.05
assert max(v['outside_max_m'] for sd in report['fingers'].values() for v in sd.values())<.002
(P/'review/geometry/rig_gate.json').write_text(json.dumps(report,indent=2)+'\n')
print('FRAME max deg',max(report['frame_error_degrees'].values()),'FINGER outside mm',{s:{i:round(v['outside_max_m']*1000,2) for i,v in f.items()} for s,f in report['fingers'].items()},flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
