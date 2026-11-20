from pathlib import Path
import bpy,json,math
P=Path(__file__).resolve().parents[1];bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(P.parent/'mm6_ogr_claude/export/mm6_ogr.glb'));r=next(o for o in bpy.data.objects if o.type=='ARMATURE');a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];base={};rows=[]
for f in range(40):
 bpy.context.scene.frame_set(f);row={'frame':f}
 for n in ('B_Pelvis','B_Spine2'):
  m=r.matrix_world@r.pose.bones[n].matrix
  if f==0:base[n]=m.copy()
  d=m.to_quaternion()@base[n].to_quaternion().inverted();row[n]={'delta_euler':[math.degrees(v) for v in d.to_euler('XYZ')],'position':list(m.translation)}
 rows.append(row)
(P/'review/source_motion/death_root.json').write_text(json.dumps(rows,indent=2)+'\n');print('DEATH_ROOT',rows[::5],flush=True)
