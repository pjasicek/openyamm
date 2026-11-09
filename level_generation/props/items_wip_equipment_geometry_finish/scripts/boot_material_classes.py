"""Use the coordinator's reviewed face-class path for leather lining and actual brass buckle solids."""
import hashlib,json,sys
from pathlib import Path
import bpy
P=Path(__file__).resolve().parents[1]
scene=P/'work/codex_tex/equipment_6boots1.blend'
bpy.ops.wm.open_mainfile(filepath=str(scene));obj=bpy.data.objects['equipment_6boots1'];mesh=obj.data
neighbours=[set() for _ in mesh.vertices]
for edge in mesh.edges:
    a,b=edge.vertices;neighbours[a].add(b);neighbours[b].add(a)
seen=set();classes=[1]*len(mesh.polygons);components=[]
for vertex in mesh.vertices:
    if vertex.index in seen:continue
    todo=[vertex.index];seen.add(vertex.index);indices=[]
    while todo:
        i=todo.pop();indices.append(i)
        for j in neighbours[i]:
            if j not in seen:seen.add(j);todo.append(j)
    vertices=[mesh.vertices[i].co for i in indices];low=min(v.z for v in vertices);high=max(v.z for v in vertices)
    metal=len(indices)<100 and low>.30 and high<.45
    if metal:
        members=set(indices)
        for face in mesh.polygons:
            if face.vertices[0] in members:classes[face.index]=0
    components.append({'vertices':len(indices),'min_z':low,'max_z':high,'material':'metal' if metal else 'leather'})
assert 30<classes.count(0)<500,(classes.count(0),components)
folder=P/'codex_tex/equipment_6boots1'
receipt={'source_scene_sha256':hashlib.sha256(scene.read_bytes()).hexdigest(),'face_classes':classes,'components':components,'review':'Actual small closed buckle bars are brass. Feet, shafts, deep lining and leather bands are leather. No gemstone exists; shaded green generated masks incorrectly labelled the lining black/gem.'}
(folder/'reviewed_material_classes.json').write_text(json.dumps(receipt,indent=2)+'\n')
frame=json.loads((folder/'views.json').read_text());frame['material_classes_file']='reviewed_material_classes.json';(folder/'views.json').write_text(json.dumps(frame,indent=2)+'\n')
print('AUTHORED_BOOT_CLASSES',classes.count(0),'brass faces;',classes.count(1),'leather faces',flush=True)
