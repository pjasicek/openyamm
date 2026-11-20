"""Compare posed master surfaces with the actual GLB, including fractional release and death samples."""
import bpy,json
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'export/m628_master.blend'));sc=bpy.context.scene;sc.render.fps=30
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
times={a.name:sorted(set([float(a.frame_range[1])/30*i/8 for i in range(9)]+([.6,.7,.85,.9,.914,.9167,.9208]if a.name=='Attack'else[])))for a in bpy.data.actions}
def coords(rig,body,a,t):
    rig.animation_data.action=a
    if len(a.slots):rig.animation_data.action_slot=a.slots[0]
    f=t*30;sc.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    co=[tuple(body.matrix_world@v.co)for v in me.vertices];ev.to_mesh_clear();return co
source={(n,t):coords(rig,body,bpy.data.actions[n],t)for n,ts in times.items()for t in ts}
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_m628.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=bpy.data.objects['SkeletonArcher'];report={}
for name,ts in times.items():
    a=next(a for a in bpy.data.actions if a.name==name or a.name.startswith(name+'_'));errors=[]
    for t in ts:
        before=source[name,t];after=coords(rig,body,a,t);tree=kdtree.KDTree(len(before))
        for i,c in enumerate(before):tree.insert(Vector(c),i)
        tree.balance();errors.append(max(tree.find(Vector(c))[2]for c in after))
    report[name]={'samples':len(ts),'max_surface_error_mm':max(errors)*1000}
    assert max(errors)<.0002,(name,max(errors))
(P/'work/export_parity.json').write_text(json.dumps(report,indent=2));print('EXPORT PARITY',report)
