"""Solve both measured hands around the native polearm shaft; preserve the fitted rest rig."""
import bpy, bmesh, sys, json, math
import numpy as np
from pathlib import Path
from mathutils import Vector, Quaternion, Matrix
PROJECT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'work/rig_v1.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;W=rig.matrix_world
lab=np.array([v.value for v in me.attributes['finger'].data]);rest_co=np.array([v.co[:] for v in me.vertices]);D=json.loads((PROJECT/'work/rig.json').read_text());R_HANDLE=.018
FING=(1,2,3,4)
results={}
for SIDE,SGN in [('R',-1),('L',1)]:
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update()
 CH={i:[f'B_{SIDE}_Finger{i}'+suffix for suffix in ['','1','2']] for i in range(5)}
 FJ={CH[i][-1]+'_tip':D['fingers'][SIDE+str(i)][-1] for i in range(5)}
 half={}
 for i,ch in CH.items():
  pts=[np.array(rig.data.bones[n].head_local) for n in ch]+[np.array(FJ[ch[-1]+'_tip'])]
  sk=rest_co[(lab==i+1)&(rest_co[:,0]*SGN>0)]
  dd=[]
  for a,b in zip(pts[:-1],pts[1:]):
   d=b-a;t=np.clip((sk-a)@d/(d@d),0,1);dd.append(np.linalg.norm(sk-a-t[:,None]*d,axis=1))
  half[i]=float(np.median(np.min(dd,axis=0)))
 H=W@rig.pose.bones['B_'+SIDE+'_Hand'].matrix;wr=np.array(H.translation)
 kn=np.mean([np.array(W@rig.pose.bones[CH[i][0]].head) for i in FING],axis=0)
 fdir=kn-wr;fdir/=np.linalg.norm(fdir)
 A=np.array(rig.pose.bones[CH[1][0]].head-rig.pose.bones[CH[4][0]].head);A/=np.linalg.norm(A)
 fp=fdir-A*(fdir@A);fp/=np.linalg.norm(fp);A=A*math.cos(.30)+fp*math.sin(.30);A/=np.linalg.norm(A)
 nrm=np.cross(A,fdir);nrm/=np.linalg.norm(nrm)
 if nrm[0]*SGN>0:nrm=-nrm
 C0=kn-fdir*.025+nrm*.035;m0=C0
 def posed():
     bpy.context.view_layer.update()
     deps = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(deps); m = ev.to_mesh()
     c = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', c); ev.to_mesh_clear()
     return (np.array(body.matrix_world) @ np.c_[c.reshape(-1, 3), np.ones(len(lab))].T).T[:, :3]


 def radial(P, C):
     v = P - C; return np.linalg.norm(v - np.outer(v @ A, A), axis=1), v @ A


 # handle against the palm: slide the line along the palm normal until the palm skin (label 0, near) clears it
 P = posed()
 palm = (lab == 0) & (np.linalg.norm(P - kn, axis=1) < 0.06) & (rest_co[:, 0]*SGN > 0)
 C = m0.copy()
 for step in range(80):
     r, al = radial(P[palm], C)
     near = np.abs(al) < 0.04
     if not near.any() or r[near].min() >= R_HANDLE:
         break
     C = C + nrm * 0.001
 print('HANDLE moved off the palm by', step, 'mm; finger half-thickness cm', {i: round(v * 100, 2) for i, v in half.items()})


 def joints(i):
     pts = [np.array(W @ rig.pose.bones[n].head) for n in CH[i]]
     tail = np.array(W @ rig.pose.bones[CH[i][-1]].matrix @ rig.pose.bones[CH[i][-1]].bone.matrix_local.inverted() @ Vector(FJ[CH[i][-1] + '_tip']))
     return pts + [tail]


 def fk(js, ax, angs):
     p = [j.copy() for j in js]
     for k, a in enumerate(angs):
         R = np.array(Matrix.Rotation(a, 3, Vector(ax)))
         for m in range(k + 1, len(p)):
             p[m] = p[k] + R @ (p[m] - p[k])
     return p


 def cost(p, want):
     c = 0.0
     for a, b in zip(p[:-1], p[1:]):
         for t in (0.2, 0.5, 0.8, 1.0):
             q = a + (b - a) * t
             v = q - C; r = np.linalg.norm(v - A * (v @ A))
             c += (r - want) ** 2 + (400 * (want - r) ** 2 if r < want - 0.001 else 0.0)
     return c


 def turn(n, ax, ang):
     pb = rig.pose.bones[n]; bpy.context.view_layer.update()
     m = W @ pb.matrix; h = m.translation.copy()
     pb.matrix = W.inverted() @ (Matrix.Translation(h) @ Matrix.Rotation(ang, 4, Vector(ax)) @ Matrix.Translation(-h) @ m)
     bpy.context.view_layer.update()


 grid = np.radians(np.arange(0, 111, 10))
 report = {}
 spread = {}
 for i in FING:
     js = joints(i)
     # goblin: the fingers are splayed 25-70 deg away from the handle's normal plane; flexing them about the handle
     # axis sweeps a cone past it. First close the spread at the knuckle (rotation about the palm normal) until the
     # proximal phalanx is perpendicular to the handle, then curl.
     d = js[1] - js[0]
     best_sp = min(np.radians(np.arange(-60, 61, 1)),
                   key=lambda a: (round(abs((np.array(Matrix.Rotation(a, 3, Vector(nrm))) @ d) @ A) / np.linalg.norm(d), 2), abs(a)))
     turn(CH[i][0], nrm, best_sp); spread[i] = round(math.degrees(best_sp))
     js = joints(i)
     d = js[1] - js[0]; ax = A.copy()                  # every finger flexes about the handle axis (fist)
     if (np.array(Matrix.Rotation(0.3, 3, Vector(ax))) @ d) @ nrm < d @ nrm:
         ax = -ax
     want = R_HANDLE + half[i] + 0.0035                    # 2 mm margin: skin, not the bone line, must clear
     best = (1e9, None)
     for a1 in grid:
         for a2 in grid:
             for a3 in grid[::2]:
                 if a3 > a2 + 1e-6:
                     continue                              # anatomy: the fingertip joint bends no more than the middle one
                 c = cost(fk(js, ax, (a1, a2, a3)), want)
                 if c < best[0]:
                     best = (c, (a1, a2, a3))
     for k, n in enumerate(CH[i]):
         turn(n, ax, best[1][k])
     report[i] = [round(math.degrees(x)) for x in best[1]]
 # thumb: swing about the finger direction toward the handle, then flex the two outer joints
 js = joints(0)
 best = (1e9, None)
 for sw in np.radians(np.arange(-120, 121, 10)):        # goblin thumb sits far round the palm
     Rs = np.array(Matrix.Rotation(sw, 3, Vector(fdir)))
     pj = [js[0]] + [js[0] + Rs @ (x - js[0]) for x in js[1:]]
     d = pj[1] - pj[0]; ax = np.cross(d, nrm); ax /= max(np.linalg.norm(ax), 1e-9)
     for a1 in np.radians(np.arange(-40, 81, 10)):           # goblin: the thumb base must flex too (stood 4 cm off)
         for a2 in np.radians(np.arange(-30, 91, 10)):
             for a3 in np.radians(np.arange(0, 81, 10)):
                 p = fk(pj, ax, (a1, a2, a3))
                 c = cost(p[2:], R_HANDLE + half[0] + 0.0035)   # only the distal segment must lie on the handle
                 if c < best[0]:
                     best = (c, (sw, ax, a1, a2, a3))
 sw, tax, a1, a2, a3 = best[1]
 turn(CH[0][0], fdir, sw); turn(CH[0][0], tax, a1); turn(CH[0][1], tax, a2); turn(CH[0][2], tax, a3)
 report[0] = [round(math.degrees(sw)), round(math.degrees(a1)), round(math.degrees(a2)), round(math.degrees(a3))]
 P = posed()
 clear = {}
 for i in range(5):
     m = (lab == i + 1) & (rest_co[:, 0]*SGN > 0)
     r, al = radial(P[m], C); nr = np.abs(al) < 0.12
     clear[i] = round(float(r[nr].min()) * 100, 2) if nr.any() else None
 r, al = radial(P[palm], C)
 print('GRIPSOLVE spread deg', spread, 'curl deg', report, '| skin clearance cm (handle radius', R_HANDLE * 100, ')', clear,
       'palm', round(float(r[np.abs(al) < 0.04].min()) * 100, 2))
 inv = (W @ rig.pose.bones['B_'+SIDE+'_Hand'].matrix).inverted()
 FL = {n: list(rig.pose.bones[n].rotation_quaternion) for ch in CH.values() for n in ch}
 results[SIDE]={'finger_local':FL,'handle_centre_hand_local':list(inv@Vector(C)),'handle_axis_hand_local':list((inv.to_3x3()@Vector(A)).normalized()),'palm_normal_hand_local':list((inv.to_3x3()@Vector(nrm)).normalized()),'radius':R_HANDLE,'curl_deg':report,'clearance_cm':clear,'half_thickness':half}
 # Inspect the evaluated hand against the real shaft radius from five directions.
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());temp=ev.to_mesh();bm=bmesh.new();bm.from_mesh(temp);ev.to_mesh_clear()
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if rest_co[v.index,0]*SGN<.5],context='VERTS')
 mesh=bpy.data.meshes.new('GripReview');bm.to_mesh(mesh);bm.free();obj=bpy.data.objects.new('GripReview',mesh);bpy.context.collection.objects.link(obj);body.hide_render=True
 bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=R_HANDLE,depth=.30,location=C);shaft=bpy.context.object;shaft.rotation_mode='QUATERNION';shaft.rotation_quaternion=Vector(A).to_track_quat('Z','Y');mat=bpy.data.materials.new('ShaftClay');mat.diffuse_color=(.15,.10,.07,1);shaft.data.materials.append(mat)
 sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.show_cavity=True;sc.display.shading.color_type='MATERIAL';sc.render.resolution_x=sc.render.resolution_y=600;sc.render.resolution_percentage=100
 cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.42
 for label,d in [('axis',A),('palm',nrm),('back',-nrm),('side',np.cross(A,nrm)),('tips',-fdir)]:
  cam.location=Vector(C)+Vector(d);cam.rotation_euler=(-Vector(d)).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(PROJECT/'review'/f'grip_{SIDE}_{label}.png');bpy.ops.render.render(write_still=True)
 for o in [shaft,obj,cam]:bpy.data.objects.remove(o,do_unlink=True)
 body.hide_render=False
(PROJECT/'work/grip_pose.json').write_text(json.dumps(results,indent=2)+'\n')
