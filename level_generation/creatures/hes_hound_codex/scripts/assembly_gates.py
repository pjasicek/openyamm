"""Every-frame skin, floor and rigid attachment checks of the final source assembly."""
import bpy, json, os, sys
from pathlib import Path
import numpy as np
from mathutils.bvhtree import BVHTree
PROJECT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'work/assembled.blend'))
rig=bpy.data.objects['Hound_Rig']; body=bpy.data.objects['Hound']; scene=bpy.context.scene
attachments=[o for o in scene.objects if o.type=='MESH' and o!=body]
def coords(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=ev.to_mesh()
    xyz=np.array([tuple(ev.matrix_world@v.co) for v in me.vertices])
    ev.to_mesh_clear(); return xyz
rig.animation_data.action=None
for bone in rig.pose.bones: bone.matrix_basis.identity()
bpy.context.view_layer.update()
body.data.calc_loop_triangles()
tri=np.array([t.vertices[:] for t in body.data.loop_triangles])
def area(xyz):
    a,b,c=xyz[tri[:,0]],xyz[tri[:,1]],xyz[tri[:,2]]
    return np.linalg.norm(np.cross(b-a,c-a),axis=1)*.5
restxyz=coords(body); restarea=area(restxyz); report={}
for action in bpy.data.actions:
    rig.animation_data.action=action
    if action.slots: rig.animation_data.action_slot=action.slots[0]
    r=dict(minimum_z=1.,maximum_lowest_z=-1.,stretch_max=0.,stretched_faces=0,
           attachment_minimum_z={o.name:1. for o in attachments},
           attachment_nearest_surface_max={o.name:0. for o in attachments})
    for frame in range(round(action.frame_range[0]),round(action.frame_range[1])+1):
        scene.frame_set(frame); xyz=coords(body); assert np.isfinite(xyz).all()
        r['minimum_z']=min(r['minimum_z'],float(xyz[:,2].min()))
        r['maximum_lowest_z']=max(r['maximum_lowest_z'],float(xyz[:,2].min()))
        ratio=area(xyz)/np.maximum(restarea,1e-9)
        if ratio.max()>r['stretch_max']:
            face=int(ratio.argmax())
            r.update(stretch_max=float(ratio[face]),stretch_worst_frame=frame,
                     stretch_worst_rest_triangle=restxyz[tri[face]].tolist())
        r['stretched_faces']=max(r['stretched_faces'],int(((ratio>20)&(area(xyz)>1e-6)).sum()))
        tree=BVHTree.FromPolygons(xyz,tri,all_triangles=True)
        for obj in attachments:
            points=coords(obj)
            r['attachment_minimum_z'][obj.name]=min(r['attachment_minimum_z'][obj.name],float(points[:,2].min()))
            near=min(tree.find_nearest(p)[3] for p in points)
            r['attachment_nearest_surface_max'][obj.name]=max(r['attachment_nearest_surface_max'][obj.name],near)
    report[action.name]=r
    print('GATE',action.name,json.dumps(r),flush=True)
(PROJECT/'review/assembly_gates.json').write_text(json.dumps(report,indent=2)+'\n')
assert len(report)==9
assert all(r['minimum_z']>=-.015 and r['stretched_faces']==0 for r in report.values())
assert all(min(r['attachment_minimum_z'].values())>=-.015 for r in report.values())
assert all(max(r['attachment_nearest_surface_max'].values())<.04 for r in report.values())
sys.stdout.flush();sys.stderr.flush();os._exit(0)
