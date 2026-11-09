"""Body cleanup on work/step0.blend: remove the dorsal spikes Smart Topology invented along the abdomen's back (separate
pieces on the midline below the waist; none in the HD references or native frames). Writes work/step1.blend."""
import bpy, bmesh, json
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'step0.blend'))
ob = bpy.data.objects['Queen']
data = json.loads((P / 'work' / 'pieces.json').read_text())
labels = np.array(data['labels'])
spikes = [r['piece'] for r in data['pieces']
          if abs(r['centre'][0]) < 0.02 and r['centre'][2] < 1.3 and r['verts'] < 200]
bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
doomed = [bm.verts[i] for i in np.where(np.isin(labels, spikes))[0]]
bmesh.ops.delete(bm, geom=doomed, context='VERTS')
bm.to_mesh(ob.data); bm.free(); ob.data.update()
print('CLEANUP removed dorsal spike pieces', spikes, 'vertices', len(doomed), 'left', len(ob.data.vertices))
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work' / 'step1.blend'))
