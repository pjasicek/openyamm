"""Evaluate the actual baked pilot surfaces at quarter frames; no art auto-approval."""
import bpy,json,math,numpy as np
from pathlib import Path
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/full_20261006')
bpy.ops.wm.open_mainfile(filepath=str(OUT/'work/native_pilots_v1.blend'))
arm=bpy.data.objects['Goblin_Rig'];body=bpy.data.objects['Goblin_Body'];sword=bpy.data.objects['Goblin_Sword'];scene=bpy.context.scene
body.data.calc_loop_triangles();tri=np.array([t.vertices[:] for t in body.data.loop_triangles]);rest=np.array([v.co[:] for v in body.data.vertices]);restarea=np.linalg.norm(np.cross(rest[tri[:,1]]-rest[tri[:,0]],rest[tri[:,2]]-rest[tri[:,0]]),axis=1)
footindices={side:np.array([v.index for v in body.data.vertices if any(body.vertex_groups[g.group].name==side+'Foot' and g.weight>.99 for g in v.groups)]) for side in ('Right','Left')}
report={};flags=[]
for clip in ('Standing','Walk','Attack'):
    a=bpy.data.actions[clip];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];previous={};worst={};samples=[];first_vertices=None;first_bones={}
    for f in np.arange(a.frame_range[0],a.frame_range[1]+.01,.25):
        scene.frame_set(int(f),subframe=float(f-int(f)));graph=bpy.context.evaluated_depsgraph_get();mesh=body.evaluated_get(graph).data
        v=np.empty(len(mesh.vertices)*3,dtype=np.float32);mesh.vertices.foreach_get('co',v);v=v.reshape(-1,3);assert np.isfinite(v).all()
        if first_vertices is None:first_vertices=v.copy();first_bones={b.name:b.matrix.to_quaternion().copy() for b in arm.pose.bones}
        area=np.linalg.norm(np.cross(v[tri[:,1]]-v[tri[:,0]],v[tri[:,2]]-v[tri[:,0]]),axis=1)/np.maximum(restarea,1e-12)
        tips=sword.evaluated_get(graph).data;blade_min=min(p.co.z for p in tips.vertices)
        record={'frame':float(f),'time_ms':float((f-1)*1000/48),'body_min_z_m':float(v[:,2].min()),'sword_min_z_m':blade_min,'minimum_area_ratio':float(area.min()),'collapsed_faces':np.where(area<.025)[0].tolist(),'feet_min_z_m':{s:float(v[ids,2].min()) for s,ids in footindices.items()}}
        for b in arm.pose.bones:
            assert max(abs(float(s)-1) for s in b.scale)<1e-4,(clip,f,b.name,'bone scale')
            q=b.rotation_quaternion.copy();q.normalize()
            if b.name in previous:
                angle=math.degrees(previous[b.name].rotation_difference(q).angle);angle=min(angle,360-angle)
                if angle>worst.get(b.name,{}).get('degrees',0):worst[b.name]={'degrees':angle,'frame':float(f)}
                if angle>35:flags.append({'clip':clip,'frame':float(f),'bone':b.name,'quarter_frame_rotation_degrees':angle})
            previous[b.name]=q
        if v[:,2].min()<-.008 or blade_min<-.008:flags.append({'clip':clip,'frame':float(f),'ground_penetration_m':min(float(v[:,2].min()),blade_min)})
        samples.append(record)
    report[clip]={'end_to_start_vertex_distance_m':float(np.linalg.norm(v-first_vertices,axis=1).max()),'end_to_start_world_bone_angles_deg':{b.name:math.degrees(first_bones[b.name].rotation_difference(b.matrix.to_quaternion()).angle) for b in arm.pose.bones},'dense_samples':samples,'worst_local_rotations_per_quarter_frame':worst}
(OUT/'review/pilot_dense_checks.json').write_text(json.dumps({'clips':report,'flags':flags,'scope':'Numerical screens complement close review; no automatic artistic pass.'},indent=2)+'\n')
print('Dense pilot flags',json.dumps(flags[:25]),'total',len(flags),flush=True)
print('Collapsed regions',{c:[{'frame':s['frame'],'rest_faces':[{'center':rest[tri[i]].mean(axis=0).tolist(),'area_mm2':float(restarea[i]*.5*1e6),'vertex_weights':[{body.vertex_groups[g.group].name:round(g.weight,3) for g in body.data.vertices[j].groups if body.vertex_groups[g.group].name in arm.data.bones} for j in tri[i]]} for i in s['collapsed_faces'][:6]]} for s in sorted(d['dense_samples'],key=lambda s:s['minimum_area_ratio'])[:2]] for c,d in report.items()},flush=True)
print('Minimum area ratios',{c:min(s['minimum_area_ratio'] for s in d['dense_samples']) for c,d in report.items()},flush=True)
