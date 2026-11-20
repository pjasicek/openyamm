"""Verify the cast revision preserves the body, upper performance and other clips, then select it."""
from pathlib import Path
import ast, json, hashlib, math
import bpy
import numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector
p = Path(__file__).resolve().parents[1]
tree = ast.parse((p/'scripts/promote_dual_cast.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'snapshot'],
                       type_ignores=[]), 'snapshot', 'exec'))
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pre_cast_step.blend'))
before = snapshot(); rig = bpy.data.objects['Rig']; scene = bpy.context.scene
changed = {'B_Pelvis'} | {f'B_{s}_{part}' for s in 'LR' for part in ['Thigh','Calf','Foot','Toe0']}
changed |= {b.name for b in rig.pose.bones if b.name.startswith('Robe_')}
upper = [b.name for b in rig.pose.bones if b.name not in changed]
def attach(action):
    rig.animation_data.action = None
    for pb in rig.pose.bones: pb.matrix_basis.identity()
    rig.animation_data.action = action; rig.animation_data.action_slot = action.slots[0]
attach(bpy.data.actions['Attack']); original=[]
for f in range(82):
    scene.frame_set(f); original.append({b.name:b.matrix_basis.copy() for b in rig.pose.bones})
bpy.ops.wm.open_mainfile(filepath=str(p/'work/cast_step.blend'))
assert snapshot() == before
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; scene = bpy.context.scene
attach(bpy.data.actions['Attack']); max_local_error=0.
for f in range(82):
    scene.frame_set(f)
    for n in upper:
        error=float(np.max(np.abs(np.array(rig.pose.bones[n].matrix_basis)-np.array(original[f][n]))))
        max_local_error=max(max_local_error,error)
    if f in [0,81]:
        for n,m in original[f].items(): assert np.max(np.abs(np.array(rig.pose.bones[n].matrix_basis)-np.array(m)))<1e-5,n
assert max_local_error<1e-5,max_local_error
pv=np.array([v.value for v in body.data.attributes['piece'].data]); rest=np.array([v.co[:] for v in body.data.vertices])
legfaces=[tuple(f.vertices) for f in body.data.polygons if all(pv[i]==0 and .13<rest[i,2]<.92 for i in f.vertices)]
clothfaces=[tuple(f.vertices) for f in body.data.polygons if all(pv[i] in [2,5,12,13,14,15,16] and rest[i,2]<1.0 for i in f.vertices)]
leg_ids=np.where((pv==0)&(rest[:,2]>.15)&(rest[:,2]<.90))[0]
def exposed(v, tree):
    out=[]
    for i in leg_ids:
        pt=v[int(i)]; direction=Vector((pt.x,pt.y+.02,0.)).normalized()
        loc,normal,index,distance=tree.ray_cast(pt+direction*.8,-direction,1.6)
        if loc is None or distance>.802:out.append(int(i))
    return out
scene.frame_set(0)
ob=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ob.to_mesh();v=[x.co.copy() for x in mesh.vertices];ob.to_mesh_clear()
baseline_exposed=set(exposed(v,BVHTree.FromPolygons(v,clothfaces)));visible=[]
positions=[]; rotations={n:[] for n in [f'B_{s}_{part}' for s in 'LR' for part in ['Thigh','Calf','Foot']]}; contacts=[]
for t in np.linspace(0,2.7,131):
    f=t*30;scene.frame_set(int(f),subframe=f-int(f))
    positions.append({s:list(rig.pose.bones[f'B_{s}_Foot'].head) for s in 'LR'})
    for n in rotations:rotations[n].append(rig.pose.bones[n].matrix.to_quaternion())
    ob=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ob.to_mesh();v=[x.co.copy() for x in mesh.vertices];ob.to_mesh_clear()
    cloth_tree=BVHTree.FromPolygons(v,clothfaces)
    overlap=BVHTree.FromPolygons(v,legfaces).overlap(cloth_tree)
    new=set(exposed(v,cloth_tree))-baseline_exposed
    if new:visible.append({'time':float(t),'vertices':sorted(new)})
    if overlap:
        centers=np.array([np.array([tuple(v[k]) for k in legfaces[a]]).mean(0) for a,b in overlap])
        contacts.append({'time':float(t),'pairs':len(overlap),'bounds':[centers.min(0).tolist(),centers.max(0).tolist()]})
metrics={}
for n,qs in rotations.items():
    steps=np.array([math.degrees(a.rotation_difference(b).angle) for a,b in zip(qs,qs[1:])]);steps=np.minimum(steps,360-steps)
    metrics[n]={'max_step_deg':float(steps.max()),'max_step_change_deg':float(np.abs(np.diff(steps)).max())}
right=np.array([r['R'] for r in positions]);left=np.array([r['L'] for r in positions])
drift=float(np.linalg.norm(right-right[0],axis=1).max())
assert drift<.001,drift

assert max(x['max_step_deg'] for x in metrics.values())<8,metrics
assert max(x['max_step_change_deg'] for x in metrics.values())<5,metrics
report={'geometry_weights_and_other_clips_identical':before,'upper_body_local_error':max_local_error,
 'endpoints':'Exact previous Attack/Standing pose','right_ankle_drift_m':drift,
 'left_step_forward_m':float(left[0,1]-left[:,1].min()),'left_ankle_lift_m':float(left[:,2].max()-left[0,2]),
 'internal_surface_overlaps':contacts,'baseline_exposed_vertices':sorted(baseline_exposed),
 'new_visible_leg_vertices':visible,'leg_rotation_at_48hz':metrics}
(p/'review/cast_step/verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('CAST_STEP_VERIFY',json.dumps({k:v for k,v in report.items() if k not in ['internal_surface_overlaps','new_visible_leg_vertices']}),flush=True)
assert not visible, f'New visible leg vertices: {visible[:3]}'
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_uv.blend'))
