"""Check the exported skin at every frame of all nine clips, including repaired far LODs."""
import bpy, json, os, sys
from pathlib import Path
import numpy as np
PROJECT=Path(__file__).resolve().parents[1]
folder=PROJECT/'work/motion_v2_lods/hes_hound'
out={}
for level in range(4):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(folder/f'lod{level}.glb'))
    scene=bpy.context.scene; scene.render.fps=60
    rig=next(o for o in scene.objects if o.type=='ARMATURE')
    body=next(o for o in scene.objects if o.type=='MESH')
    body.data.calc_loop_triangles(); tri=np.array([t.vertices[:] for t in body.data.loop_triangles])
    def points():
        ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=ev.to_mesh()
        xyz=np.array([tuple(ev.matrix_world@v.co) for v in me.vertices]);ev.to_mesh_clear();return xyz
    def areas(xyz):
        a,b,c=xyz[tri[:,0]],xyz[tri[:,1]],xyz[tri[:,2]]
        return np.linalg.norm(np.cross(b-a,c-a),axis=1)*.5
    rig.animation_data.action=None
    for bone in rig.pose.bones:bone.matrix_basis.identity()
    bpy.context.view_layer.update(); rest=areas(points())
    clips={}
    for action in bpy.data.actions:
        rig.animation_data.action=action
        if action.slots:rig.animation_data.action_slot=action.slots[0]
        result=dict(minimum_z=1.,maximum_lowest_z=-1.,stretch_max=0.,stretched_faces=0)
        for frame in range(round(action.frame_range[0]),round(action.frame_range[1])+1):
            scene.frame_set(frame);xyz=points();assert np.isfinite(xyz).all()
            a=areas(xyz); ratio=a/np.maximum(rest,1e-9)
            result['minimum_z']=min(result['minimum_z'],float(xyz[:,2].min()))
            result['maximum_lowest_z']=max(result['maximum_lowest_z'],float(xyz[:,2].min()))
            result['stretch_max']=max(result['stretch_max'],float(ratio.max()))
            result['stretched_faces']=max(result['stretched_faces'],int(((ratio>20)&(a>1e-6)).sum()))
        clips[action.name]=result
    out[str(level)]=dict(triangles=len(tri),clips=clips)
    print('LOD_GATE',level,json.dumps(out[str(level)]),flush=True)
(PROJECT/'review/lod_animation_gates.json').write_text(json.dumps(out,indent=2)+'\n')
assert all(len(lod['clips'])==9 for lod in out.values())
assert all(c['minimum_z']>=-.015 and c['stretched_faces']==0 for lod in out.values() for c in lod['clips'].values())
assert all(c['maximum_lowest_z']<.04 for lod in out.values() for name,c in lod['clips'].items()
           if any(word in name.lower() for word in ('dead','standing','walking')))
sys.stdout.flush();sys.stderr.flush();os._exit(0)
