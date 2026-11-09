"""Bake both independently packed UV sets with the whole creature present as an occluder."""
import bpy, bmesh, runpy, sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_uv.blend'))
source=bpy.data.objects['Body']
parts=[]
for slot,label in enumerate(('body','head')):
    part=source.copy();part.data=source.data.copy();part.name='Bake_'+label
    bpy.context.scene.collection.objects.link(part)
    bm=bmesh.new();bm.from_mesh(part.data)
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=slot],context='FACES')
    bm.to_mesh(part.data);bm.free()
    if part.data.uv_layers.get('BodyFull'):part.data.uv_layers.remove(part.data.uv_layers['BodyFull'])
    part.data.uv_layers.active=part.data.uv_layers['UVMap'];part.data.uv_layers.active.active_render=True
    for face in part.data.polygons:face.material_index=0
    assert len(part.data.polygons)>1000
    parts.append((part,label))
bpy.data.objects.remove(source,do_unlink=True)
for part,label in parts:
    sys.argv=['bake_creature_ao.py','--',part.name,str(P/'textures'/f'm524_{label}_ao.png'),'0.04','1024']
    runpy.run_path(str(P.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
