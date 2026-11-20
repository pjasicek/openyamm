"""Finish only the user's Run B / Hit A choices; preserve the current Attack byte-for-byte."""
import bpy,sys,runpy,os
from pathlib import Path
p=Path(__file__).resolve().parents[1];out=p/'review/selected_motion_20261011'
sys.path.insert(0,str(p/'scripts'))
def execute(name,code):
 exec(compile(code,str(p/'scripts'/name),'exec'),{'__file__':str(p/'scripts'/name),'__name__':'__main__'})
# Reuse the established fixed-length leg solver without its historical mesh/weight edits.
s=(p/'scripts/feet_cloak_repair.py').read_text().replace('rig_v10.blend','rig_v15_import.blend')
start=s.index('for i in np.flatnonzero');end=s.index('rest={b.name',start);s=s[:start]+s[end:]
s=s.replace('for act in bpy.data.actions:',"for act in [bpy.data.actions['Running']]:")
s=s.replace("['Standing','Fidget','Walking','Running','Attack','Hit','Death']","['Running']")
s=s.replace("(.75 if s=='L' else .25)","(.24 if s=='L' else .72)")
s=s.replace("contact=.56 if name=='Walking' else .43","contact=.56 if name=='Walking' else .32")
s=s.replace("(.085 if name=='Walking' else .14)","(.085 if name=='Walking' else .18)")
needle="ankle=b.head.copy()"
s=s.replace(needle,needle+"""
   if name=='Running':
    # The running 1.2 * 1.55 m stride contract gives a planted foot a constant backward speed.
    if phase<=contact:
     ankle.y=1.86*(phase-contact*.5)
    else:
     t=(phase-contact)/(1-contact)
     h00=2*t**3-3*t*t+1;h10=t**3-2*t*t+t;h01=-2*t**3+3*t*t;h11=t**3-t*t
     ankle.y=h00*(1.86*contact*.5)+h10*(1.86*(1-contact))+h01*(-1.2*contact*.5)+h11*(1.86*(1-contact))
""")
start=s.index('# Corpse keeps');end=s.index('for a in bpy.data.actions:',start);s=s[:start]+s[end:]
s=s.replace('for a in bpy.data.actions:',"for a in [bpy.data.actions['Running']]:")
s=s.replace('rig_v11_geometry.blend','rig_v15_feet.blend').replace('review/feet_cloak_20261011/repair.json','review/selected_motion_20261011/feet.json')
execute('feet_cloak_repair.py',s)
# Bake both existing rear cloth groups against the new gait and upright recoil.
for group in ['nobl_cloak','nobl_skirt_back']:
 os.environ['CLOTH_GROUP']=group
 sys.argv=['cloak_sim.py','--','rig_v15_feet.blend','Running','Hit']
 runpy.run_path(str(p/'scripts/cloak_sim.py'),run_name='__main__')
os.environ.pop('CLOTH_GROUP',None)
# Existing coherent front-tabard solver, with the already repaired pinning preserved.
s=(p/'scripts/feedback_tabard.py').read_text().replace('rig_v10_geometry.blend','rig_v15_feet.blend').replace('rig_v10.blend','rig_v15_cloth.blend')
start=s.index('for i in C:');end=s.index('co=np.array([v.co[:] for v in me.vertices]);index=',start);s=s[:start]+s[end:]
s=s.replace("roles=['Standing','Walking','Running','Attack','Hit','Death','Fidget']","roles=['Running','Hit']")
start=s.index('# Exact held death pose.');end=s.index("sc['tabard_feedback_repair']",start);s=s[:start]+s[end:]
s=s.replace('review/feedback_20261011/tabard_repair.json','review/selected_motion_20261011/tabard.json')
execute('feedback_tabard.py',s)
# Exact loop closure for new cloth, and the recoil returns to its standing baseline.
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v15_cloth.blend'))
r=bpy.data.objects['Rig'];sc=bpy.context.scene
def use(a):
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
def pose():return {b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in r.pose.bones}
use(bpy.data.actions['Standing']);sc.frame_set(0);standing=pose()
from mathutils import Quaternion
a=bpy.data.actions['Running'];use(a);end=int(a.frame_range[1]);samples=[]
for f in range(end+1):
 sc.frame_set(f);samples.append(pose())
cloth=[n for n in samples[0] if n.startswith(('Cloak_','Tabard_','BackTabard_'))]
for f,row in enumerate(samples):
 sc.frame_set(f);t=f/end;t=t*t*(3-2*t)
 for n in cloth:
  q,pos=row[n];dq=samples[0][n][0]@samples[-1][n][0].inverted();dp=samples[0][n][1]-samples[-1][n][1]
  b=r.pose.bones[n];b.rotation_quaternion=Quaternion().slerp(dq,t)@q;b.location=pos+dp*t
  b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
a=bpy.data.actions['Hit'];use(a);end=int(a.frame_range[1]);samples=[]
for f in range(end+1):
 sc.frame_set(f);samples.append(pose())
for f,row in enumerate(samples):
 sc.frame_set(f);t=max(0,min(1,(f-(end-4))/4));t=t*t*(3-2*t)
 for n,(q,pos) in row.items():
  b=r.pose.bones[n];b.rotation_quaternion=q.slerp(standing[n][0],t);b.location=pos.lerp(standing[n][1],t)
  b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
for a in [bpy.data.actions['Running'],bpy.data.actions['Hit']]:
 for l in a.layers:
  for st in l.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
use(bpy.data.actions['Standing']);sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v15.blend'))
# Check arms, hands, blade axis and head before the runtime build.
for name,args in [('g6_contacts.py',[p/'work/rig_v15.blend','Running','Hit']),('g5_hand_stretch.py',[p/'work/rig_v15.blend','Running','Hit']),('g6_head_clearance.py',[p/'work/rig_v15.blend','Running','Hit'])]:
 sys.argv=[name,'--']+[str(x) for x in args];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
