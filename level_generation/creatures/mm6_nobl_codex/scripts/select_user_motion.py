"""Import the selected two audition actions; preserve selected geometry and all other actions."""
import bpy,json,sys,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];O=P/'review/selected_motion_20261011';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v14.blend'))
rig=bpy.data.objects['Rig'];sc=bpy.context.scene
def curves(a):return [fc for l in a.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
def signature(a):
 return hashlib.sha256(json.dumps([(fc.data_path,fc.array_index,[(list(k.co),list(k.handle_left),list(k.handle_right),k.interpolation) for k in fc.keyframe_points]) for fc in curves(a)],sort_keys=True).encode()).hexdigest()
original={a.name:signature(a) for a in bpy.data.actions}
with bpy.data.libraries.load(str(P/'review/animation_alternatives_20261011/auditions.blend'),link=False) as (src,dst):
 dst.actions=['Run_B_Jog','Hit_A_Quick']
for source,target in [('Run_B_Jog','Running'),('Hit_A_Quick','Hit')]:
 bpy.data.actions.remove(bpy.data.actions[target]);bpy.data.actions[source].name=target
 a=bpy.data.actions[target];a.use_fake_user=True;rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
# Close the small imported cyclic mismatch continuously over the run, including derivatives later checked by gates.
a=bpy.data.actions['Running'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
end=int(a.frame_range[1]);samples=[]
for f in range(end+1):
 sc.frame_set(f);samples.append({b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones})
from mathutils import Quaternion
for f,row in enumerate(samples):
 sc.frame_set(f);t=f/end;t=t*t*(3-2*t)
 for n,(q,pos) in row.items():
  dq=samples[0][n][0]@samples[-1][n][0].inverted();dp=samples[0][n][1]-samples[-1][n][1]
  b=rig.pose.bones[n];b.rotation_quaternion=Quaternion().slerp(dq,t)@q;b.location=pos+dp*t
  b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
rows=[]
for f in range(end+1):
 sc.frame_set(f)
 rows.append({'f':f,'pelvis':list(rig.pose.bones['B_Pelvis'].head),'L':list(rig.pose.bones['B_L_Foot'].head),'R':list(rig.pose.bones['B_R_Foot'].head)})
after={a.name:signature(a) for a in bpy.data.actions}
assert set(after)==set(original)
assert all(after[n]==v for n,v in original.items() if n not in ('Running','Hit'))
(O/'preserved_actions.json').write_text(json.dumps({'before':original,'after_import':after,'run_ankles':rows},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v15_import.blend'))
print('IMPORTED Run B and Hit A; kept Attack and five other clips unchanged.')
print('ANKLES',json.dumps(rows[::3]))
