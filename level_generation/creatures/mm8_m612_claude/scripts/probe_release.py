import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated_authored.blend'))
rig=bpy.data.objects['Rig'];sc=bpy.context.scene
a=bpy.data.actions['Attack'];rig.animation_data.action=a
if a.slots:rig.animation_data.action_slot=a.slots[0]
rows=[]
for f in range(int(a.frame_range[1])+1):
 sc.frame_set(f)
 hand=rig.pose.bones['B_R_Hand'].head
 chest=rig.pose.bones['B_Spine2'].head
 rows.append({'frame':f,'hand':list(hand),'relative_reach':chest.y-hand.y})
print('PALM_REACH',[(r['frame'],round(r['relative_reach'],3)) for r in rows],flush=True)
(P/'work/palm_release_probe.json').write_text(json.dumps(rows,indent=2))
