"""Pack the textured LOD0 master while retaining its source-component and glow-zone face attributes."""
import json
import os
from pathlib import Path
import sys
import traceback

import bpy

P=Path(__file__).resolve().parents[1]


def main():
    bpy.ops.wm.open_mainfile(filepath=str(P/'work/ion_cannon_uv.blend'))
    original=list(bpy.data.objects)
    for obj in original:
        if obj.type=='MESH':obj.data.materials.clear()
    for material in list(bpy.data.materials):bpy.data.materials.remove(material)
    bpy.ops.import_scene.gltf(filepath=str(P/'work/ion_cannon_ready.glb'))
    materials={m.name:m for m in bpy.data.materials}
    for obj in original:
        if obj.type!='MESH':continue
        assert obj.name in materials,obj.name
        obj.data.materials.append(materials[obj.name])
        for face in obj.data.polygons:face.material_index=0
    for obj in list(bpy.data.objects):
        if obj in original:continue
        if obj.name=='GC_Arcs':
            obj['visible_state']='c5';obj.hide_render=True;obj.hide_viewport=True
        else:bpy.data.objects.remove(obj,do_unlink=True)
    data=(P/'work/ion_cannon_ready.glb').read_bytes()
    length=int.from_bytes(data[12:16],'little')
    doc=json.loads(data[20:20+length])
    for source in doc['materials']:
        if source['name'] in materials:
            for key,value in source.get('extras',{}).items():materials[source['name']][key]=value
    assert sum(len(f.vertices)-2 for o in original if o.type=='MESH' for f in o.data.polygons)==7916
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/ion_cannon_textured.blend'))
    print('Packed editable LOD0 master; c5 arcs hidden by default. Runtime LODs remain in ion_cannon_ready.glb.',flush=True)


try:main()
except Exception:
    traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
