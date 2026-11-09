"""Reopen the actual GLB in the same studio and inspect imported materials, action timings and deformation."""
import bpy
import json
import hashlib
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from render_export_review import build as render_review
from verify_mesh_motion import build as verify_motion

def build():
    assert Path(bpy.data.filepath)==ROOT/'mm6_goblin.blend','Run from the isolated delivered Blender project'
    scene=bpy.context.scene;scene.name='MM6 Goblin imported GLB review'
    original=[o for o in scene.objects if o.type in {'MESH','ARMATURE'}]
    assert len(original)==2
    for obj in original:bpy.data.objects.remove(obj,do_unlink=True)
    for action in list(bpy.data.actions):bpy.data.actions.remove(action,do_unlink=True)
    bpy.ops.import_scene.gltf(filepath=str(ROOT/'mm6_goblin.glb'),disable_bone_shape=True)
    rigs=[o for o in scene.objects if o.type=='ARMATURE'];assert len(rigs)==1
    rig=rigs[0];rig.animation_data.use_nla=False
    manifest=json.loads((ROOT/'animations/manifest.json').read_text());manifest['scene']=scene.name
    report={'consumer':'Blender glTF importer 5.2.1; actual delivered GLB',
        'glb_sha256':hashlib.sha256((ROOT/'mm6_goblin.glb').read_bytes()).hexdigest(),'clips':{}}
    assert {a.name for a in bpy.data.actions}==set(manifest['clips'])
    for name,clip in manifest['clips'].items():
        action=bpy.data.actions[name];start,end=action.frame_range
        duration=(end-start)/scene.render.fps
        assert abs(duration-clip['duration_seconds'])<1e-5,(name,duration,clip['duration_seconds'])
        clip['frame_start']=float(start);clip['frame_end']=float(end);clip['action']=name
        report['clips'][name]={'frame_start':float(start),'frame_end':float(end),'duration_seconds':duration}
    (ROOT/'export_work/imported_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (ROOT/'export_work/import_report.json').write_text(json.dumps(report,indent=2)+'\n')
    verify_motion(scene.name,ROOT/'export_work/imported_motion_report.json',manifest_override=manifest)
    render_review(scene.name,'glb',manifest_override=manifest)
    rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];scene.frame_set(int(manifest['clips']['Standing']['frame_start']))
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'review/imported_glb.blend'))
    print('Actual GLB import timing, geometry checks and matched studio views complete')

if __name__=='__main__':build()
