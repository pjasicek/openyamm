from pathlib import Path
import sys,json
import bpy,numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from common import render
bpy.ops.wm.open_mainfile(filepath=str(P/'work/body_import.blend'))
m=bpy.data.objects['Wyvern'];co=np.array([tuple(v.co) for v in m.data.vertices]);parent=list(range(len(co)))
def find(x):
    while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
    return x
for e in m.data.edges:
    a,b=(find(i) for i in e.vertices);parent[b]=a
parts={}
for i in range(len(co)):parts.setdefault(find(i),[]).append(i)
parts=sorted(parts.values(),key=len,reverse=True)
m.hide_render=True
for k,ids in enumerate(parts[:5]):
    sel=set(ids);data=bpy.data.meshes.new('part');data.from_pydata(co.tolist(),[],[list(f.vertices) for f in m.data.polygons if f.vertices[0] in sel]);o=bpy.data.objects.new('part',data);bpy.context.collection.objects.link(o)
    for f in data.polygons:f.use_smooth=True
    render(f'part_{k}','quarter',1.3,(0,-.05,0))
    bpy.data.objects.remove(o,do_unlink=True)
