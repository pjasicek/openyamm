"""Far spear keeps the continuous shaft, grip and blade; raised thread becomes baked detail."""
import bpy,bmesh,sys,json,math,subprocess,shutil
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import reduction_common as C,reduction_bake as B
from reduction_render import render
code=(P/'scripts/build_props.py').read_text();exec(code[code.index('def mesh'):code.index('def finish')])
cal=json.loads((P/'review/calibration.json').read_text());rows=[]
for level in [2,3]:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/lod{level}_fit{1 if level==2 else 8}.blend'));C.reset();rig=bpy.data.objects['Rig'];old=bpy.data.objects['SpearMesh'];material=old.data.materials[0];bpy.data.objects.remove(old,do_unlink=True)
 parts=[cyl('Continuous shaft',.012,1.70,-.04,12 if level==2 else 8),cyl('Socket',.014,.12,.81,8)]
 for c,h,r in [(-.025,.19,.0157),(.35,.045,.0152),(.775,.065,.0167),(-.865,.036,.0152)]:
  if level==3 and c!=-.025:continue
  parts.append(cyl('Bound leather',r,h,c,12 if c==-.025 else 8))
 rings=[(.85,.007,.005),(.875,.030,.009),(.92,.028,.008),(1.015,.010,.004),(1.08,.0004,.0004)] if level==2 else [(.85,.007,.005),(.89,.030,.009),(1.08,.0004,.0004)]
 vv=[];ff=[]
 for z,w,t in rings:
  vv.extend([(-w,0,z),(0,-t,z),(w,0,z),(0,t,z)])
 for j in range(len(rings)-1):
  for k in range(4):a=j*4+k;b=j*4+(k+1)%4;ff.append((a,b,b+4,a+4))
 ff.extend([tuple(reversed(range(4))),tuple(range(len(vv)-4,len(vv)))]);parts.append(mesh('Diamond blade',vv,ff))
 for side in [-1,1]:
  pts=[(.013,side*.004,.75),(.025,side*.018,.65),(.034,side*.026,.58)];parts.append(tube('Tassel cord',pts,.002,3))
  a=Vector(pts[-1]);v=[a+Vector((x,y,z))for x,y,z in [(0,0,0),(-.010,0,-.045),(0,-.003,-.14),(.012,0,-.052),(0,.003,-.05)]];parts.append(mesh('Feather tassel',v,[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(0,3,2,1)]))
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=parts[0];o.name='SpearMesh';bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 M=rig.data.bones['Spear'].matrix_local
 for v in o.data.vertices:
  z=v.co.z
  if z>.775:v.co.z=z+cal['spear_tip_m']-1.08
  elif z>.15:v.co.z=.15+(z-.15)*(cal['spear_tip_m']-.305-.15)/(.775-.15)
  elif z<-.15:v.co.z=-.15+(z+.15)*(cal['spear_butt_m']-.15)/(.89-.15)
  v.co=M@v.co
 o.vertex_groups.new(name='Spear').add(list(range(len(o.data.vertices))),1,'REPLACE');o.parent=rig;m=o.modifiers.new('Rig','ARMATURE');m.object=rig;o.data.materials.append(material)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
 tex=P/f'work/reduction/lod{level}_continuous';shutil.copytree(P/f'work/reduction/lod{level}_fit' if level==2 else P/'work/reduction/lod3_envelopes',tex,dirs_exist_ok=True);B.bake(o,tex/'spear');subprocess.run(['/usr/bin/python3','-B',str(P/'scripts/tier_previews.py'),str(tex)],check=True)
 dest=P/f'work/lod{level}_continuous.blend';report={'level':level,'triangles':{name:C.triangles(bpy.data.objects[name])for name in ['Body','SpearMesh','BucklerMesh']}};assert report['triangles']['SpearMesh']<=(552 if level==2 else 221)
 bpy.ops.wm.save_as_mainfile(filepath=str(dest));out=P/f'review/reduction/lod{level}_continuous';render(dest,out,tex,220 if level==2 else 88)
 v=json.loads(subprocess.check_output(['/usr/bin/python3','-B',str(P/'scripts/reduction_metrics.py'),str(P/f'review/reduction/lod{level}_reference'),str(out)],text=True));rr=list(v['views'].values());uu=[(x['reference_pixels']+x['candidate_pixels'])/(1+x['iou'])for x in rr];report['pooled_iou']=sum(x['iou']*u for x,u in zip(rr,uu))/sum(uu);report['visual']=v;rows.append(report);(P/'review/reduction/continuous_curve.json').write_text(json.dumps(rows,indent=2));print('CONTINUOUS',report['level'],report['triangles'],report['pooled_iou'],flush=True)
