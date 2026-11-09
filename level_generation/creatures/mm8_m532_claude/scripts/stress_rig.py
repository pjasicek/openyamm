"""Hybrid rig deformation probes, with measured edge stretch and front/side views."""
from pathlib import Path
import bpy,json,sys,math
import numpy as np
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_rat_claude/scripts'));import posing as Q
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
edges=np.array([tuple(e.vertices)for e in body.data.edges]);co=np.array([tuple(v.co)for v in body.data.vertices]);length=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)
comp=np.array([x.value for x in body.data.attributes['component'].data]);skin=(comp[edges[:,0]]==0)&(comp[edges[:,1]]==0)&(length>.004)
sc.render.engine='BLENDER_WORKBENCH';sh=sc.display.shading;sh.light='STUDIO';sh.color_type='SINGLE';sh.single_color=(.65,.64,.60);sh.show_cavity=True;sh.show_shadows=False
sc.world=bpy.data.worlds.new('ReviewWorld');sc.world.color=(.16,.16,.16)
sc.render.resolution_x=720;sc.render.resolution_y=720;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=3.55
results={}
for pose in ('rest','bow_reach','stride','rear','collapse'):
    Q.reset(rig)
    if pose=='bow_reach':
        Q.rotate_world(rig,'Chest',(0,0,1),-25)
        Q.two_bone_ik(rig,'LArm','LForeArm',(.15,-1.43,1.93),(.9,-.7,1.9))
        Q.two_bone_ik(rig,'RArm','RForeArm',(-.16,-.82,2.10),(-.9,-.2,2.1))
    elif pose=='stride':
        for side,sg in [('L',1),('R',-1)]:
            Q.two_bone_ik(rig,'FrontUpper_'+side,'FrontLower_'+side,(sg*.215,-.625+sg*.18,.16+max(0,sg)*.13),(sg*.3,-.1,.6))
            Q.rotate_world(rig,'HindUpper_'+side,(1,0,0),sg*24)
            Q.rotate_world(rig,'HindLower_'+side,(1,0,0),-sg*20)
    elif pose=='rear':
        Q.rotate_world(rig,'HorsePelvis',(1,0,0),-22)
        Q.rotate_world(rig,'Spine',(1,0,0),15)
        for side in ('L','R'):
            Q.rotate_world(rig,'FrontUpper_'+side,(1,0,0),-25)
            Q.rotate_world(rig,'FrontLower_'+side,(1,0,0),60)
        Q.rotate_world(rig,'LArm',(0,1,0),-80);Q.rotate_world(rig,'RArm',(0,1,0),65)
        Q.rotate_world(rig,'Head',(0,0,1),35)
    elif pose=='collapse':
        Q.rotate_world(rig,'Root',(0,1,0),70)
        Q.rotate_world(rig,'Spine',(1,0,0),35)
        Q.rotate_world(rig,'LArm',(0,1,0),30);Q.rotate_world(rig,'RArm',(0,1,0),-40)
    dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);m=ev.to_mesh();pts=np.array([tuple(v.co)for v in m.vertices]);ev.to_mesh_clear()
    stretch=np.linalg.norm(pts[edges[:,0]]-pts[edges[:,1]],axis=1)/np.maximum(length,1e-8)
    results[pose]={'skin_edge_p99':float(np.percentile(stretch[skin],99)),'skin_edge_max':float(stretch[skin].max())}
    center=Vector((pts.min(0)+pts.max(0))/2)
    for view,direction in [('front',(0,-1,.03)),('side',(-1,0,.03))]:
        cam.location=center+Vector(direction)*8;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        sc.render.filepath=str(P/'review'/f'stress_{pose}_{view}.png');bpy.ops.render.render(write_still=True)
(P/'review/stress_report.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results))
