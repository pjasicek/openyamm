"""Read local Mixamo clips for a motion-only shortlist; no production asset writes."""
import bpy, json, math, re
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
OUT=P/'review/animation_alternatives_20261011'
OUT.mkdir(exist_ok=True)
LIB=Path('/home/pjasicek/Downloads/mixamo_library')
pat=r'(Run With Sword|Standard Run|Jogging|Jog Forward|Running( \([0-9]+\))?|Standing Run Forward( \([0-9]+\))?|Stable Sword .+|Standing Melee Attack (Downward|Horizontal|Backhand)|Sword And Shield (Run|Impact.*|Slash.*|Attack.*)|Hit Reaction( \([0-9]+\))?|Light Hit To Head( \([0-9]+\))?)'
rows=[]
for path in sorted(LIB.glob('*.fbx')):
 if not re.fullmatch(pat,path.stem): continue
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.fbx(filepath=str(path))
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
 act=rig.animation_data.action
 fps=bpy.context.scene.render.fps/bpy.context.scene.render.fps_base
 bones={b.name.split(':')[-1]:b for b in rig.pose.bones}
 def pt(n): return rig.matrix_world@bones[n].head
 hips_rest=(rig.matrix_world@bones['Hips'].bone.head_local).z
 vals=[]
 f0,f1=act.frame_range
 for f in [f0+(f1-f0)*i/40 for i in range(41)]:
  bpy.context.scene.frame_set(int(f),subframe=f-int(f))
  v=pt('Neck')-pt('Hips')
  lean=math.degrees(v.angle(Vector((0,0,1))))
  bends=[]
  for s in ('Left','Right'):
   a,b,c=pt(s+'UpLeg'),pt(s+'Leg'),pt(s+'Foot')
   bends.append(180-math.degrees((a-b).angle(c-b)))
  vals.append({'hip':pt('Hips').z/hips_rest,'lean':lean,'knees':bends})
 row={'file':path.name,'fps':fps,'duration':(f1-f0)/fps,
      'action':act.name,'hip_ratio':[round(min(v['hip'] for v in vals),3),round(sum(v['hip'] for v in vals)/41,3)],
      'lean_deg':[round(sum(v['lean'] for v in vals)/41,1),round(max(v['lean'] for v in vals),1)],
      'knee_start':[round(x,1) for x in vals[0]['knees']],
      'rest_bones':{n:{'head':list(rig.matrix_world@b.bone.head_local),'tail':list(rig.matrix_world@b.bone.tail_local)} for n,b in bones.items()}}
 rows.append(row)
 print('CLIP',json.dumps({k:v for k,v in row.items() if k!='rest_bones'}),flush=True)
(OUT/'source_metrics.json').write_text(json.dumps(rows,indent=2))
assert len(rows)>20 and all(r['fps']>0 and r['duration']>0 for r in rows)
