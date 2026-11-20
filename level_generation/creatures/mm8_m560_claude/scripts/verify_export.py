"""Verify the delivered surface and motion after reimport, and keep portable authoring maps."""
from pathlib import Path
import json,sys,bpy
import numpy as np
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from common import coordinates
bpy.ops.wm.open_mainfile(filepath=str(P/'wyvern.blend'))
rig=bpy.data.objects['Wyvern_Rig'];mesh=bpy.data.objects['Wyvern'];sc=bpy.context.scene
expected={}
for name in ['Fly','Attack','Hit','Death','Dead']:
    a=bpy.data.actions[name];rig.animation_data.action=a;end=float(a.frame_range[1]);poses=[]
    for f in [1,(1+end)*.5,end]:
        sc.frame_set(int(f),subframe=f%1);poses.append(coordinates(mesh))
    expected[name]=poses
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_m560.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');mesh=bpy.data.objects['Wyvern'];sc=bpy.context.scene
print('IMPORTED ACTIONS',[a.name for a in bpy.data.actions],flush=True)
report={}
for name,poses in expected.items():
    a=next(a for a in bpy.data.actions if name==a.name or a.name.endswith('_'+name) or a.name.startswith(name+'_'))
    rig.animation_data.action=a;end=float(a.frame_range[1]);error=0
    for f,ref in zip([float(a.frame_range[0]),(float(a.frame_range[0])+end)*.5,end],poses):
        sc.frame_set(int(f),subframe=f%1);co=coordinates(mesh);tree=KDTree(len(ref))
        for i,v in enumerate(ref):tree.insert(v,i)
        tree.balance();error=max(error,max(tree.find(v)[2] for v in co))
    assert error<.0001,(name,error)
    report[name]={'max_surface_error':error,'duration':(end-float(a.frame_range[0]))/sc.render.fps}
(P/'review/export_parity.json').write_text(json.dumps(report,indent=2)+'\n')
print('PARITY',report,flush=True)
# The editable master gets the exact runtime normal and ORM maps; geometry and animation remain the master.
normal=next(i for i in bpy.data.images if i.name.startswith('wyvern_normal'))
normal.filepath_raw=str(P/'textures/wyvern_normal_runtime.png');normal.file_format='PNG';normal.save()
bpy.ops.wm.open_mainfile(filepath=str(P/'wyvern.blend'))
mat=bpy.data.objects['Wyvern'].data.materials[0]
for n in mat.node_tree.nodes:
    if n.type=='TEX_IMAGE' and n.image:
        if n.image.name.startswith('wyvern_normal'):n.image=bpy.data.images.load(str(P/'textures/wyvern_normal_runtime.png'),check_existing=True);n.image.colorspace_settings.name='Non-Color'
        if n.image.name.startswith('wyvern_orm'):n.image=bpy.data.images.load(str(P/'textures/runtime/mm8_m560_2_mr.png'),check_existing=True);n.image.colorspace_settings.name='Non-Color'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'wyvern.blend'))
