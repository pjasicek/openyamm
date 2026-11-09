"""Keep the upper lip rigid with the skull after the closed-mouth split; UVs and geometry are unchanged."""
from pathlib import Path
import json
import bpy
import numpy as np

P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/uv_master.blend'))
mesh = bpy.data.objects['Couatl']
data = json.loads((P/'work/rig.json').read_text())
labels = mesh.data.attributes['anatomy_part'].data
head = mesh.vertex_groups['Head']
jaw = mesh.vertex_groups['Jaw']
changed = []
for vertex in mesh.data.vertices:
    original = np.array(vertex.co)/data['source_scale'] + data['source_offset']
    if labels[vertex.index].value == 0 and original[1] < -.385 and original[2] > .025:
        if any(g.group == jaw.index and g.weight > 1e-5 for g in vertex.groups):
            changed.append(vertex.index)
        for group in mesh.vertex_groups:
            group.remove([vertex.index])
        head.add([vertex.index],1.,'REPLACE')
assert changed
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/uv_master_v2.blend'))
(P/'review/lip_weight_repair.json').write_text(json.dumps({'upper_lip_vertices_corrected':len(changed),
    'geometry_and_uvs':'unchanged','reason':'bisected upper-lip vertices retained soft Jaw influence'},indent=2)+'\n')
print('REPAIRED',len(changed))
