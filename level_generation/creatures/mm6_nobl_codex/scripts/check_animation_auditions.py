"""Measure audition posture and verify the original baseline clips remain intact."""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];O=P/'review/animation_alternatives_20261011'
bpy.ops.wm.open_mainfile(filepath=str(O/'auditions.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene
def bind(a):
 rig.animation_data.action=a
 if a.slots:rig.animation_data.action_slot=a.slots[0]
def pt(n):return rig.matrix_world@rig.pose.bones[n].head
bind(bpy.data.actions['Standing']);scene.frame_set(0);hz=pt('B_Pelvis').z
results={}
for act in bpy.data.actions:
 bind(act);start,end=act.frame_range;vals=[]
 for i in range(61):
  f=start+(end-start)*i/60;scene.frame_set(int(f),subframe=f-int(f))
  torso=pt('B_Neck')-pt('B_Pelvis')
  lean=math.degrees(torso.angle(Vector((0,0,1))))
  vals.append((lean,pt('B_Pelvis').z/hz))
 assert all(math.isfinite(x) for row in vals for x in row)
 results[act.name]={'torso_lean_mean_deg':round(sum(v[0] for v in vals)/len(vals),1),
  'torso_lean_max_deg':round(max(v[0] for v in vals),1),'hips_min_vs_standing':round(min(v[1] for v in vals),3)}
assert len(results)==12
for n in ('Attack_A_Inward','Attack_B_Outward','Attack_C_Overhead','Hit_A_Quick','Hit_B_Light'):
 assert abs(results[n]['hips_min_vs_standing']-1)<.001
root=P.parents[2]
hashes={}
for name,expected in [('mm6_nobl.glb','f197087a462dc6fbaa1e7db776d428563509487b89603937e31045e304df4601'),('mm6_nobl_sword.glb','fabf23523a56342959a34f3273c1a57db125108ecbc4f5599feea1a6714fa89c')]:
 actual=hashlib.sha256((root/'assets_dev/worlds/mm6/models'/name).read_bytes()).hexdigest()
 assert actual==expected;hashes[name]=actual
(O/'posture_checks.json').write_text(json.dumps({'sampled_poses_per_clip':61,'clips':results,'installed_unchanged':hashes},indent=2))
print(json.dumps(results,indent=2))
