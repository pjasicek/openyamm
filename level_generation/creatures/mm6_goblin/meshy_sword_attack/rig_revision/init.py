import bpy,json
from pathlib import Path
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_sword_attack/rig_revision')
with bpy.data.libraries.load(str(ROOT.parent/'goblin_sword.blend'),link=False) as (src,dst):
 dst.scenes=['Meshy Goblin Sword and Native Attack']
s=dst.scenes[0];s.name='Goblin Arm Rig Revision';bpy.context.window.scene=s
r=next(o for o in s.objects if o.type=='ARMATURE');r.name='Goblin Arm Revision Rig'
body=next(o for o in s.objects if o.type=='MESH' and o.data.shape_keys);body.name='Goblin Arm Revision Body'
s['source_actions']=json.dumps({tr.name.removeprefix('Meshy_'):tr.strips[0].action.name for tr in r.animation_data.nla_tracks if tr.name.startswith('Meshy_')})
s['authored_actions']=json.dumps({k:next(tr.strips[0].action.name for tr in r.animation_data.nla_tracks if tr.name==n) for k,n in [('Standing','MM6_Standing_Sword'),('Attack','MM6_Attack_Native')]})
r.animation_data.action=None
for tr in r.animation_data.nla_tracks:tr.mute=True
for pb in r.pose.bones:pb.matrix_basis.identity()
print(json.dumps({'scene':s.name,'rig':r.name,'body':body.name,'bones':len(r.data.bones),'actions':s['authored_actions']}))
