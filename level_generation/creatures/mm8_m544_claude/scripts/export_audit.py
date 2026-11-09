"""Reimport the delivered GLB and compare its animated surface with the editable master."""
from pathlib import Path
import json
import bpy
import numpy as np
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'unicorn_master.blend'))
sc=bpy.context.scene;sc.render.fps=48
rig=bpy.data.objects['Unicorn_Rig'];mesh=bpy.data.objects['Unicorn']
times={a.name:np.linspace(0,(float(a.frame_range[1])-float(a.frame_range[0]))/48,9).tolist()
       for a in bpy.data.actions}
def coords(rig,mesh,action,t,offset):
    rig.animation_data.action=action
    if len(action.slots):rig.animation_data.action_slot=action.slots[0]
    f=t*48+offset;sc.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
    ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());data=ev.to_mesh()
    result=np.array([tuple(mesh.matrix_world@v.co) for v in data.vertices]);ev.to_mesh_clear()
    assert np.isfinite(result).all()
    return result
source={(name,t):coords(rig,mesh,bpy.data.actions[name],t,1) for name,ts in times.items() for t in ts}
standing=source['Standing',0.0]
height=float(np.ptp(standing[:,2]));assert .5<height<.8
assert np.max(abs(source['Dead',0.0]-source['Death',.75]))<1e-6
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.render.fps=48
bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_m544.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');mesh=bpy.data.objects['Unicorn']
assert 'HornTip' in rig.pose.bones and 'Breath' in rig.pose.bones
report={}
for name,ts in times.items():
    act=next(a for a in bpy.data.actions if a.name==name or a.name.startswith(name+'_'))
    errors=[]
    for t in ts:
        before=source[name,t];after=coords(rig,mesh,act,t,0)
        tree=kdtree.KDTree(len(before))
        for i,c in enumerate(before):tree.insert(Vector(c),i)
        tree.balance();errors.append(max(tree.find(Vector(c))[2] for c in after))
    report[name]={'samples':len(ts),'max_surface_error_mm':max(errors)*1000}
    assert max(errors)<.0002,(name,max(errors))
(P/'work/export_parity.json').write_text(json.dumps({'clips':report,'standing_height_m':height},indent=2)+'\n')
print('PARITY',report,'height',height,flush=True)
