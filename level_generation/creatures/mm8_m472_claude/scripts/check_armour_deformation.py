from pathlib import Path
import runpy,bpy,numpy as np,json
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/repair_armour.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/check_deformation.py'),init_globals={'INPUT_BLEND':'rig_textured_uv.blend'},run_name='__main__')
report=json.loads((p/'work/deformation.json').read_text())
assert max(r['stretch']['arms']['p99'] for r in report.values())<2
assert max(r['stretch']['hands']['max'] for r in report.values())<4.5
assert min(r['cloth_floor_min_m'] for r in report.values())>-.02
o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];pc=np.array([v.value for v in o.data.attributes['piece'].data]);a=bpy.data.actions['Death'];r.animation_data.action=a
if a.slots:r.animation_data.action_slot=a.slots[0]
minimum=(10,None,None)
for f in range(58):
    bpy.context.scene.frame_set(f);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();z=np.array([v.co.z for v in m.vertices]);i=int(np.argmin(z))
    if z[i]<minimum[0]:minimum=(float(z[i]),f,int(pc[i]))
    ev.to_mesh_clear()
print('FINAL_DEATH_FLOOR',minimum)

runpy.run_path(str(p/'scripts/review_armour.py'),run_name='__main__')
