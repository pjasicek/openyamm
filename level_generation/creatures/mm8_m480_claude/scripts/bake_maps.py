"""Bake short-range rest-pose AO separately into each selected UV set."""
from pathlib import Path
import bpy,bmesh,sys,runpy
p=Path(__file__).resolve().parents[1]
for layer in ('UVMap','HeadUV'):
    bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured.blend'))
    rig=bpy.data.objects['Rig'];rig.animation_data.action=None
    for bone in rig.pose.bones:bone.matrix_basis.identity()
    body=bpy.data.objects['Body'];club=bpy.data.objects['Club'];club.hide_render=True
    ob=body.copy();ob.data=body.data.copy();bpy.context.scene.collection.objects.link(ob);ob.name='AOBake'
    ob.modifiers.clear();ob.parent=None
    bm=bmesh.new();bm.from_mesh(ob.data);hl=bm.faces.layers.int['head'];want=layer=='HeadUV'
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if bool(f[hl])!=want],context='FACES');bm.to_mesh(ob.data);bm.free()
    ob.data.uv_layers.active=ob.data.uv_layers[layer]
    sys.argv=['bake_creature_ao.py','--',ob.name,str(p/f'work/ao_{layer}.png'),'.035','1024']
    runpy.run_path(str(p.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
