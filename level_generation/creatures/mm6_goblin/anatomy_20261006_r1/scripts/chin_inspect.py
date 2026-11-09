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

core=body.vertex_groups['Component_0'].index
rows=[]
for v in body.data.vertices:
 if any(g.group==core for g in v.groups) and abs(v.co.x)<.12 and v.co.y<-.07 and 1.24<v.co.z<1.38:
  rows.append(dict(id=v.index,co=list(v.co),weights={body.vertex_groups[g.group].name:round(g.weight,3) for g in v.groups if body.vertex_groups[g.group].name in arm.data.bones}))
(OUT/'chin_points.json').write_text(json.dumps(sorted(rows,key=lambda r:r['co'][2]),indent=2)+'\n')
print(len(rows), 'chin/neck points captured')
