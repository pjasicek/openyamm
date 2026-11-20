import bpy,json
from pathlib import Path
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin')
OUT=ROOT/'anatomy_20261006_r5'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'anatomy_20261006_r1/goblin_anatomy_r4.blend'))
body=bpy.data.objects['Goblin_Body'];arm=bpy.data.objects['Goblin_Rig']
regions={}
for g in body.vertex_groups:
 if not g.name.startswith('Component_'):continue
 vs=[v.co for v in body.data.vertices if any(x.group==g.index for x in v.groups)]
 if vs:regions[g.name]=dict(count=len(vs),lo=[min(v[i] for v in vs) for i in range(3)],hi=[max(v[i] for v in vs) for i in range(3)])
core=body.vertex_groups['Component_0'].index
points=[dict(i=v.index,co=list(v.co)) for v in body.data.vertices if any(g.group==core for g in v.groups) and 1.29<v.co.z<1.57 and v.co.y<-.045 and abs(v.co.x)<.14]
front_slices={}
for lo,hi in [(1.30,1.35),(1.35,1.39),(1.39,1.43),(1.43,1.46),(1.46,1.485),(1.485,1.51),(1.51,1.54),(1.54,1.57)]:
 pts=[p for p in points if lo<=p['co'][2]<hi]
 front_slices[str((lo,hi))]=sorted(pts,key=lambda p:p['co'][1])[:8]
report=dict(groups=regions,face_slices=front_slices,face_points=points,bones={b.name:dict(head=list(b.head_local),tail=list(b.tail_local)) for b in arm.data.bones if any(s in b.name for s in ['Hand','Foot','Toe','ForeArm','UpLeg','Leg'])})
(OUT/'inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'foot_groups':{k:v for k,v in regions.items() if v['lo'][2]<.4},'front_slices':front_slices,'bones':report['bones']}),flush=True)
