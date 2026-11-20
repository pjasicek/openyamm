"""Pose/loop/visibility gates and master-to-portable parity for the effect rig."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1];FPS=48
info=json.loads((P/'export/export_info.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(P/'export/m528_master.blend'));sc=bpy.context.scene;sc.render.fps=FPS
rig=bpy.data.objects['WispRig'];names=['WispRing','WispSparks']
def activate(rig,a,t):
    rig.animation_data.action=a
    if len(a.slots):rig.animation_data.action_slot=a.slots[0]
    f=t*FPS;sc.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
def vertices(ob):
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    co=[tuple(ob.matrix_world@v.co) for v in me.vertices];ev.to_mesh_clear();return co
source={};report={};times={}
for n,duration in info['clips'].items():
    a=bpy.data.actions[n];ts=sorted(set([duration*i/8 for i in range(9)]+([.73,.75,.77] if n=='Attack' else [])))
    times[n]=ts
    for t in ts:
        activate(rig,a,t)
        for name in names:source[n,t,name]=vertices(bpy.data.objects[name])
    worststep=0;previous=None
    for i in range(round(duration*FPS*2)+1):
        activate(rig,a,i/(FPS*2))
        current={b.name:b.matrix.to_quaternion() for b in rig.pose.bones}
        assert all(math.isfinite(c) for b in rig.pose.bones for row in b.matrix for c in row)
        if previous:
            worststep=max(worststep,max(2*math.acos(min(1,abs(q.dot(previous[k])))) for k,q in current.items()))
        previous=current
    assert worststep<math.radians(65),(n,'rotation jump',math.degrees(worststep))
    report[n]={'max_rotation_step_degrees_96hz':math.degrees(worststep),'samples':len(ts)}
    if n in ('Standing','Walking'):
        for name in names:
            error=max((Vector(a)-Vector(b)).length for a,b in zip(source[n,0,name],source[n,duration,name]))
            # Hidden smoke leaves can move, but their collapsed surface is below 0.1 mm.
            assert error<.00015,(n,name,'loop seam',error)
        report[n]['loop_surface_error_m']=error
    if n=='Dead':
        assert all(max(b.scale)<.001 for b in rig.pose.bones if b.name!='Root')
        report[n]['all_effect_components_collapsed']=True

bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.render.fps=FPS
bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_m528.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
meshes={name:next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(name)) for name in names}
for n,ts in times.items():
    a=next(a for a in bpy.data.actions if a.name==n or a.name.startswith(n+'_'));errors=[]
    for t in ts:
        activate(rig,a,t)
        for name in names:
            before=source[n,t,name];after=vertices(meshes[name]);tree=kdtree.KDTree(len(before))
            for i,c in enumerate(before):tree.insert(Vector(c),i)
            tree.balance();errors.append(max(tree.find(Vector(c))[2] for c in after))
    report[n]['max_export_error_mm']=max(errors)*1000
    assert max(errors)<.0002,(n,'export drift',max(errors))
(P/'work/motion_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('MOTION AND EXPORT',report)
