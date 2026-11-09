import bpy, json, math
from pathlib import Path
from mathutils import Vector
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin')
OUT=ROOT/'anatomy_20261006_r1'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'review_20261006/goblin_review.blend'))
arm=bpy.data.objects['Goblin_Rig'];body=bpy.data.objects['Goblin_Body'];scene=bpy.context.scene
for b in arm.pose.bones:b.matrix_basis.identity()
if arm.animation_data:arm.animation_data.action=None
bpy.context.view_layer.update()
records=[]
for group in body.vertex_groups:
 if not (group.name.startswith('Component_') or group.name.startswith('EarHoop')):continue
 vs=[v.co for v in body.data.vertices if any(g.group==group.index for g in v.groups)]
 if not vs or max(v.z for v in vs)<1.28:continue
 records.append(dict(name=group.name,count=len(vs),lo=[min(v[i] for v in vs) for i in range(3)],hi=[max(v[i] for v in vs) for i in range(3)]))
report=dict(bones={b.name:dict(head=list(b.head_local),tail=list(b.tail_local),parent=b.parent.name if b.parent else None) for b in arm.data.bones if b.name in ['Head','Neck','Jaw','Spine','Spine01','Spine02']},materials=[m.name for m in body.data.materials],groups=records)
(OUT/'inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
